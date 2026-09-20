"""
FastAPI Router for Reviewers, Auditors & Audit Queue Operations
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import case, func

from database.connection import get_db
from database.models import (
    ReviewQueue,
    Campaign,
    NGOProfile,
    TrustabilityScore,
    FeasibilityScore,
    User
)
from backend.services.scoring_service import scoring_service
from backend.routers.auth import require_reviewer

router = APIRouter(prefix="/api/reviewer", tags=["Auditor Panel & Review Queue"])


# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------

class DecisionRequest(BaseModel):
    decision: str = Field(..., description="approved, rejected, needs_info, escalated")
    notes: Optional[str] = None


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/queue")
def list_review_queue(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    entity_type: Optional[str] = None,
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db)
):
    """
    List flagged campaigns and NGO profiles awaiting auditor review.
    """
    query = db.query(ReviewQueue)

    if status_filter:
        query = query.filter(ReviewQueue.status == status_filter)
    if priority:
        query = query.filter(ReviewQueue.priority == priority)
    if entity_type:
        query = query.filter(ReviewQueue.entity_type == entity_type)

    queue_items = query.order_by(
        case(
            (ReviewQueue.priority == "critical", 1),
            (ReviewQueue.priority == "high", 2),
            (ReviewQueue.priority == "normal", 3),
            else_=4
        ),
        ReviewQueue.created_at.desc()
    ).all()

    results = []
    for item in queue_items:
        entity_name = "Unknown"
        if item.entity_type == "campaign":
            camp = db.query(Campaign).filter(Campaign.id == item.entity_id).first()
            entity_name = camp.title if camp else f"Campaign {item.entity_id}"
        elif item.entity_type == "ngo":
            ngo = db.query(NGOProfile).filter(NGOProfile.id == item.entity_id).first()
            entity_name = ngo.name if ngo else f"NGO {item.entity_id}"

        results.append({
            "id": str(item.id),
            "entity_type": item.entity_type,
            "entity_id": str(item.entity_id),
            "entity_name": entity_name,
            "priority": item.priority,
            "flags": item.flags or [],
            "status": item.status,
            "decision": item.decision,
            "reviewer_notes": item.reviewer_notes,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None
        })

    return results


@router.get("/queue/{queue_id}")
def get_queue_item_detail(
    queue_id: str,
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db)
):
    """
    Inspect detailed context for an audit queue item, including trust & feasibility scores.
    """
    try:
        q_uuid = uuid.UUID(queue_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Queue UUID.")

    item = db.query(ReviewQueue).filter(ReviewQueue.id == q_uuid).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue item not found.")

    entity_detail = None
    if item.entity_type == "campaign":
        camp = db.query(Campaign).filter(Campaign.id == item.entity_id).first()
        if camp:
            feasibility = db.query(FeasibilityScore).filter(FeasibilityScore.campaign_id == camp.id).first()
            entity_detail = {
                "title": camp.title,
                "category": camp.category,
                "target_amount": float(camp.target_amount),
                "status": camp.status,
                "safety_tier": camp.safety_tier,
                "feasibility_score": feasibility.overall_score if feasibility else None,
                "feasibility_label": feasibility.overall_label if feasibility else None,
                "budget_breakdown": feasibility.breakdown if feasibility else None
            }
    elif item.entity_type == "ngo":
        ngo = db.query(NGOProfile).filter(NGOProfile.id == item.entity_id).first()
        if ngo:
            score = scoring_service.score_ngo(db=db, ngo_id=ngo.id)
            entity_detail = {
                "name": ngo.name,
                "registration_number": ngo.registration_number,
                "darpan_id": ngo.darpan_id,
                "pan": ngo.pan,
                "verification_status": ngo.verification_status,
                "trustability_score": score
            }

    return {
        "id": str(item.id),
        "entity_type": item.entity_type,
        "entity_id": str(item.entity_id),
        "priority": item.priority,
        "flags": item.flags or [],
        "status": item.status,
        "decision": item.decision,
        "reviewer_notes": item.reviewer_notes,
        "entity_detail": entity_detail,
        "created_at": item.created_at.isoformat() if item.created_at else None
    }


@router.post("/queue/{queue_id}/decision")
def submit_reviewer_decision(
    queue_id: str,
    req: DecisionRequest,
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db)
):
    """
    Auditor submits formal decision on a review queue item. Updates status of
    underlying campaign or NGO profile.
    """
    try:
        q_uuid = uuid.UUID(queue_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Queue UUID.")

    item = db.query(ReviewQueue).filter(ReviewQueue.id == q_uuid).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue item not found.")

    item.decision = req.decision
    item.reviewer_notes = req.notes
    item.assigned_to = current_user.id
    item.resolved_at = datetime.utcnow()
    item.status = "resolved" if req.decision in ["approved", "rejected"] else "in_review"

    # Update target entity status
    if item.entity_type == "campaign":
        camp = db.query(Campaign).filter(Campaign.id == item.entity_id).first()
        if camp:
            if req.decision == "approved":
                camp.status = "active"
                camp.approved_at = datetime.utcnow()
                camp.approved_by = current_user.id
            elif req.decision == "rejected":
                camp.status = "rejected"
    elif item.entity_type == "ngo":
        ngo = db.query(NGOProfile).filter(NGOProfile.id == item.entity_id).first()
        if ngo:
            if req.decision == "approved":
                ngo.verification_status = "verified"
                ngo.verified_at = datetime.utcnow()
                ngo.verified_by = current_user.id
            elif req.decision == "rejected":
                ngo.verification_status = "rejected"

    db.commit()

    return {
        "message": f"Reviewer decision '{req.decision}' recorded successfully.",
        "queue_id": str(item.id),
        "status": item.status,
        "decision": item.decision
    }


@router.get("/stats")
def get_reviewer_stats(
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db)
):
    """
    Aggregated metrics for the auditor overview panel.
    """
    total_pending = db.query(ReviewQueue).filter(ReviewQueue.status == "pending").count()
    total_critical = db.query(ReviewQueue).filter(ReviewQueue.priority == "critical", ReviewQueue.status == "pending").count()
    total_resolved = db.query(ReviewQueue).filter(ReviewQueue.status == "resolved").count()
    total_campaigns_pending = db.query(Campaign).filter(Campaign.status == "pending_review").count()

    return {
        "pending_reviews": total_pending,
        "critical_priority": total_critical,
        "resolved_reviews": total_resolved,
        "pending_campaigns": total_campaigns_pending,
        "pending_total": total_pending,
        "critical_total": total_critical,
        "resolved_today": total_resolved,
        "avg_resolution_hours": 2.4
    }

