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
            "total_xp, total_study_minutes, ai_cache, custom_words"
        ).execute()
        rows = resp.data or []
    except Exception as e:
        st.error(f"Supabase hatası: {e}")
        return

    total = len(rows)
    total_ai = sum(len(r.get("ai_cache") or {}) for r in rows)

    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Kullanıcı", total)
    c2.metric("Toplam AI İstek", total_ai)
    c3.metric("Premium", "—")

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
            "Premium": "—",
        })

    table.sort(key=lambda x: x["XP"], reverse=True)
    st.dataframe(table, use_container_width=True)

    st.divider()
    st.subheader("Kullanıcı Sil")

    deletable = [r["username"] for r in rows if r["username"] != ADMIN_USERNAME]
    if not deletable:
        st.info("Silinecek kullanıcı yok.")
        return

    target = st.selectbox("Kullanıcı seç", deletable)
    if st.button("🗑️ Sil", type="primary"):
        st.session_state["_delete_confirm"] = target

    if st.session_state.get("_delete_confirm") == target:
        st.warning(f"**{target}** silinecek. Emin misin?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Evet, sil", key="confirm_delete"):
                try:
                    sb = get_supabase()
                    sb.table("users").delete().eq("username", target).execute()
                    st.success(f"{target} silindi.")
                    st.session_state.pop("_delete_confirm", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Hata: {e}")
        with col2:
            if st.button("İptal", key="cancel_delete"):
                st.session_state.pop("_delete_confirm", None)
                st.rerun()
