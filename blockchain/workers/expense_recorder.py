"""
Asynchronous Blockchain Worker for Campaign Expense & Vendor Invoice Logging
Anchors commercial vendor invoices and outflow payouts on Polygon Amoy.
"""

import asyncio
import logging
from uuid import UUID
from typing import Optional, Union

from database.connection import SessionLocal
from database.models import Milestone, Campaign
from blockchain.services.blockchain_service import blockchain_service, calculate_file_sha256
from razorpay.services.redis_service import redis_service

logger = logging.getLogger("expense_recorder")

MAX_RETRIES = 3
INITIAL_DELAY_SECONDS = 1.0
BACKOFF_FACTOR = 2.0


async def record_expense_on_chain(
    campaign_id: UUID,
    milestone_index: int,
    amount: float,
    vendor_gst: str,
    invoice_bytes_or_hash: Union[bytes, str],
    campaign_title: str = "Campaign",
    db_session=None,
    max_retries: int = MAX_RETRIES
) -> Optional[str]:
    """
    Background worker to anchor a commercial expense invoice on Polygon Amoy.
    """
    logger.info(f"[Expense Job] Starting on-chain recording for Campaign={campaign_id}, Milestone={milestone_index}, Amount=₹{amount}")

    # Compute SHA-256 if raw invoice bytes provided
    if isinstance(invoice_bytes_or_hash, bytes):
        invoice_hash = calculate_file_sha256(invoice_bytes_or_hash)
    else:
        invoice_hash = str(invoice_bytes_or_hash)

    tx_hash = None
    delay = INITIAL_DELAY_SECONDS

    # 1. Attempt on-chain submission with exponential backoff
    for attempt in range(1, max_retries + 1):
        try:
            tx_hash = blockchain_service.record_expense(
                campaign_id=campaign_id,
                milestone_index=milestone_index,
                amount_inr=amount,
                vendor_gst=vendor_gst,
                invoice_hash=invoice_hash
            )
            if tx_hash:
                break
        except Exception as exc:
            logger.warning(
                f"[Expense Job] Attempt {attempt}/{max_retries} failed for Campaign {campaign_id}: {exc}"
            )
            if attempt < max_retries:
                await asyncio.sleep(delay)
                delay *= BACKOFF_FACTOR

    if not tx_hash:
        logger.error(f"[Expense Job] Failed to record expense for Campaign {campaign_id} after {max_retries} retries.")
        return None

    explorer_url = blockchain_service.get_explorer_url(tx_hash)
    logger.info(f"[Expense Job] TX generated for Campaign {campaign_id} Expense: {tx_hash}")

    # 2. Broadcast to Explorer feed
    try:
        await redis_service.broadcast_explorer(
            event_type="expense_recorded",
            data={
                "type": "expense_proof",
                "campaign_id": str(campaign_id),
                "campaign_title": campaign_title,
                "milestone_index": milestone_index,
                "amount": amount,
                "vendor_gst": vendor_gst,
                "invoice_hash": invoice_hash,
                "tx_hash": tx_hash,
                "explorer_url": explorer_url
            }
        )
    except Exception as e:
        logger.warning(f"[Expense Job] Failed to broadcast explorer event: {e}")

    return tx_hash

