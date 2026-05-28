import os
import streamlit as st
from supabase import create_client, Client


def _get_secret(key: str) -> str:
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, "")


def get_supabase() -> Client:
    if "_supabase" not in st.session_state:
        url = _get_secret("SUPABASE_URL").rstrip("/")
        key = _get_secret("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL ve SUPABASE_SERVICE_ROLE_KEY tanimli olmali."
            )
        st.session_state["_supabase"] = create_client(url, key)
    return st.session_state["_supabase"]
