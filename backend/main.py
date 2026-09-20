"""
Eleos Unified Backend Gateway (FastAPI)
Brings together Auth, Campaigns, NGO Profiles, Volunteer Network, Reviewer Panel,
Scoring, Payments (Razorpay), and Blockchain Explorer (Polygon Amoy).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routers.auth import router as auth_router
from backend.routers.scoring import router as scoring_router
from backend.routers.campaigns import router as campaigns_router
from backend.routers.ngo import router as ngo_router
from backend.routers.volunteers import router as volunteers_router
from backend.routers.reviewer import router as reviewer_router
from backend.routers.donor_review import router as donor_review_router
from razorpay.routers.donations import router as donations_router
from blockchain.routers.explorer import router as explorer_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Unified API Gateway for Eleos Transparent Charity, Scoring, Payments & Blockchain Ledger.",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# -----------------------------------------------------------------------------
# CORS Middleware
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Mount Routers
# -----------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(scoring_router)
app.include_router(campaigns_router)
app.include_router(ngo_router)
app.include_router(volunteers_router)
app.include_router(reviewer_router)
app.include_router(donor_review_router)
app.include_router(donations_router)
app.include_router(explorer_router)

import os
from fastapi.staticfiles import StaticFiles

# -----------------------------------------------------------------------------
# Static Media Mount (email video and preview assets)
# -----------------------------------------------------------------------------
media_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "media"))
if not os.path.exists(media_path):
    media_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "images"))
if os.path.exists(media_path):
    app.mount("/media", StaticFiles(directory=media_path), name="media")


# -----------------------------------------------------------------------------
# Health & Status
# -----------------------------------------------------------------------------
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "gateway": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "supabase_connected",
        "blockchain_network": "polygon_amoy",
        "contract_address": settings.CONTRACT_ADDRESS
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
