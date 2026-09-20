# Eleos Razorpay Payment Module

The **Razorpay Payment Module** is dedicated strictly to fiat payment processing (UPI, Debit/Credit Cards, Netbanking):
1. **Razorpay Order Creation & Checkout Setup**
2. **Client-side Signature Verification** (HMAC-SHA256 for instant UI confirmation)
3. **Server-to-Server Webhook Processing** (HMAC-SHA256 signature validation & idempotency checks)
4. **Database State Management** (Creating initiated records, updating campaign raised totals)
5. **Real-time Payment Confirmation WebSocket Notifications** (via Redis Pub/Sub)

*(Note: Blockchain recording and smart contract verification will be handled separately in the dedicated blockchain module).*

---

## 📁 Package Architecture

```
razorpay/
├── __init__.py                # Package exports
├── config.py                  # Razorpay API keys, webhook secret, and settings
├── main.py                    # Standalone FastAPI payment service runner (Port 8001)
├── routers/
│   ├── __init__.py
│   └── donations.py           # FastAPI endpoints (/initiate, /verify, /webhook, etc.)
├── schemas/
│   ├── __init__.py
│   └── donation.py            # Pydantic schemas (DonationInitiate, Verify, Webhook, etc.)
├── services/
│   ├── __init__.py
│   ├── razorpay_service.py    # Order creation, HMAC signatures, refunds
│   ├── donation_service.py    # Donation lifecycle, DB ops, campaign amount updates, idempotency
│   └── redis_service.py       # WebSocket broadcasting (payment confirmation events)
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest test client and mock fixtures
│   └── test_razorpay.py       # Comprehensive unit & integration tests
└── README.md                  # Documentation
```

---

## 🔗 Shared Repository Imports

This module imports directly from the existing repository modules without duplication:
- **`from database.models import Donation, Campaign, User`**
- **`from database.connection import get_db, SessionLocal`**

---

## 📡 API Endpoints

### 1. Initiate Donation (`POST /api/donations/initiate` or `POST /api/donate`)
Creates a Razorpay Order and registers an `initiated` donation record in PostgreSQL.
```json
// Request
{
  "campaign_id": "10000000-0000-0000-0000-000000000001",
  "amount": 500.00,
  "donor_id": "77777777-7777-7777-7777-777777777777",
  "payment_method": "upi",
  "donor_message": "For flood relief",
  "is_anonymous": false
}

// Response (201 Created)
{
  "donation_id": "90000000-0000-0000-0000-000000000001",
  "order_id": "order_Qz981029481203",
  "amount": 500.0,
  "amount_paise": 50000,
  "currency": "INR",
  "key_id": "rzp_test_placeholder",
  "status": "initiated"
}
```

### 2. Client Payment Verification (`POST /api/donations/verify`)
Called immediately when the Razorpay checkout completes in the frontend:
```json
// Request
{
  "razorpay_order_id": "order_Qz981029481203",
  "razorpay_payment_id": "pay_Qz981029481203",
  "razorpay_signature": "5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f"
}

// Response (200 OK)
{
  "verified": true,
  "donation_id": "90000000-0000-0000-0000-000000000001",
  "status": "completed",
  "payment_id": "pay_Qz981029481203",
  "message": "Payment successfully verified and confirmed on Eleos."
}
```

### 3. Server Webhook (`POST /api/donations/webhook` or `POST /api/webhooks/razorpay`)
Receives raw webhooks from Razorpay with header `X-Razorpay-Signature`:
- Handles `payment.captured`
- Handles `payment.failed`
- Idempotency check ensures duplicate webhooks are safely ignored without double-counting raised amounts.

---

## 🧪 Running Tests

To run the unit and integration tests:
```powershell
python -m pytest razorpay/tests/test_razorpay.py -v
```

---

## ⚡ Running Standalone

To run the payment module as a microservice on port 8001:
```powershell
python -m uvicorn razorpay.main:app --port 8001 --reload
```
Interactive Swagger docs available at: `http://localhost:8001/docs`
