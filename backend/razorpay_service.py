import os
import requests
import hmac
import hashlib


RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

BASE_URL = "https://api.razorpay.com/v1"


def create_order(amount):

    data = {
        "amount": int(amount * 100),
        "currency": "INR",
        "receipt": "shopboost_demo",
        "notes": {
            "source": "ShopBoost AI",
            "track": "AI Growth & Agentic Commerce"
        }
    }

    response = requests.post(
        f"{BASE_URL}/orders",
        auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
        json=data
    )

    response.raise_for_status()

    return response.json()


def verify_payment(
    razorpay_order_id,
    razorpay_payment_id,
    razorpay_signature
):

    message = (
        razorpay_order_id
        + "|"
        + razorpay_payment_id
    )

    generated_signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        generated_signature,
        razorpay_signature
    )