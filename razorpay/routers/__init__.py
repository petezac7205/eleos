"""
Routers package for Razorpay payments and donations
"""

from razorpay.routers.donations import router as donations_router

__all__ = ["donations_router"]

