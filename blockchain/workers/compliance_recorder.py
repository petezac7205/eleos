"""
Asynchronous Blockchain Worker for NGO Compliance Document Anchoring
Anchors 12A, 80G, FCRA, and CA-audited balance sheet checksums on Polygon Amoy.
"""

import asyncio
import logging
from uuid import UUID
from typing import Optional, Union

from database.connection import SessionLocal
from database.models import Document, NGOProfile
from blockchain.services.blockchain_service import blockchain_service, calculate_file_sha256
from razorpay.services.redis_service import redis_service

logger = logging.getLogger("compliance_recorder")

MAX_RETRIES = 3
INITIAL_DELAY_SECONDS = 1.0
BACKOFF_FACTOR = 2.0


async def anchor_document_on_chain(
    ngo_id: UUID,
    doc_id: UUID,
    doc_type: str,
    file_bytes_or_hash: Union[bytes, str],
    db_session=None,
    max_retries: int = MAX_RETRIES
) -> Optional[str]:
    """
    Background worker to anchor a compliance document hash on Polygon Amoy.
    """
    logger.info(f"[Compliance Job] Starting on-chain anchoring for NGO={ngo_id}, Doc={doc_id}, Type={doc_type}")

    # Compute SHA-256 if raw bytes provided
    if isinstance(file_bytes_or_hash, bytes):
        file_hash = calculate_file_sha256(file_bytes_or_hash)
    else:
        file_hash = str(file_bytes_or_hash)

    tx_hash = None
    delay = INITIAL_DELAY_SECONDS

    # 1. Attempt on-chain submission with exponential backoff
    for attempt in range(1, max_retries + 1):
        try:
            tx_hash = blockchain_service.anchor_document(
                ngo_id=ngo_id,
                doc_type=doc_type,
                file_hash=file_hash
            )
            if tx_hash:
                break
        except Exception as exc:
            logger.warning(
                f"[Compliance Job] Attempt {attempt}/{max_retries} failed for Doc {doc_id}: {exc}"
            )
            if attempt < max_retries:
                await asyncio.sleep(delay)
                delay *= BACKOFF_FACTOR

    if not tx_hash:
        logger.error(f"[Compliance Job] Failed to anchor Doc {doc_id} on-chain after {max_retries} retries.")
        return None

    explorer_url = blockchain_service.get_explorer_url(tx_hash)
    logger.info(f"[Compliance Job] TX generated for Doc {doc_id}: {tx_hash}")

    # 2. Update database record
    session_created_here = False
    db = db_session
    if db is None:
        db = SessionLocal()
        session_created_here = True

    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.file_hash = file_hash
            db.commit()
            logger.info(f"[Compliance Job] Document {doc_id} file_hash updated in DB.")
    except Exception as db_err:
        logger.error(f"[Compliance Job] Failed to update DB for Doc {doc_id}: {db_err}")
    finally:
        if session_created_here:
            db.close()

    # 3. Broadcast to Explorer feed
    try:
        await redis_service.broadcast_explorer(
            event_type="compliance_anchored",
            data={
                "type": "document_proof",
                "ngo_id": str(ngo_id),
                "doc_id": str(doc_id),
                "doc_type": doc_type,
                "file_hash": file_hash,
                "tx_hash": tx_hash,
                "explorer_url": explorer_url
            }
        )
    except Exception as e:
        logger.warning(f"[Compliance Job] Failed to broadcast explorer event: {e}")

    return tx_hash

