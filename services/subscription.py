import os
import streamlit as st
from storage.user_store import persist_current_user


def get_valid_codes() -> list[str]:
    """Load valid promo codes from secrets or env (comma-separated)."""
    try:
        raw = st.secrets.get("PROMO_CODES", "")
        if raw:
            return [c.strip().upper() for c in raw.split(",") if c.strip()]
    except Exception:
        pass
    raw = os.getenv("PROMO_CODES", "")
    if raw:
        return [c.strip().upper() for c in raw.split(",") if c.strip()]
    return []


def apply_promo_code(code: str) -> tuple[bool, str]:
    """Apply a promo code for the current user. Returns (ok, message)."""
    valid = get_valid_codes()
    if not valid:
        return False, "Sistem henüz aktif değil."

    if code.strip().upper() not in valid:
        return False, "Geçersiz kod."

    ai_cache = st.session_state.get("ai_cache", {})
    if ai_cache.get("__subscription_active__"):
        return False, "Zaten aktif AI üyeliğin var."

    ai_cache["__subscription_active__"] = True
    ai_cache["__promo_used__"] = code.strip().upper()
    st.session_state.ai_cache = ai_cache
    persist_current_user()
    return True, "Kod geçerli! AI üyeliğin aktif edildi. 🎉"


def grant_subscription(username: str) -> bool:
    """Admin: activate AI subscription for a user."""
    try:
        from storage.supabase_client import get_supabase
        sb = get_supabase()
        resp = sb.table("users").select("ai_cache").eq("username", username).single().execute()
        ai_cache = dict(resp.data.get("ai_cache") or {})
        ai_cache["__subscription_active__"] = True
        ai_cache["__granted_by_admin__"] = True
        sb.table("users").update({"ai_cache": ai_cache}).eq("username", username).execute()
        return True
    except Exception:
        return False


def activate_stripe_subscription(info: dict) -> None:
    """After successful Stripe checkout, activate subscription for current user."""
    ai_cache = st.session_state.get("ai_cache", {})
    ai_cache["__subscription_active__"] = True
    ai_cache["__stripe_customer_id__"] = info.get("customer_id", "")
    ai_cache["__stripe_subscription_id__"] = info.get("subscription_id", "")
    st.session_state.ai_cache = ai_cache
    persist_current_user()


def activate_stripe_subscription_for_user(info: dict) -> bool:
    """Activate subscription directly in Supabase (works even when user is not logged in)."""
    username = info.get("username", "")
    if not username:
        return False
    # If this is the current logged-in user, also update session state
    if st.session_state.get("current_user") == username:
        activate_stripe_subscription(info)
        return True
    try:
        from storage.supabase_client import get_supabase
        sb = get_supabase()
        resp = sb.table("users").select("ai_cache").eq("username", username).single().execute()
        ai_cache = dict(resp.data.get("ai_cache") or {})
        ai_cache["__subscription_active__"] = True
        ai_cache["__stripe_customer_id__"] = info.get("customer_id", "")
        ai_cache["__stripe_subscription_id__"] = info.get("subscription_id", "")
        sb.table("users").update({"ai_cache": ai_cache}).eq("username", username).execute()
        return True
    except Exception:
        return False


def revoke_subscription(username: str) -> bool:
    """Admin: remove AI subscription from a user."""
    try:
        from storage.supabase_client import get_supabase
        sb = get_supabase()
        resp = sb.table("users").select("ai_cache").eq("username", username).single().execute()
        ai_cache = dict(resp.data.get("ai_cache") or {})
        ai_cache["__subscription_active__"] = False
        ai_cache.pop("__granted_by_admin__", None)
        ai_cache.pop("__promo_used__", None)
        sb.table("users").update({"ai_cache": ai_cache}).eq("username", username).execute()
        return True
    except Exception:
        return False
