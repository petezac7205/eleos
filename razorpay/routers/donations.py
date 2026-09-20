"""
FastAPI Router for Razorpay Payments & Donations
"""

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Header, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

# Import DB session dependency from database module
from database.connection import get_db
from database.models import User
from backend.routers.auth import get_current_user

from razorpay.schemas.donation import (
    DonationInitiateRequest,
    DonationInitiateResponse,
    DonationVerifyRequest,
    DonationVerifyResponse,
    DonationResponse,
    DonationListResponse
)
from razorpay.services.donation_service import donation_service

router = APIRouter(prefix="/api/donations", tags=["Donations & Razorpay"])


# -----------------------------------------------------------------------------
# 1. Initiate Donation (Creates Razorpay Order & DB record)
# -----------------------------------------------------------------------------
@router.post("/initiate", response_model=DonationInitiateResponse, status_code=status.HTTP_201_CREATED)
async def initiate_donation(
    request: DonationInitiateRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db)
):
    """
    Initiate a donation for a campaign:
    1. Generates an order with Razorpay.
    2. Stores the initiated donation record in PostgreSQL.
    3. Returns order details for Razorpay checkout sheet.
    4. Handles client idempotency to prevent duplicate orders.
    """
    if idempotency_key and not request.idempotency_key:
        request.idempotency_key = idempotency_key
    return donation_service.initiate_donation(db=db, request=request)


# Convenience aliases for /api/donations/donate and /api/donations/create-order
@router.post("/donate", response_model=DonationInitiateResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/create-order", response_model=DonationInitiateResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def donate_alias(
    request: DonationInitiateRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db)
):
    if idempotency_key and not request.idempotency_key:
        request.idempotency_key = idempotency_key
    return donation_service.initiate_donation(db=db, request=request)


# -----------------------------------------------------------------------------
# 2. Client Payment Verification (Instant checkout callback)
# -----------------------------------------------------------------------------
@router.post("/verify", response_model=DonationVerifyResponse)
async def verify_payment(
    verify_req: DonationVerifyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Verify payment signature upon Razorpay checkout completion:
    1. Verifies HMAC-SHA256 signature.
    2. Updates donation status to 'completed'.
    3. Triggers background task for Polygon blockchain recording & WebSocket alerts.
    """
    return donation_service.verify_client_payment(
        db=db,
        verify_req=verify_req,
        background_tasks=background_tasks
    )


# -----------------------------------------------------------------------------
# 3. Razorpay Server-to-Server Webhook Handler
# -----------------------------------------------------------------------------
@router.post("/webhook", include_in_schema=True)
@router.post("/webhooks/razorpay", include_in_schema=False)
async def razorpay_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    db: Session = Depends(get_db)
):
    """
    Razorpay Webhook receiver:
    1. Validates webhook signature header.
    2. Processes payment.captured and payment.failed events.
    3. Idempotently updates database state and initiates blockchain writes.
    """
    if not x_razorpay_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'X-Razorpay-Signature' header in webhook request."
        )

    raw_body = await request.body()
    return donation_service.process_webhook_event(
        db=db,
        raw_body=raw_body,
        signature=x_razorpay_signature,
        background_tasks=background_tasks
    )


# -----------------------------------------------------------------------------
# 4. Get Authenticated Donor's Donations
# -----------------------------------------------------------------------------
@router.get("/my-donations", response_model=DonationListResponse)
async def get_my_donations(
    limit: int = 50,
    offset: int = 0,
    current_user: "User" = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all donations made by the currently authenticated donor."""
    donations = donation_service.get_donor_donations(
        db=db,
        donor_id=current_user.id,
        limit=limit,
        offset=offset
    )
    result_donations = []
    for d in donations:
        c = d.campaign
        ngo = c.ngo if c else None
        d_resp = DonationResponse(
            id=d.id,
            donor_id=d.donor_id,
            campaign_id=d.campaign_id,
            amount=float(d.amount),
            currency=d.currency or "INR",
            payment_method=d.payment_method,
            payment_gateway_order_id=d.payment_gateway_order_id,
            payment_gateway_payment_id=d.payment_gateway_payment_id,
            status=d.status,
            blockchain_tx_hash=d.blockchain_tx_hash,
            blockchain_confirmed=d.blockchain_confirmed,
            donor_message=d.donor_message,
            is_anonymous=d.is_anonymous,
            campaign_title=c.title if c else "Humanitarian Campaign",
            ngo_name=ngo.name if ngo else "Verified NGO",
            created_at=d.created_at,
            completed_at=d.completed_at
        )
        result_donations.append(d_resp)
    return DonationListResponse(total=len(result_donations), donations=result_donations)


# -----------------------------------------------------------------------------
# 5. Get Donation Details
# -----------------------------------------------------------------------------
@router.get("/{donation_id}", response_model=DonationResponse)
async def get_donation(
    donation_id: UUID,
    db: Session = Depends(get_db)
):
    """Retrieve details and blockchain verification status for a specific donation."""
    donation = donation_service.get_donation(db=db, donation_id=donation_id)
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donation '{donation_id}' not found."
        )
    return donation


# -----------------------------------------------------------------------------
# 6. List Donations for Campaign
# -----------------------------------------------------------------------------
@router.get("/campaign/{campaign_id}", response_model=DonationListResponse)
async def list_campaign_donations(
    campaign_id: UUID,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List recent completed donations for a campaign."""
    donations = donation_service.get_campaign_donations(
        db=db,
        campaign_id=campaign_id,
        limit=limit,
        offset=offset
    )
    return DonationListResponse(total=len(donations), donations=donations)

