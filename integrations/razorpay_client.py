import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")
BASE_URL = "https://api.razorpay.com/v1/payment_links"


def create_payment_link(amount_rupees, description, reference_id, diagnosed_category, rule_id):
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        return {"error": "Missing RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET - check your .env file."}

    payload = {
        "amount": int(round(amount_rupees * 100)),
        "currency": "INR",
        "description": description[:2048],
        "reference_id": reference_id[:40],
        "notify": {"sms": False, "email": False},
        "reminder_enable": False,
        "notes": {
            "diagnosed_category": diagnosed_category,
            "policy_rule_id": rule_id,
        },
    }

    try:
        response = requests.post(
            BASE_URL,
            auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
            json=payload,
            timeout=10,
        )
    except requests.exceptions.RequestException as e:
        return {"error": f"Network/request failure: {e}"}

    if response.status_code not in (200, 201):
        return {"error": f"HTTP {response.status_code}: {response.text}"}

    data = response.json()
    return {
        "razorpay_link_id": data.get("id"),
        "short_url": data.get("short_url"),
        "status": data.get("status"),
    }