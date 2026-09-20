"""
Eleos Payment Microservice (FastAPI)
Standalone entrypoint for testing and running the Razorpay payment module.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from razorpay.routers.donations import router as donations_router
from razorpay.config import settings
from uuid import UUID

app = FastAPI(
    title="Eleos Payment & Razorpay Service",
    description="Payment orchestration, UPI checkout, Razorpay webhook handling, and Polygon blockchain logging for Eleos.",
    version="1.0.0"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Payment Router
app.include_router(donations_router)


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "eleos-razorpay-payments",
        "currency": settings.RAZORPAY_CURRENCY,
        "test_mode": settings.TEST_MODE
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("razorpay.main:app", host="0.0.0.0", port=8001, reload=True)

