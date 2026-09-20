"""
Razorpay Payment Module Configuration
"""

import os
from pathlib import Path
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel as BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

# Locate and load root .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class PaymentSettings(BaseSettings):
    # Razorpay API Credentials
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "rzp_secret_placeholder")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "rzp_webhook_secret_placeholder")

    # Payment defaults
    RAZORPAY_CURRENCY: str = os.getenv("RAZORPAY_CURRENCY", "INR")
    MINIMUM_AMOUNT_INR: float = 1.0  # 1 INR = 100 paise

    # Redis Pub/Sub for WebSockets
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Allowed CORS Origins (comma-separated or list)
    ALLOWED_ORIGINS: list = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",") if origin.strip()]

    # Test / Simulation Mode Flag
    TEST_MODE: bool = os.getenv("RAZORPAY_TEST_MODE", "true").lower() in ("true", "1", "yes")

    model_config = ConfigDict(case_sensitive=True, extra="ignore")


settings = PaymentSettings()
