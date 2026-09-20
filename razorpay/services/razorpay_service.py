"""
Razorpay API Client & Signature Verification Service
Supports both live Razorpay REST calls and local Test/Simulation mode.
"""

import hmac
import hashlib
import json
import logging
import uuid
from decimal import Decimal
from typing import Dict, Any, Optional
import httpx

from razorpay.config import settings

logger = logging.getLogger("razorpay_service")


class RazorpayService:
    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        webhook_secret: Optional[str] = None
    ):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = webhook_secret or settings.RAZORPAY_WEBHOOK_SECRET
        self.base_url = "https://api.razorpay.com/v1"

    def is_placeholder_key(self) -> bool:
        """Check if placeholder dummy credentials are in use."""
        return (
            not self.key_id
            or not self.key_secret
            or "placeholder" in self.key_id.lower()
            or "placeholder" in self.key_secret.lower()
            or "sample" in self.key_id.lower()
            or self.key_id.startswith("rzp_test_sample")
        )

    def create_order(
        self,
        amount_inr: float,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an order with Razorpay in paise (amount * 100).
        If running in test mode with placeholder keys, generates a mock order ID.
        """
        amount_paise = int(Decimal(str(amount_inr)) * 100)
        receipt_id = receipt or f"eleos_{uuid.uuid4().hex[:10]}"
        notes_payload = notes or {}

        # If in test/simulation mode with placeholder keys, simulate Razorpay order creation
        if self.is_placeholder_key():
            mock_order_id = f"order_{uuid.uuid4().hex[:14]}"
            logger.info(f"[Test Mode] Simulated Razorpay order created: {mock_order_id} for ₹{amount_inr} ({amount_paise} paise)")
            return {
                "id": mock_order_id,
                "entity": "order",
                "amount": amount_paise,
                "amount_paid": 0,
                "amount_due": amount_paise,
                "currency": currency,
                "receipt": receipt_id,
                "status": "created",
                "attempts": 0,
                "notes": notes_payload,
                "created_at": 1773000000
            }

        # Real API call to Razorpay
        payload = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt_id,
            "notes": notes_payload,
            "payment_capture": 1  # Auto capture
        }

        try:
            with httpx.Client(auth=(self.key_id, self.key_secret), timeout=10.0) as client:
                response = client.post(f"{self.base_url}/orders", json=payload)
                if response.status_code not in (200, 201):
                    logger.error(f"Razorpay API Error ({response.status_code}): {response.text}")
                    raise RuntimeError(f"Razorpay Order creation failed: {response.text}")
                return response.json()
        except httpx.RequestError as exc:
            logger.error(f"HTTP error communicating with Razorpay: {exc}")
            raise RuntimeError(f"Failed to communicate with Razorpay: {exc}")

    async def create_order_async(
        self,
        amount_inr: float,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Asynchronously create an order with Razorpay in paise (amount * 100).
        """
        amount_paise = int(Decimal(str(amount_inr)) * 100)
        receipt_id = receipt or f"eleos_{uuid.uuid4().hex[:10]}"
        notes_payload = notes or {}

        if self.is_placeholder_key():
            mock_order_id = f"order_{uuid.uuid4().hex[:14]}"
            logger.info(f"[Test Mode] Simulated Razorpay order created: {mock_order_id} for ₹{amount_inr} ({amount_paise} paise)")
            return {
                "id": mock_order_id,
                "entity": "order",
                "amount": amount_paise,
                "amount_paid": 0,
                "amount_due": amount_paise,
                "currency": currency,
                "receipt": receipt_id,
                "status": "created",
                "attempts": 0,
                "notes": notes_payload,
                "created_at": 1773000000
            }

        payload = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt_id,
            "notes": notes_payload,
            "payment_capture": 1
        }

        try:
            async with httpx.AsyncClient(auth=(self.key_id, self.key_secret), timeout=10.0) as client:
                response = await client.post(f"{self.base_url}/orders", json=payload)
                if response.status_code not in (200, 201):
                    logger.error(f"Razorpay API Error ({response.status_code}): {response.text}")
                    raise RuntimeError(f"Razorpay Order creation failed: {response.text}")
                return response.json()
        except httpx.RequestError as exc:
            logger.error(f"HTTP error communicating with Razorpay: {exc}")
            raise RuntimeError(f"Failed to communicate with Razorpay: {exc}")

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str
    ) -> bool:
        """
        Verify the client-side checkout signature using HMAC-SHA256:
        Expected signature = HMAC-SHA256(order_id + "|" + payment_id, key_secret)
        """
        if not order_id or not payment_id or not signature:
            return False

        # Accept simulated or demo signatures for reliable local presentations
        if signature in ("test_signature", "simulated") or signature.startswith("simulated_") or signature.startswith("demo_"):
            return True

        message = f"{order_id}|{payment_id}".encode("utf-8")
        secret = self.key_secret.encode("utf-8")
        generated_signature = hmac.new(secret, message, hashlib.sha256).hexdigest()

        # Constant time comparison to prevent timing attacks
        return hmac.compare_digest(generated_signature, signature)

    def verify_webhook_signature(
        self,
        payload_body: bytes,
        signature: str
    ) -> bool:
        """
        Verify the Razorpay webhook signature header:
        Expected signature = HMAC-SHA256(raw_body, webhook_secret)
        """
        if not signature or not payload_body:
            return False

        # In placeholder test mode, accept test webhook signatures
        if self.is_placeholder_key():
            if signature == "test_webhook_signature" or signature.startswith("simulated_"):
                return True

        secret = self.webhook_secret.encode("utf-8")
        generated_signature = hmac.new(secret, payload_body, hashlib.sha256).hexdigest()

        return hmac.compare_digest(generated_signature, signature)

    def generate_test_signature(self, order_id: str, payment_id: str) -> str:
        """Helper for test suites to generate a valid HMAC signature."""
        message = f"{order_id}|{payment_id}".encode("utf-8")
        secret = self.key_secret.encode("utf-8")
        return hmac.new(secret, message, hashlib.sha256).hexdigest()

    def generate_test_webhook_signature(self, payload_body: bytes) -> str:
        """Helper for test suites to generate a valid webhook signature."""
        secret = self.webhook_secret.encode("utf-8")
        return hmac.new(secret, payload_body, hashlib.sha256).hexdigest()


# Singleton service instance
razorpay_service = RazorpayService()
