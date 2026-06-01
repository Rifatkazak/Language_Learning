import os
import streamlit as st


def _secret(key: str, fallback: str = "") -> str:
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key] or fallback
    except Exception:
        pass
    return os.getenv(key, fallback)


def is_configured() -> bool:
    return bool(_secret("STRIPE_SECRET_KEY") and _secret("STRIPE_PRICE_ID"))


def _stripe():
    """Return configured stripe module or None."""
    key = _secret("STRIPE_SECRET_KEY")
    if not key:
        return None
    try:
        import stripe as _s
        _s.api_key = key
        return _s
    except ImportError:
        return None


def create_checkout_session(username: str) -> tuple[str | None, str]:
    """Create a Stripe Checkout Session. Returns (url, error_message)."""
    s = _stripe()
    price_id = _secret("STRIPE_PRICE_ID")
    app_url = _secret("APP_URL", "http://localhost:8501").rstrip("/")
    if not s:
        return None, "Stripe yapılandırılmamış (STRIPE_SECRET_KEY eksik)."
    if not price_id:
        return None, "Stripe fiyat ID'si eksik (STRIPE_PRICE_ID)."
    try:
        session = s.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{app_url}?stripe_session={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{app_url}?stripe_cancel=1",
            client_reference_id=username,
            metadata={"username": username},
        )
        return session.url, ""
    except Exception as e:
        return None, str(e)


def validate_session(session_id: str) -> dict | None:
    """Validate a completed Stripe Checkout Session. Returns payment info."""
    s = _stripe()
    if not s or not session_id:
        return None
    try:
        session = s.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid" and session.status == "complete":
            return {
                "customer_id": session.customer,
                "subscription_id": session.subscription,
                "username": session.metadata.get("username", ""),
            }
    except Exception:
        pass
    return None


def check_subscription(subscription_id: str) -> bool:
    """Return True if a Stripe subscription is currently active."""
    s = _stripe()
    if not s or not subscription_id:
        return False
    try:
        sub = s.Subscription.retrieve(subscription_id)
        return sub.status in ("active", "trialing")
    except Exception:
        return False
