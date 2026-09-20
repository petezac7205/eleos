"""
Asynchronous Blockchain Worker for Donation Recording
Submits completed donations to Polygon Amoy, updates database records, and emits WebSocket updates.
Includes resilient retry logic with exponential backoff for transient RPC and network failures.
"""

import asyncio
import logging
from uuid import UUID
from typing import Optional

from database.connection import SessionLocal
from database.models import Donation
from blockchain.services.blockchain_service import blockchain_service
from razorpay.services.redis_service import redis_service

logger = logging.getLogger("donation_recorder")

MAX_RETRIES = 3
INITIAL_DELAY_SECONDS = 1.0
BACKOFF_FACTOR = 2.0


async def record_donation_on_chain(
    donation_id: UUID,
    campaign_id: UUID,
    amount: float,
    gateway_receipt_hash: Optional[str] = None,
    donor_id: Optional[str] = None,
    campaign_title: str = "Campaign",
    db_session=None,
    max_retries: int = MAX_RETRIES
) -> Optional[str]:
    """
    Background worker function called after a payment is verified/captured:
    1. Calls EleosRegistry smart contract on Polygon Amoy (or simulation) with retry logic.
    2. Updates PostgreSQL record: blockchain_tx_hash and blockchain_confirmed = True.
    3. Emits WebSocket 'blockchain_confirmed' to donor and public live explorer feed.
    """
    logger.info(f"[Blockchain Job] Starting on-chain recording for Donation={donation_id}, Campaign={campaign_id}, Amount=₹{amount}")

    tx_hash = None
    delay = INITIAL_DELAY_SECONDS

    # 1. Attempt on-chain transaction submission with exponential backoff retry
    for attempt in range(1, max_retries + 1):
        try:
            tx_hash = blockchain_service.record_donation(
                donation_id=donation_id,
                campaign_id=campaign_id,
                amount_inr=amount,
                gateway_receipt_hash=gateway_receipt_hash
            )
            if tx_hash:
                break
        except Exception as exc:
            logger.warning(
                f"[Blockchain Job] Attempt {attempt}/{max_retries} failed for Donation {donation_id}: {exc}"
            )
            if attempt < max_retries:
                await asyncio.sleep(delay)
                delay *= BACKOFF_FACTOR
            else:
                logger.error(
                    f"[Blockchain Job] All {max_retries} attempts exhausted for Donation {donation_id}. On-chain record failed.",
                    exc_info=True
                )

    if not tx_hash:
        logger.error(f"[Blockchain Job] Failed to record Donation {donation_id} on-chain after {max_retries} retries.")
        return None

    explorer_url = blockchain_service.get_explorer_url(tx_hash)
    logger.info(f"[Blockchain Job] TX generated for Donation {donation_id}: {tx_hash}")

    # 2. Update database record
    session_created_here = False
    db = db_session
    if db is None:
        db = SessionLocal()
        session_created_here = True

    try:
        donation = db.query(Donation).filter(Donation.id == donation_id).first()
        if donation:
            donation.blockchain_tx_hash = tx_hash
            donation.blockchain_confirmed = True
            db.commit()
            db.refresh(donation)
            logger.info(f"[Blockchain Job] Donation {donation_id} marked blockchain_confirmed in DB.")
        else:
            logger.warning(f"[Blockchain Job] Donation {donation_id} not found in DB during on-chain update.")
    except Exception as db_err:
        logger.error(f"[Blockchain Job] Failed to update DB for Donation {donation_id}: {db_err}")
    finally:
        if session_created_here:
            db.close()

    # 3. Publish WebSocket confirmation event to donor channel
    if donor_id:
        try:
            await redis_service.notify_donor(
                user_id=donor_id,
                event_type="blockchain_confirmed",
                data={
                    "donation_id": str(donation_id),
                    "amount": amount,
                    "tx_hash": tx_hash,
                    "explorer_url": explorer_url
                }
            )
        except Exception as e:
            logger.warning(f"[Blockchain Job] Failed to notify donor via WebSocket: {e}")

    # 4. Broadcast live proof event to the public Transparency Explorer feed
    try:
        await redis_service.broadcast_explorer(
            event_type="blockchain_confirmed",
            data={
                "type": "donation_proof",
                "donation_id": str(donation_id),
                "campaign_title": campaign_title,
                "amount": amount,
                "currency": "INR",
                "tx_hash": tx_hash,
                "explorer_url": explorer_url
            }
        )
    except Exception as e:
        logger.warning(f"[Blockchain Job] Failed to broadcast explorer event: {e}")

    return tx_hash

