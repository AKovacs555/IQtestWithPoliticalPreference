import os

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
PAYPAY_API_KEY = os.getenv("PAYPAY_API_KEY", "")
LINEPAY_API_KEY = os.getenv("LINEPAY_API_KEY", "")


def select_processor(region: str) -> str:
    """Select the cheapest payment processor for a region."""
    if region == "JP" and PAYPAY_API_KEY:
        return "paypay"
    if region == "JP" and LINEPAY_API_KEY:
        return "linepay"
    return "stripe"
