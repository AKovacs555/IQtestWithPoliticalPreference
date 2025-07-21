import os

# Stripe secret key used for server-side API calls.
# The older name ``STRIPE_API_KEY`` is still honoured for backwards
# compatibility but ``STRIPE_SECRET_KEY`` is preferred.
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY", "")
PAYPAY_API_KEY = os.getenv("PAYPAY_API_KEY", "")
LINEPAY_API_KEY = os.getenv("LINEPAY_API_KEY", "")


def select_processor(region: str) -> str:
    """Select the cheapest payment processor for a region."""
    if region == "JP" and PAYPAY_API_KEY:
        return "paypay"
    if region == "JP" and LINEPAY_API_KEY:
        return "linepay"
    return "stripe"
