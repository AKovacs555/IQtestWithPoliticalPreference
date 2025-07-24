import os
import random
import logging

SMS_PROVIDER = os.getenv("SMS_PROVIDER", "twilio")
TWILIO_VERIFY_SID = ""

if SMS_PROVIDER == "twilio":
    try:
        from twilio.rest import Client as TwilioClient
    except Exception:  # pragma: no cover - optional dependency
        TwilioClient = None
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_VERIFY_SID = os.environ.get("TWILIO_VERIFY_SERVICE_SID", "")
    sms_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TwilioClient else None
    COST_PER_SMS = 0.0075
elif SMS_PROVIDER == "sns":
    try:
        import boto3
    except Exception:  # pragma: no cover - optional dependency
        boto3 = None
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
    sms_client = boto3.client("sns", region_name=AWS_REGION) if boto3 else None
    COST_PER_SMS = 0.00645
else:
    sms_client = None
    COST_PER_SMS = 0.0

logger = logging.getLogger(__name__)

__all__ = ["send_otp", "SMS_PROVIDER", "TWILIO_VERIFY_SID"]


def send_otp(phone: str, code: str) -> None:
    """Send an OTP via the configured provider and log estimated cost."""
    if SMS_PROVIDER == "twilio":
        sms_client.verify.v2.services(TWILIO_VERIFY_SID).verifications.create(
            to=phone, channel="sms"
        )
    elif SMS_PROVIDER == "sns":
        sms_client.publish(PhoneNumber=phone, Message=f"Your code is {code}")
    logger.info("Sent OTP via %s costing approx $%.4f", SMS_PROVIDER, COST_PER_SMS)
