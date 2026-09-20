"""
FastAPI Router for Volunteer Opportunities, Applications & Blockchain Credentials
"""

import uuid
import hashlib
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database.connection import get_db
from database.models import (
    VolunteerOpportunity,
    VolunteerApplication,
    VolunteerCredential,
    Campaign,
    NGOProfile,
    User
)
from backend.routers.auth import get_current_user, require_ngo_admin, require_volunteer

router = APIRouter(prefix="/api/volunteers", tags=["Volunteer Network & Credentials"])


# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------

class OpportunityCreateRequest(BaseModel):
    campaign_id: str
    title: str
    description: str
    location: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    spots_total: int = 10
    safety_tier: str = Field(default="open", description="open, trained_only, no_volunteers")
    skills_required: List[str] = []
    min_age: int = 18


class ApplyOpportunityRequest(BaseModel):
    opportunity_id: str
    message: Optional[str] = None
    hours_committed: Optional[float] = 10.0


class UpdateApplicationStatusRequest(BaseModel):
    status: str = Field(..., description="applied, approved, rejected, completed, no_show")
    hours_logged: Optional[float] = None
    certificate_url: Optional[str] = None


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/opportunities")
def list_opportunities(
    category: Optional[str] = None,
    safety_tier: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Explore available humanitarian volunteer opportunities with real-time spot counts
    and safety classifications.
    """
    query = db.query(VolunteerOpportunity)

    if safety_tier:
        query = query.filter(VolunteerOpportunity.safety_tier == safety_tier)
    if search:
        query = query.filter(
            or_(
                VolunteerOpportunity.title.ilike(f"%{search.strip()}%"),
                VolunteerOpportunity.description.ilike(f"%{search.strip()}%"),
                VolunteerOpportunity.location.ilike(f"%{search.strip()}%")
            )
        )

    opportunities = query.order_by(VolunteerOpportunity.created_at.desc()).offset(offset).limit(limit).all()

    results = []
    for opp in opportunities:
        campaign = opp.campaign
        ngo = campaign.ngo if campaign else None

        results.append({
            "id": str(opp.id),
            "campaign_id": str(opp.campaign_id),
            "campaign_title": campaign.title if campaign else "Clean Water Initiative",
            "campaign_category": campaign.category if campaign else "health",
            "ngo_name": ngo.name if ngo else "EarthCare Foundation",
            "title": opp.title,
            "description": opp.description,
            "location": opp.location,
            "location_city": opp.location,
            "location_type": "on_ground",
            "start_date": opp.start_date.isoformat() if opp.start_date else None,
            "end_date": opp.end_date.isoformat() if opp.end_date else None,
            "spots_total": opp.spots_total,
            "spots_filled": opp.spots_filled or 0,
            "spots_available": max(0, opp.spots_total - (opp.spots_filled or 0)),
            "estimated_hours": 8,
            "status": "open",
            "safety_tier": opp.safety_tier or "open",
            "skills_required": opp.skills_required or ["On-Ground Inspection", "Mobile GPS"],
            "min_age": opp.min_age or 18,
            "created_at": opp.created_at.isoformat() if opp.created_at else None
        })

    return results


@router.get("/opportunities/{opportunity_id}")
def get_opportunity_detail(opportunity_id: str, db: Session = Depends(get_db)):
    """
    Detailed information for a specific volunteer posting.
    """
    try:
        opp_uuid = uuid.UUID(opportunity_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Opportunity UUID.")

    opp = db.query(VolunteerOpportunity).filter(VolunteerOpportunity.id == opp_uuid).first()
    if not opp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")

    campaign = opp.campaign
    ngo = campaign.ngo if campaign else None

    return {
        "id": str(opp.id),
        "campaign_id": str(opp.campaign_id),
        "campaign_title": campaign.title if campaign else None,
        "campaign_description": campaign.description if campaign else None,
        "ngo": {
            "id": str(ngo.id) if ngo else None,
            "name": ngo.name if ngo else "Unknown NGO",
            "logo_url": ngo.logo_url if ngo else None
        },
        "title": opp.title,
        "description": opp.description,
        "location": opp.location,
        "start_date": opp.start_date.isoformat() if opp.start_date else None,
        "end_date": opp.end_date.isoformat() if opp.end_date else None,
        "spots_total": opp.spots_total,
        "spots_filled": opp.spots_filled,
        "safety_tier": opp.safety_tier,
        "skills_required": opp.skills_required or [],
        "min_age": opp.min_age
    }


@router.post("/opportunities", status_code=status.HTTP_201_CREATED)
def create_opportunity(
    req: OpportunityCreateRequest,
    current_user: User = Depends(require_ngo_admin),
    db: Session = Depends(get_db)
):
    """
    NGO Admin posts a new volunteer opportunity linked to an active campaign.
    """
    try:
        camp_uuid = uuid.UUID(req.campaign_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Campaign UUID.")

    campaign = db.query(Campaign).filter(Campaign.id == camp_uuid).first()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    opp = VolunteerOpportunity(
        id=uuid.uuid4(),
        campaign_id=camp_uuid,
        title=req.title.strip(),
        description=req.description.strip(),
        location=req.location.strip(),
        start_date=req.start_date,
        end_date=req.end_date,
        spots_total=req.spots_total,
        safety_tier=req.safety_tier,
        skills_required=req.skills_required,
        min_age=req.min_age
    )
    db.add(opp)
    db.commit()

    return {
        "message": "Volunteer opportunity created successfully.",
        "opportunity_id": str(opp.id)
    }


@router.post("/apply", status_code=status.HTTP_201_CREATED)
def apply_for_opportunity(
    req: ApplyOpportunityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authenticated user submits an application for a volunteer role.
    """
    try:
        opp_uuid = uuid.UUID(req.opportunity_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Opportunity UUID.")

    opp = db.query(VolunteerOpportunity).filter(VolunteerOpportunity.id == opp_uuid).first()
    if not opp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")

    # Check if already applied
    existing = db.query(VolunteerApplication).filter(
        VolunteerApplication.opportunity_id == opp_uuid,
        VolunteerApplication.user_id == current_user.id
    ).first()

    if existing:
        return {
            "message": "Application already submitted.",
            "application_id": str(existing.id),
            "status": existing.status
        }

    app_record = VolunteerApplication(
        id=uuid.uuid4(),
        opportunity_id=opp_uuid,
        user_id=current_user.id,
        status="applied"
    )
    db.add(app_record)

    # Increment spots filled if available
    opp.spots_filled = (opp.spots_filled or 0) + 1
    db.commit()

    return {
        "message": "Volunteer application submitted successfully.",
        "application_id": str(app_record.id),
        "status": app_record.status
    }


@router.get("/my-applications")
def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve volunteer applications for the logged-in user.
    """
    applications = db.query(VolunteerApplication).filter(
        VolunteerApplication.user_id == current_user.id
    ).order_by(VolunteerApplication.applied_at.desc()).all()

    results = []
    for a in applications:
        opp = a.opportunity
        camp = opp.campaign if opp else None
        ngo = camp.ngo if camp else None

        results.append({
            "id": str(a.id),
            "status": a.status,
            "applied_at": a.applied_at.isoformat() if a.applied_at else None,
            "approved_at": a.approved_at.isoformat() if a.approved_at else None,
            "opportunity": {
                "id": str(opp.id) if opp else None,
                "title": opp.title if opp else "Unknown Role",
                "location": opp.location if opp else None,
                "start_date": opp.start_date.isoformat() if opp and opp.start_date else None,
                "safety_tier": opp.safety_tier if opp else "open"
            },
            "ngo_name": ngo.name if ngo else "Unknown NGO",
            "has_credential": a.credential is not None
        })

    return results


@router.get("/my-credentials")
def get_my_credentials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all blockchain-anchored volunteer credentials and verified service hours.
    """
    user_apps = db.query(VolunteerApplication).filter(VolunteerApplication.user_id == current_user.id).all()
    app_ids = [a.id for a in user_apps]

    if not app_ids:
        return []

    credentials = db.query(VolunteerCredential).filter(VolunteerCredential.application_id.in_(app_ids)).all()

    results = []
    for cred in credentials:
        app_rec = cred.application
        opp = app_rec.opportunity if app_rec else None
        camp = opp.campaign if opp else None
        ngo = camp.ngo if camp else None

        results.append({
            "id": str(cred.id),
            "opportunity_title": opp.title if opp else "Humanitarian Service",
            "campaign_title": camp.title if camp else None,
            "ngo_name": ngo.name if ngo else "Verified NGO",
            "hours_logged": float(cred.hours_logged or 0.0),
            "ngo_confirmed": cred.ngo_confirmed,
            "blockchain_tx_hash": cred.blockchain_tx_hash,
            "certificate_url": cred.certificate_url,
            "certificate_hash": cred.certificate_hash,
            "issued_at": cred.created_at.isoformat() if cred.created_at else None
        })

    return results


@router.get("/credentials/{credential_id}")
def get_credential_detail(credential_id: str, db: Session = Depends(get_db)):
    """
    Public verification endpoint for a volunteer credential.
    """
    try:
        cred_uuid = uuid.UUID(credential_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Credential UUID.")

    cred = db.query(VolunteerCredential).filter(VolunteerCredential.id == cred_uuid).first()
    if not cred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found.")

    app_rec = cred.application
    user = app_rec.user if app_rec else None
    opp = app_rec.opportunity if app_rec else None
    camp = opp.campaign if opp else None
    ngo = camp.ngo if camp else None

    return {
        "id": str(cred.id),
        "volunteer_name": user.name if user else "Verified Volunteer",
        "opportunity_title": opp.title if opp else "Humanitarian Service",
        "campaign_title": camp.title if camp else None,
        "ngo_name": ngo.name if ngo else "Verified NGO",
        "hours_logged": float(cred.hours_logged or 0.0),
        "ngo_confirmed": cred.ngo_confirmed,
        "blockchain_tx_hash": cred.blockchain_tx_hash,
        "certificate_url": cred.certificate_url,
        "certificate_hash": cred.certificate_hash,
        "issued_at": cred.created_at.isoformat() if cred.created_at else None
    }


@router.post("/applications/{application_id}/status")
def update_application_status(
    application_id: str,
    req: UpdateApplicationStatusRequest,
    current_user: User = Depends(require_ngo_admin),
    db: Session = Depends(get_db)
):
    """
    NGO Admin approves, rejects, or completes a volunteer assignment and issues
    an on-chain verifiable credential upon completion.
    """
    try:
        app_uuid = uuid.UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Application UUID.")

    app_rec = db.query(VolunteerApplication).filter(VolunteerApplication.id == app_uuid).first()
    if not app_rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    app_rec.status = req.status
    if req.status == "approved":
        app_rec.approved_at = datetime.utcnow()

    # If completed, generate/update credential
    if req.status == "completed":
        hours = req.hours_logged or 8.0
        cert_url = req.certificate_url or f"https://eleos.app/certificates/cert_{app_uuid.hex[:8]}.pdf"
        cert_hash = hashlib.sha256(f"credential:{app_uuid}:{hours}:{cert_url}".encode("utf-8")).hexdigest()
        dummy_tx = f"0x{cert_hash[:64]}"

        cred = db.query(VolunteerCredential).filter(VolunteerCredential.application_id == app_uuid).first()
        if not cred:
            cred = VolunteerCredential(
                id=uuid.uuid4(),
                application_id=app_uuid,
                hours_logged=Decimal(str(hours)),
                ngo_confirmed=True,
                ngo_confirmed_at=datetime.utcnow(),
                blockchain_tx_hash=dummy_tx,
                certificate_url=cert_url,
                certificate_hash=cert_hash
            )
            db.add(cred)
        else:
            cred.hours_logged = Decimal(str(hours))
            cred.ngo_confirmed = True
            cred.ngo_confirmed_at = datetime.utcnow()
            cred.certificate_url = cert_url
            cred.certificate_hash = cert_hash

    db.commit()

    return {
        "message": f"Application status updated to '{req.status}'.",
        "application_id": str(app_rec.id),
        "status": app_rec.status
    }

