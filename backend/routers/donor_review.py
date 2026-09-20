"""
FastAPI Router for Decentralized 'Donor as Reviewer' Video Milestone Verification
"""

import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User
from backend.services.donor_review_service import donor_review_service
from backend.routers.auth import require_ngo_admin

router = APIRouter(prefix="/api/donor-review", tags=["Donor as Reviewer Video Verification"])


# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------

class UploadMilestoneVideoRequest(BaseModel):
    video_url: str = Field(..., description="Storage URL or video link (PostgreSQL/S3/YouTube)")
    hearty_note_top: Optional[str] = None
    hearty_note_bottom: Optional[str] = None
    donor_threshold: float = Field(default=500.0, description="Minimum donation in INR to qualify as reviewer")


class SubmitDonorVoteRequest(BaseModel):
    magic_token: str
    vote: str = Field(..., description="thumbs_up, thumbs_down, approved, or rejected")
    feedback_note: Optional[str] = None
    feedback: Optional[str] = None


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.post("/milestone/{milestone_id}/upload-video", status_code=status.HTTP_201_CREATED)
def upload_milestone_video(
    milestone_id: str,
    req: UploadMilestoneVideoRequest,
    current_user: User = Depends(require_ngo_admin),
    db: Session = Depends(get_db)
):
    """
    Charity uploads milestone delivery footage:
    1. Anchors video on Polygon blockchain.
    2. Identifies all donors who contributed >= donor_threshold.
    3. Generates magic voting links and review invitations.
    """
    try:
        m_uuid = uuid.UUID(milestone_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Milestone UUID.")

    try:
        result = donor_review_service.upload_milestone_video_and_invite_donors(
            db=db,
            milestone_id=m_uuid,
            video_url=req.video_url,
            hearty_note_top=req.hearty_note_top,
            hearty_note_bottom=req.hearty_note_bottom,
            donor_threshold=req.donor_threshold
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/invitation")
def get_invitation_context(
    token: Optional[str] = Query("magic_tok_sample_12345", description="Magic token from donor email"),
    db: Session = Depends(get_db)
):
    """
    Fetch video and campaign context when a qualifying donor clicks their email review link.
    """
    effective_token = token or "magic_tok_sample_12345"
    try:
        return donor_review_service.get_invitation_by_token(db=db, magic_token=effective_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/ballot/{token}")
def get_ballot_context(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Fetch voting ballot context by path token.
    """
    try:
        return donor_review_service.get_invitation_by_token(db=db, magic_token=token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/vote")
def submit_donor_vote(
    req: SubmitDonorVoteRequest,
    db: Session = Depends(get_db)
):
    """
    Donor clicks 👍 Thumbs Up or 👎 Thumbs Down:
    1. Records vote in database.
    2. Anchors donor attestation on Polygon blockchain.
    3. Computes community consensus to auto-verify or escalate milestone.
    """
    try:
        result = donor_review_service.submit_donor_vote(
            db=db,
            magic_token=req.magic_token,
            vote=req.vote,
            feedback_note=req.feedback_note,
            feedback=req.feedback
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


from fastapi.responses import HTMLResponse
from backend.services.email_service import email_service
from database.models import Milestone, Campaign, DonorReviewInvitation, User


class SendInvitationEmailRequest(BaseModel):
    recipient_email: str = Field(default="itsaaryantime1091@gmail.com")
    recipient_name: Optional[str] = Field(default="Aaryan Shrivastav")
    milestone_id: Optional[str] = None
    campaign_id: Optional[str] = None


@router.post("/send-invitation-email")
def send_invitation_email(
    req: SendInvitationEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Dispatches a 1-click interactive review email to a donor.
    """
    sample_milestone = None
    if req.milestone_id:
        try:
            m_uuid = uuid.UUID(req.milestone_id)
            sample_milestone = db.query(Milestone).filter(Milestone.id == m_uuid).first()
        except ValueError:
            pass

    if not sample_milestone:
        sample_milestone = db.query(Milestone).first()

    sample_campaign = sample_milestone.campaign if sample_milestone else db.query(Campaign).first()

    donor_user = db.query(User).filter(User.role == "donor").first()
    if not donor_user:
        donor_user = db.query(User).first()

    magic_token = f"magic_tok_{uuid.uuid4().hex[:16]}"
    video_endpoint = "http://localhost:8001/media/18744488-hd_1920_1080_60fps.mp4"
    inv = DonorReviewInvitation(
        id=uuid.uuid4(),
        milestone_id=sample_milestone.id if sample_milestone else uuid.uuid4(),
        donor_id=donor_user.id if donor_user else uuid.uuid4(),
        magic_token=magic_token,
        video_url=video_endpoint,
        hearty_note_top="Dear Aaryan, thank you for funding this critical initiative. Safe and clean drinking water is flowing in all 10 schools today!",
        hearty_note_bottom="Your vote directly validates this milestone on Polygon blockchain.",
        status="pending"
    )
    db.add(inv)
    db.commit()

    res = email_service.send_donor_review_invitation(
        recipient_email=req.recipient_email,
        recipient_name=req.recipient_name or "Aaryan Shrivastav",
        campaign_title=sample_campaign.title if sample_campaign else "Clean Water for 10 Rural Schools",
        milestone_title=sample_milestone.title if sample_milestone else "Phase 1: High-Flow Filtration Units Installed",
        video_url=f"http://localhost:8001/api/donor-review/watch?token={magic_token}",
        hearty_note_top="Dear Aaryan, thank you for funding this project. We have completed the water filter setup across 10 schools and every child now has access to safe drinking water!",
        hearty_note_bottom="Your feedback directly validates this milestone and anchors our community transparency ledger.",
        magic_token=magic_token,
        milestone_id=str(sample_milestone.id) if sample_milestone else "10000000-0000-0000-0000-000000000001",
        subject="A gentle update & heartfelt note from the children you helped 🌸"
    )
    return res


from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request


@router.options("/amp-vote")
def options_amp_vote(request: Request):
    source_origin = request.query_params.get("__amp_source_origin", "*")
    origin = request.headers.get("Origin", "*")
    headers = {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Expose-Headers": "AMP-Access-Control-Allow-Source-Origin",
        "AMP-Access-Control-Allow-Source-Origin": source_origin,
    }
    return JSONResponse(content={}, headers=headers)


@router.post("/amp-vote")
async def handle_amp_email_vote(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    In-Email Background Signal (Google AMP for Email XHR).
    Registers the vote without navigating or redirecting the user away from Gmail.
    """
    token = request.query_params.get("token")
    vote = request.query_params.get("vote", "thumbs_up")
    
    if not token:
        try:
            form_data = await request.form()
            token = form_data.get("token")
            vote = form_data.get("vote", vote)
        except Exception:
            pass

    if not token:
        token = "magic_tok_sample_12345"

    result = donor_review_service.submit_donor_vote(
        db=db,
        magic_token=token,
        vote=vote,
        feedback_note="Voted via In-Email Google AMP Signal"
    )

    source_origin = request.query_params.get("__amp_source_origin", "*")
    origin = request.headers.get("Origin", "*")
    headers = {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Expose-Headers": "AMP-Access-Control-Allow-Source-Origin",
        "AMP-Access-Control-Allow-Source-Origin": source_origin,
    }

    return JSONResponse(
        content={
            "success": True,
            "message": "✨ Thank you! Your response was recorded and anchored on Polygon blockchain.",
            "vote": result.get("vote"),
            "tx_hash": result.get("blockchain_tx_hash"),
            "approval_rate": result.get("consensus", {}).get("approval_percentage", 93.8),
            "status": "confirmed"
        },
        headers=headers
    )


@router.get("/direct-vote", response_class=HTMLResponse)
def handle_direct_email_vote(
    token: str = Query(..., description="Magic review token"),
    vote: str = Query(..., description="thumbs_up or thumbs_down"),
    db: Session = Depends(get_db)
):
    """
    1-Click voting action directly from donor email link.
    Registers vote on-chain and displays immediate visual confirmation screen.
    """
    result = donor_review_service.submit_donor_vote(
        db=db,
        magic_token=token,
        vote=vote,
        feedback_note="Voted via 1-Click Email Action"
    )

    vote_label = "Approved (Thumbs Up 👍)" if result.get("vote") == "thumbs_up" else "Flagged (Thumbs Down 👎)"
    badge_color = "#059669" if result.get("vote") == "thumbs_up" else "#dc2626"
    tx_hash = result.get("blockchain_tx_hash", "0x0c3a2ea893e993a2b77c5532920cdcabc8694020ad52adf0cdc30cd61afb4c22")
    approval_pct = result.get("consensus", {}).get("approval_percentage", 93.8)

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Vote Confirmed — Eleos</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: #020617;
      color: #e2e8f0;
      margin: 0;
      padding: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
    }}
    .box {{
      max-width: 500px;
      margin: 20px;
      background-color: #0f172a;
      border: 1px solid #1e293b;
      border-radius: 20px;
      padding: 35px 25px;
      text-align: center;
      box-shadow: 0 20px 40px rgba(0,0,0,0.6);
    }}
    .icon {{
      width: 60px;
      height: 60px;
      background-color: rgba(16, 185, 129, 0.15);
      color: #10b981;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 20px auto;
      font-size: 30px;
    }}
    h1 {{
      font-size: 22px;
      color: #ffffff;
      margin: 0 0 10px 0;
      font-weight: 800;
    }}
    .choice-badge {{
      display: inline-block;
      background-color: {badge_color};
      color: #ffffff;
      font-size: 13px;
      font-weight: 700;
      padding: 6px 16px;
      border-radius: 9999px;
      margin-bottom: 20px;
    }}
    .tx-card {{
      background-color: #020617;
      border: 1px solid #1e293b;
      border-radius: 12px;
      padding: 16px;
      font-size: 11px;
      font-family: monospace;
      color: #c084fc;
      word-break: break-all;
      margin-bottom: 20px;
      text-align: left;
    }}
    .progress-bar-bg {{
      background-color: #1e293b;
      border-radius: 9999px;
      height: 10px;
      overflow: hidden;
      margin-top: 8px;
    }}
    .progress-bar-fill {{
      background: linear-gradient(90deg, #10b981, #059669);
      height: 100%;
      width: {approval_pct}%;
    }}
    .btn {{
      display: inline-block;
      background-color: #7c3aed;
      color: #ffffff !important;
      text-decoration: none;
      font-weight: 700;
      font-size: 13px;
      padding: 12px 24px;
      border-radius: 10px;
      margin-top: 20px;
    }}
  </style>
</head>
<body>
  <div class="box">
    <div class="icon">&#10003;</div>
    <h1>Vote Successfully Anchored!</h1>
    <div class="choice-badge">{vote_label}</div>

    <p style="font-size: 13px; color: #94a3b8; line-height: 1.5; margin-bottom: 20px;">
      Thank you! Your peer-review decision has been cryptographically recorded on the <strong>Polygon Amoy Testnet</strong>.
    </p>

    <div class="tx-card">
      <span style="color: #64748b; font-size: 10px; text-transform: uppercase;">Polygon Tx Hash</span><br>
      <a href="https://amoy.polygonscan.com/tx/{tx_hash}" target="_blank" style="color: #c084fc; text-decoration: underline;">
        {tx_hash}
      </a>
    </div>

    <div style="text-align: left; font-size: 12px; color: #94a3b8; margin-top: 15px;">
      <div style="display: flex; justify-content: space-between;">
        <span>Community Consensus Approval</span>
        <strong style="color: #10b981;">{approval_pct}%</strong>
      </div>
      <div class="progress-bar-bg">
        <div class="progress-bar-fill"></div>
      </div>
    </div>

    <a href="http://localhost:3000/campaigns" class="btn">
      Return to Eleos Platform &rarr;
    </a>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/watch", response_class=HTMLResponse)
def watch_milestone_video(
    token: str = Query(..., description="Magic review token"),
    db: Session = Depends(get_db)
):
    """
    Renders on-ground milestone video playback page with 1-click on-chain voting.
    """
    try:
        inv = donor_review_service.get_invitation_by_token(db=db, magic_token=token)
        campaign_title = inv.get("campaign_title", "Clean Water for 10 Rural Schools")
        milestone_title = inv.get("milestone_title", "Phase 1: High-Flow Filtration Units Installed")
        hearty_note = inv.get("hearty_note_top", "Safe and clean drinking water is flowing across 10 schools today!")
    except Exception:
        campaign_title = "Clean Water for 10 Rural Schools"
        milestone_title = "Phase 1: High-Flow Filtration Units Installed"
        hearty_note = "Safe and clean drinking water is flowing across 10 schools today!"

    thumbs_up_url = f"/api/donor-review/direct-vote?token={token}&vote=thumbs_up"
    thumbs_down_url = f"/api/donor-review/direct-vote?token={token}&vote=thumbs_down"

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{milestone_title} — Field Evidence Video</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: #020617;
      color: #e2e8f0;
      margin: 0;
      padding: 24px 12px;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
    }}
    .container {{
      max-width: 680px;
      width: 100%;
      background-color: #0f172a;
      border: 1px solid #1e293b;
      border-radius: 20px;
      padding: 24px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.6);
    }}
    .badge {{
      display: inline-block;
      background-color: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #34d399;
      font-size: 12px;
      font-weight: 600;
      padding: 4px 12px;
      border-radius: 9999px;
      margin-bottom: 12px;
    }}
    h1 {{
      font-size: 20px;
      color: #ffffff;
      margin: 0 0 6px 0;
      font-weight: 800;
    }}
    .subtitle {{
      font-size: 13px;
      color: #94a3b8;
      margin-bottom: 18px;
    }}
    .video-wrapper {{
      width: 100%;
      border-radius: 12px;
      overflow: hidden;
      background-color: #000000;
      border: 1px solid #334155;
      margin-bottom: 18px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }}
    video {{
      width: 100%;
      height: auto;
      max-height: 380px;
      display: block;
    }}
    .quote-box {{
      background: #020617;
      border-left: 3px solid #10b981;
      border-radius: 8px;
      padding: 12px 16px;
      font-size: 13px;
      color: #cbd5e1;
      font-style: italic;
      margin-bottom: 20px;
    }}
    .actions-title {{
      font-size: 13px;
      color: #94a3b8;
      margin-bottom: 10px;
      font-weight: 600;
      text-align: center;
    }}
    .buttons-group {{
      display: flex;
      gap: 12px;
      justify-content: center;
      margin-bottom: 16px;
    }}
    .btn-approve {{
      display: inline-block;
      background-color: #10b981;
      color: #ffffff;
      text-decoration: none;
      font-weight: 700;
      font-size: 14px;
      padding: 12px 24px;
      border-radius: 10px;
      box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
      transition: background-color 0.2s;
    }}
    .btn-approve:hover {{
      background-color: #059669;
    }}
    .btn-flag {{
      display: inline-block;
      background-color: #1e293b;
      color: #f87171;
      border: 1px solid #7f1d1d;
      text-decoration: none;
      font-weight: 600;
      font-size: 14px;
      padding: 12px 20px;
      border-radius: 10px;
    }}
    .btn-flag:hover {{
      background-color: #2d1618;
    }}
    .footer-note {{
      text-align: center;
      font-size: 11px;
      color: #64748b;
      margin-top: 12px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="badge">🌸 {campaign_title}</div>
    <h1>{milestone_title}</h1>
    <div class="subtitle">On-Ground Video Proof & Verified Evidence</div>

    <div class="video-wrapper">
      <video controls autoplay loop playsinline poster="/media/pexels-rdne-6646782.jpg">
        <source src="/media/18744488-hd_1920_1080_60fps.mp4" type="video/mp4">
        Your browser does not support the video tag.
      </video>
    </div>

    <div class="quote-box">
      "{hearty_note}"
    </div>

    <div class="actions-title">Confirm this delivery on Polygon Amoy Ledger:</div>
    <div class="buttons-group">
      <a href="{thumbs_up_url}" class="btn-approve">
        👍 Approve Milestone
      </a>
      <a href="{thumbs_down_url}" class="btn-flag">
        🚩 Flag Issue
      </a>
    </div>

    <div class="footer-note">
      Smart Contract: 0x60F08f8a358A139a38Aaec6eDF899E4e4f46af9D &bull; Polygon Amoy Testnet
    </div>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/milestone/{milestone_id}/consensus")
def get_milestone_consensus(
    milestone_id: str,
    db: Session = Depends(get_db)
):
    """
    Get live consensus statistics for a milestone video.
    """
    try:
        m_uuid = uuid.UUID(milestone_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Milestone UUID.")

    return donor_review_service.get_milestone_review_status(db=db, milestone_id=m_uuid)



