import os
import streamlit as st
from supabase import create_client, Client


def get_supabase() -> Client:
    if "_supabase" not in st.session_state:
        url = os.getenv("SUPABASE_URL", "").rstrip("/")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL ve SUPABASE_SERVICE_ROLE_KEY .env dosyasında tanımlı olmalı."
            )
        st.session_state["_supabase"] = create_client(url, key)
    return st.session_state["_supabase"]
