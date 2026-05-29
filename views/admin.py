import os
import streamlit as st
from storage.supabase_client import get_supabase

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "rifat")


def render(*_):
    if st.session_state.get("current_user") != ADMIN_USERNAME:
        st.error("Erişim reddedildi.")
        return

    st.title("Admin Paneli")

    try:
        sb = get_supabase()
        resp = sb.table("users").select(
            "username, created_at, last_study_date, daily_streak, "
            "total_xp, total_study_minutes, ai_cache, custom_words, "
            "is_premium"
        ).execute()
        rows = resp.data or []
    except Exception as e:
        st.error(f"Supabase hatası: {e}")
        return

    total = len(rows)
    premium = sum(1 for r in rows if r.get("is_premium"))
    free = total - premium
    total_ai = sum(len(r.get("ai_cache") or {}) for r in rows)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Kullanıcı", total)
    c2.metric("Free", free)
    c3.metric("Premium", premium)
    c4.metric("Toplam AI İstek", total_ai)

    st.divider()

    table = []
    for r in rows:
        ai_count = len(r.get("ai_cache") or {})
        cw_count = len(r.get("custom_words") or [])
        table.append({
            "Kullanıcı": r.get("username", ""),
            "Kayıt": (r.get("created_at") or "")[:10],
            "Son Giriş": r.get("last_study_date") or "-",
            "Streak": r.get("daily_streak", 0),
            "XP": r.get("total_xp", 0),
            "Dakika": r.get("total_study_minutes", 0),
            "AI İstek": ai_count,
            "Özel Kelime": cw_count,
            "Premium": "✅" if r.get("is_premium") else "❌",
        })

    table.sort(key=lambda x: x["XP"], reverse=True)
    st.dataframe(table, use_container_width=True)
