import datetime
import os
import streamlit as st
from storage.supabase_client import get_supabase
from services.subscription import grant_subscription, revoke_subscription, get_valid_codes

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "rifat")
TRIAL_DAYS = 3


def _sub_status(ai_cache: dict, created_at: str) -> tuple[str, str]:
    """Returns (emoji_label, sort_key) for subscription status."""
    if ai_cache.get("__subscription_active__"):
        source = "admin" if ai_cache.get("__granted_by_admin__") else f"kod: {ai_cache.get('__promo_used__','?')}"
        return f"✅ Premium ({source})", "0"
    trial_start = ai_cache.get("__trial_start__") or created_at or ""
    if not trial_start:
        return "❓ Bilinmiyor", "9"
    try:
        start = datetime.date.fromisoformat(str(trial_start)[:10])
        days_used = (datetime.date.today() - start).days
        remaining = TRIAL_DAYS - 1 - days_used
        if remaining >= 0:
            return f"⏳ Trial ({remaining+1} gün kaldı)", "1"
        return f"🔒 Süresi doldu ({abs(remaining+1)} gün önce)", "2"
    except Exception:
        return "❓ Bilinmiyor", "9"


def render(*_):
    if st.session_state.get("current_user") != ADMIN_USERNAME:
        st.error("Erişim reddedildi.")
        return

    st.title("⚙️ Admin Paneli")

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

    # ── Özet metrikler ──────────────────────────────────────────────────────
    premium = sum(1 for r in rows if (r.get("ai_cache") or {}).get("__subscription_active__"))
    trial_active = 0
    trial_expired = 0
    for r in rows:
        if r.get("username") == ADMIN_USERNAME:
            continue
        ac = r.get("ai_cache") or {}
        if ac.get("__subscription_active__"):
            continue
        trial_start = ac.get("__trial_start__") or r.get("created_at") or ""
        try:
            start = datetime.date.fromisoformat(str(trial_start)[:10])
            days_used = (datetime.date.today() - start).days
            if days_used < TRIAL_DAYS:
                trial_active += 1
            else:
                trial_expired += 1
        except Exception:
            pass

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👤 Toplam Kullanıcı", len(rows))
    c2.metric("✅ Premium", premium)
    c3.metric("⏳ Trial", trial_active)
    c4.metric("🔒 Süresi Dolmuş", trial_expired)

    st.divider()

    # ── Kullanıcı tablosu ───────────────────────────────────────────────────
    st.subheader("Kullanıcılar")
    table = []
    for r in rows:
        ac = r.get("ai_cache") or {}
        ai_count = sum(1 for k in ac if not k.startswith("__"))
        cw_count = len(r.get("custom_words") or [])
        status, sort_key = _sub_status(ac, r.get("created_at", ""))
        table.append({
            "Kullanıcı": r.get("username", ""),
            "Kayıt": (r.get("created_at") or "")[:10],
            "Son Giriş": r.get("last_study_date") or "-",
            "Streak": r.get("daily_streak", 0),
            "XP": r.get("total_xp", 0),
            "AI Önbellek": ai_count,
            "Özel Kelime": cw_count,
            "Üyelik": status,
            "_sort": sort_key,
        })

    table.sort(key=lambda x: (x["_sort"], -x["XP"]))
    for row in table:
        row.pop("_sort")

    st.dataframe(table, use_container_width=True)

    st.divider()

    # ── Üyelik Yönetimi ─────────────────────────────────────────────────────
    st.subheader("Üyelik Yönetimi")

    non_admin = [r["username"] for r in rows if r["username"] != ADMIN_USERNAME]
    if not non_admin:
        st.info("Yönetilecek kullanıcı yok.")
    else:
        target = st.selectbox("Kullanıcı seç", non_admin, key="admin_sub_target")
        target_row = next((r for r in rows if r["username"] == target), {})
        target_ac = target_row.get("ai_cache") or {}
        status_label, _ = _sub_status(target_ac, target_row.get("created_at", ""))
        st.markdown(f"**Mevcut durum:** {status_label}")

        col_g, col_r = st.columns(2)
        with col_g:
            if st.button("✅ Premium Ver", key="admin_grant", use_container_width=True, type="primary",
                         disabled=bool(target_ac.get("__subscription_active__"))):
                if grant_subscription(target):
                    st.success(f"{target} için premium aktif edildi.")
                    st.rerun()
                else:
                    st.error("Hata oluştu.")
        with col_r:
            if st.button("🔒 Premium Al", key="admin_revoke", use_container_width=True,
                         disabled=not bool(target_ac.get("__subscription_active__"))):
                st.session_state["_revoke_confirm"] = target

        if st.session_state.get("_revoke_confirm") == target:
            st.warning(f"**{target}** kullanıcısının premium'u kaldırılacak. Emin misin?")
            cy, cn = st.columns(2)
            with cy:
                if st.button("Evet, kaldır", key="admin_revoke_yes"):
                    if revoke_subscription(target):
                        st.success(f"{target} premium'u kaldırıldı.")
                        st.session_state.pop("_revoke_confirm", None)
                        st.rerun()
                    else:
                        st.error("Hata oluştu.")
            with cn:
                if st.button("İptal", key="admin_revoke_no"):
                    st.session_state.pop("_revoke_confirm", None)
                    st.rerun()

    st.divider()

    # ── Promo Kodları ───────────────────────────────────────────────────────
    st.subheader("Promo Kodları")
    codes = get_valid_codes()
    if codes:
        st.success(f"Aktif kodlar: **{', '.join(codes)}**")
        used = [
            {"Kullanıcı": r["username"], "Kod": (r.get("ai_cache") or {}).get("__promo_used__", "")}
            for r in rows
            if (r.get("ai_cache") or {}).get("__promo_used__")
        ]
        if used:
            st.caption("Kodu kullananlar:")
            st.dataframe(used, use_container_width=True)
        else:
            st.caption("Henüz kimse promo kod kullanmadı.")
    else:
        st.warning("Promo kod tanımlanmamış. `.env` veya Streamlit secrets'a `PROMO_CODES=KOD1,KOD2` ekle.")

    st.divider()

    # ── Kullanıcı Sil ───────────────────────────────────────────────────────
    st.subheader("Kullanıcı Sil")
    deletable = [r["username"] for r in rows if r["username"] != ADMIN_USERNAME]
    if not deletable:
        st.info("Silinecek kullanıcı yok.")
        return

    del_target = st.selectbox("Kullanıcı seç", deletable, key="admin_del_target")
    if st.button("🗑️ Sil", type="primary", key="admin_del_btn"):
        st.session_state["_delete_confirm"] = del_target

    if st.session_state.get("_delete_confirm") == del_target:
        st.warning(f"**{del_target}** silinecek. Emin misin?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Evet, sil", key="confirm_delete"):
                try:
                    sb = get_supabase()
                    sb.table("users").delete().eq("username", del_target).execute()
                    st.success(f"{del_target} silindi.")
                    st.session_state.pop("_delete_confirm", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Hata: {e}")
        with col2:
            if st.button("İptal", key="cancel_delete"):
                st.session_state.pop("_delete_confirm", None)
                st.rerun()
