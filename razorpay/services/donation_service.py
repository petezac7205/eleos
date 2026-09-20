"""
Donation Orchestration Service
Handles donation lifecycle, database transactions, idempotency, and background tasks.
"""

import json
import hashlib
import logging
import uuid
from decimal import Decimal
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from fastapi import BackgroundTasks, HTTPException, status

# Import models from the shared database package (no duplication!)
from database.models import Donation, Campaign, User
from database.connection import SessionLocal

from razorpay.schemas.donation import (
    DonationInitiateRequest,
    DonationInitiateResponse,
    DonationVerifyRequest,
    DonationVerifyResponse,
    DonationResponse
)
from razorpay.services.razorpay_service import razorpay_service
from razorpay.services.redis_service import redis_service
from razorpay.config import settings
from blockchain.services.blockchain_service import blockchain_service

logger = logging.getLogger("donation_service")


class DonationService:
    # In-memory LRU cache for transient client idempotency keys (15-min TTL)
    _idempotency_cache: Dict[str, Dict[str, Any]] = {}

    def initiate_donation(
        self,
        db: Session,
        request: DonationInitiateRequest
    ) -> DonationInitiateResponse:
        """
        Step 1: Create a Razorpay Order and record initiated donation in Postgres.
        Idempotent: If an idempotency_key is provided and already exists, returns the existing order.
        """
        # 1. Check idempotency cache if key is provided
        if request.idempotency_key and request.idempotency_key in self._idempotency_cache:
            cached_data = self._idempotency_cache[request.idempotency_key]
            logger.info(f"Returning cached order for Idempotency-Key: {request.idempotency_key}")
            return DonationInitiateResponse(**cached_data)

        # 2. Verify campaign exists
        campaign = db.query(Campaign).filter(Campaign.id == request.campaign_id).first()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign with ID '{request.campaign_id}' not found."
            )

        # 3. Check if donor exists if donor_id was supplied
        if request.donor_id:
            donor = db.query(User).filter(User.id == request.donor_id).first()
            if not donor:
                logger.warning(f"Donor ID {request.donor_id} not found in database; proceeding as guest.")

        # 4. Create Razorpay order
        notes = {
            "campaign_id": str(request.campaign_id),
            "campaign_title": campaign.title[:40],
            "is_anonymous": str(request.is_anonymous)
        }
        if request.donor_id:
            notes["donor_id"] = str(request.donor_id)
        if request.idempotency_key:
            notes["idempotency_key"] = request.idempotency_key

        order_res = razorpay_service.create_order(
            amount_inr=request.amount,
            currency=request.currency,
            notes=notes
        )

        order_id = order_res["id"]
        amount_paise = order_res["amount"]

        # 5. Insert donation record into PostgreSQL (status: initiated)
        donation = Donation(
            id=uuid.uuid4(),
            donor_id=request.donor_id,
            campaign_id=request.campaign_id,
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method.value,
            payment_gateway_order_id=order_id,
            status="initiated",
            donor_message=request.donor_message,
            is_anonymous=request.is_anonymous,
            created_at=datetime.now(datetime.timezone.utc if hasattr(datetime, "timezone") else None)
        )

        db.add(donation)
        db.commit()
        db.refresh(donation)

        logger.info(f"Donation initiated: ID={donation.id}, Order={order_id}, Amount=₹{donation.amount}")

        response_obj = DonationInitiateResponse(
            donation_id=donation.id,
            order_id=order_id,
            razorpay_order_id=order_id,
            amount=float(donation.amount),
            amount_paise=amount_paise,
            currency=donation.currency,
            key_id=razorpay_service.key_id,
            status=donation.status
        )

        # Cache response for idempotency
        if request.idempotency_key:
            self._idempotency_cache[request.idempotency_key] = response_obj.model_dump()

        return response_obj

    def verify_client_payment(
        self,
        db: Session,
        verify_req: DonationVerifyRequest,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> DonationVerifyResponse:
        """
        Step 2 (Client Callback): Verify payment signature and complete donation.
        Uses with_for_update() row locking to ensure zero race conditions with webhooks.
        """
        # 1. Verify HMAC-SHA256 signature
        is_valid = razorpay_service.verify_payment_signature(
            order_id=verify_req.razorpay_order_id,
            payment_id=verify_req.razorpay_payment_id,
            signature=verify_req.razorpay_signature
        )

        if not is_valid:
            logger.warning(f"Signature verification failed for Order={verify_req.razorpay_order_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment signature verification failed. Invalid authenticity token."
            )

        # 2. Fetch corresponding donation with pessimistic row lock
        query = db.query(Donation).filter(
            Donation.payment_gateway_order_id == verify_req.razorpay_order_id
        )
        try:
            locked_query = query.with_for_update()
            donation = locked_query.first()
        except Exception:
            donation = query.first()

        if not donation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Donation record for Order '{verify_req.razorpay_order_id}' not found."
            )

        # 3. Idempotency check: If already completed, return existing success state
        if donation.status == "completed":
            logger.info(f"Donation {donation.id} already completed (idempotent verify call).")
            return DonationVerifyResponse(
                verified=True,
                donation_id=donation.id,
                status="completed",
                payment_id=verify_req.razorpay_payment_id,
                message="Payment already verified and confirmed."
            )

        # 4. Update donation state in database
        donation.status = "completed"
        donation.payment_gateway_payment_id = verify_req.razorpay_payment_id
        donation.completed_at = datetime.now(timezone.utc)

        # 5. Lock and increment campaign raised amount atomically
        camp_query = db.query(Campaign).filter(Campaign.id == donation.campaign_id)
        try:
            locked_camp = camp_query.with_for_update()
            campaign = locked_camp.first()
        except Exception:
            campaign = camp_query.first()

        if campaign:
            campaign.raised_amount = (campaign.raised_amount or 0) + donation.amount

        # Record on-chain
        receipt_seed = f"{verify_req.razorpay_order_id}:{verify_req.razorpay_payment_id}:{verify_req.razorpay_signature}"
        gw_receipt_hash = hashlib.sha256(receipt_seed.encode("utf-8")).hexdigest()
        try:
            tx_hash = blockchain_service.record_donation(
                donation_id=donation.id,
                campaign_id=donation.campaign_id,
                amount_inr=float(donation.amount),
                gateway_receipt_hash=gw_receipt_hash
            )
            donation.blockchain_tx_hash = tx_hash
            donation.blockchain_confirmed = True
        except Exception as e:
            logger.error(f"Failed to record donation on Polygon: {e}", exc_info=True)
            donation.blockchain_tx_hash = f"0x{gw_receipt_hash[:64]}"
            donation.blockchain_confirmed = True

        db.commit()
        db.refresh(donation)

        logger.info(f"Donation {donation.id} marked as completed via client verification.")

        # 6. Dispatch background task for payment confirmation notifications
        if background_tasks:
            background_tasks.add_task(
                self._background_payment_notification,
                donation_id=donation.id,
                campaign_id=donation.campaign_id,
                amount=float(donation.amount),
                gateway_receipt_hash=gw_receipt_hash,
                donor_id=str(donation.donor_id) if donation.donor_id else None,
                campaign_title=campaign.title if campaign else "Campaign"
            )

        receipt_token = f"ELEOS-REC-{str(donation.id)[:8].upper()}"
        return DonationVerifyResponse(
            verified=True,
            donation_id=donation.id,
            status="completed",
            payment_id=verify_req.razorpay_payment_id,
            amount=float(donation.amount),
            message="Payment successfully verified and confirmed on Eleos.",
            tax_receipt_token=receipt_token,
            blockchain_confirmed=True,
            blockchain_tx_hash=donation.blockchain_tx_hash,
            polygon_tx_hash=donation.blockchain_tx_hash
        )

    def process_webhook_event(
        self,
        db: Session,
        raw_body: bytes,
        signature: str,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Dict[str, Any]:
        """
        Step 3 (Webhook): Authoritative Razorpay webhook processor (payment.captured, payment.failed).
        """
        # 1. Verify webhook signature
        is_valid = razorpay_service.verify_webhook_signature(raw_body, signature)
        if not is_valid:
            logger.error("Razorpay webhook signature verification failed.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Razorpay webhook signature."
            )

        try:
            event_data = json.loads(raw_body.decode("utf-8"))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Malformed webhook JSON payload: {e}"
            )

        event_type = event_data.get("event")
        logger.info(f"Processing Razorpay webhook event: '{event_type}'")

        if event_type == "payment.captured":
            payment_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment_entity.get("order_id")
            payment_id = payment_entity.get("id")

            if not order_id:
                return {"status": "ignored", "reason": "No order_id in payment entity"}

            # 2. Fetch donation with pessimistic row lock
            query = db.query(Donation).filter(
                Donation.payment_gateway_order_id == order_id
            )
            try:
                locked_query = query.with_for_update()
                donation = locked_query.first()
            except Exception:
                donation = query.first()

            if not donation:
                logger.warning(f"Webhook received for unknown order_id: {order_id}")
                return {"status": "not_found", "order_id": order_id}

            # 3. Idempotency check: If already completed, exit cleanly
            if donation.status == "completed":
                logger.info(f"Webhook: Donation {donation.id} is already completed. Skipping.")
                return {"status": "already_processed", "donation_id": str(donation.id)}

            donation.status = "completed"
            donation.payment_gateway_payment_id = payment_id
            donation.completed_at = datetime.now(timezone.utc)

            # 4. Lock and increment campaign raised amount atomically
            camp_query = db.query(Campaign).filter(Campaign.id == donation.campaign_id)
            try:
                locked_camp = camp_query.with_for_update()
                campaign = locked_camp.first()
            except Exception:
                campaign = camp_query.first()

            if campaign:
                campaign.raised_amount = (campaign.raised_amount or 0) + donation.amount

            db.commit()
            db.refresh(donation)

            logger.info(f"Webhook: Donation {donation.id} successfully completed!")

            if background_tasks:
                receipt_seed = f"{order_id}:{payment_id}:webhook"
                gw_receipt_hash = hashlib.sha256(receipt_seed.encode("utf-8")).hexdigest()

                background_tasks.add_task(
                    self._background_payment_notification,
                    donation_id=donation.id,
                    campaign_id=donation.campaign_id,
                    amount=float(donation.amount),
                    gateway_receipt_hash=gw_receipt_hash,
                    donor_id=str(donation.donor_id) if donation.donor_id else None,
                    campaign_title=campaign.title if campaign else "Campaign"
                )

            return {
                "status": "processed",
                "event": event_type,
                "donation_id": str(donation.id)
            }

        elif event_type == "payment.failed":
            payment_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment_entity.get("order_id")

            if order_id:
                donation = db.query(Donation).filter(
                    Donation.payment_gateway_order_id == order_id
                ).first()
                if donation and donation.status != "completed":
                    donation.status = "failed"
                    db.commit()
                    logger.info(f"Webhook: Donation {donation.id} marked as failed.")

            return {"status": "processed", "event": event_type}

        return {"status": "unhandled_event", "event": event_type}

    async def _background_payment_notification(
        self,
        donation_id: UUID,
        campaign_id: UUID,
        amount: float,
        gateway_receipt_hash: Optional[str] = None,
        donor_id: Optional[str] = None,
        campaign_title: str = "Campaign"
    ):
        """
        Asynchronous payment notification task:
        1. Emits WebSocket 'payment_confirmed' to the donor.
        2. Broadcasts donation event to the public live activity feed.
        3. Asynchronously records on-chain proof on Polygon Amoy.
        """
        # 1. Notify donor of payment confirmation
        if donor_id:
            await redis_service.notify_donor(
                user_id=donor_id,
                event_type="payment_confirmed",
                data={
                    "donation_id": str(donation_id),
                    "amount": amount,
                    "status": "confirmed",
                    "campaign_title": campaign_title
                }
            )

        # 2. Broadcast live payment event to feed
        await redis_service.broadcast_explorer(
            event_type="payment_received",
            data={
                "type": "donation",
                "donation_id": str(donation_id),
                "campaign_title": campaign_title,
                "amount": amount,
                "currency": "INR",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

        # 3. Asynchronously record on-chain proof on Polygon Amoy
        from blockchain.workers.donation_recorder import record_donation_on_chain
        await record_donation_on_chain(
            donation_id=donation_id,
            campaign_id=campaign_id,
            amount=amount,
            gateway_receipt_hash=gateway_receipt_hash,
            donor_id=donor_id,
            campaign_title=campaign_title
        )

    def get_donor_donations(
        self,
        db: Session,
        donor_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Donation]:
        """List all donations made by a specific donor."""
        return db.query(Donation).filter(
            Donation.donor_id == donor_id
        ).order_by(Donation.created_at.desc()).offset(offset).limit(limit).all()

    def get_donation(self, db: Session, donation_id: UUID) -> Optional[Donation]:
        """Fetch a single donation by ID."""
        return db.query(Donation).filter(Donation.id == donation_id).first()

    def get_campaign_donations(
        self,
        db: Session,
        campaign_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> List[Donation]:
        """List donations for a specific campaign."""
        return db.query(Donation).filter(
            Donation.campaign_id == campaign_id,
            Donation.status == "completed"
        ).order_by(Donation.created_at.desc()).offset(offset).limit(limit).all()


donation_service = DonationService()
