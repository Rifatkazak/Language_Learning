import datetime
import streamlit as st
from core.session import ALL_PAGES, PAGE_HOME
from core.auth import is_logged_in, logout, login, register, set_password_for_legacy
from storage.user_store import load_users_file, save_users_file, load_user_data
from storage.word_repo import load_words


_SHARED_PASSWORD = "kazak"


def render_auth_gate() -> None:
    """Giriş ekranı — kullanıcı adı + ortak şifre (kazak).
    Kullanıcı yoksa otomatik oluşturulur.
    # Yeni hesap oluşturma sekmesi şimdilik devre dışı.
    """
    st.markdown("# 🇩🇪 Goethe B1 Kelime Öğrenimi")
    st.markdown("---")

    with st.form("login_form"):
        uname = st.text_input("Kullanıcı adı")
        pwd = st.text_input("Şifre", type="password", placeholder="kazak")
        submitted = st.form_submit_button("Giriş Yap", type="primary", use_container_width=True)

    if submitted:
        uname = uname.strip()
        if not uname:
            st.error("Kullanıcı adı boş olamaz.")
            return

        users = load_users_file()

        # Kullanıcı yoksa otomatik oluştur
        if uname not in users:
            ok, msg = register(uname, pwd or _SHARED_PASSWORD)
            if ok:
                st.session_state.page = PAGE_HOME
                st.rerun()
            else:
                st.error(msg)
            return

        # Mevcut kullanıcı — legacy (şifresiz) ise şifreyi şimdi kaydet
        if not users[uname].get("password_hash"):
            ok, msg = set_password_for_legacy(uname, pwd or _SHARED_PASSWORD)
            if ok:
                st.session_state.page = PAGE_HOME
                st.rerun()
            else:
                st.error(msg)
            return

        # Normal giriş
        ok, msg = login(uname, pwd)
        if ok:
            st.session_state.page = PAGE_HOME
            st.rerun()
        else:
            st.error(msg)

    # ── Yeni hesap oluşturma (şimdilik devre dışı) ──────────────────────────
    # with st.expander("Yeni Hesap Oluştur"):
    #     with st.form("register_form"):
    #         new_uname = st.text_input("Kullanıcı adı")
    #         new_pwd   = st.text_input("Şifre (en az 4 karakter)", type="password")
    #         new_pwd2  = st.text_input("Şifre tekrar", type="password")
    #         reg_ok = st.form_submit_button("Hesap Oluştur", type="primary", use_container_width=True)
    #     if reg_ok:
    #         if new_pwd != new_pwd2:
    #             st.error("Şifreler eşleşmiyor.")
    #         else:
    #             ok, msg = register(new_uname, new_pwd)
    #             if ok:
    #                 st.success(msg)
    #                 st.session_state.page = PAGE_HOME
    #                 st.rerun()
    #             else:
    #                 st.error(msg)


def render_sidebar(words: list, custom_words: list) -> None:
    with st.sidebar:
        st.markdown("## 🇩🇪 Goethe B1")
        st.markdown(f"👤 **{st.session_state.get('current_user', '')}**")
        if st.button("Çıkış Yap", use_container_width=True):
            logout()
            st.rerun()
        st.markdown("---")

        # AI status
        from services.ai_service import get_ai_service
        ai = get_ai_service()
        if ai.is_available():
            st.sidebar.success("✅ AI Hizmeti Aktif")
        else:
            st.sidebar.error("❌ AI Pasif — DEEPSEEK_API_KEY eksik")

        st.markdown("---")
        st.markdown("### ⏰ Hatırlatıcı")
        last_study = st.session_state.get("last_study_date")
        if last_study:
            last_date = datetime.date.fromisoformat(last_study)
            days_since = (datetime.date.today() - last_date).days
            if days_since == 0:
                st.success("✅ Bugün çalıştın! Harika!")
            elif days_since == 1:
                st.warning("⚠️ Dün çalışmışsın. Seriyi bozma!")
            else:
                st.error(f"📅 {days_since} gündür çalışmamışsın!")

        st.markdown("---")
        for pg in ALL_PAGES:
            btn_type = "primary" if st.session_state.page == pg else "secondary"
            if st.button(pg, use_container_width=True, type=btn_type, key=f"sidebar_{pg}"):
                st.session_state.page = pg
                st.rerun()

        st.markdown("---")
        all_w = words + custom_words
        counts_total = {
            "Verb":    sum(1 for w in all_w if w.get("type") == "Verb"),
            "Nomen":   sum(1 for w in all_w if w.get("type") == "Nomen"),
            "Adj/Adv": sum(1 for w in all_w if w.get("type") == "Adj/Adv"),
        }
        total = len(all_w)
        display_map = {
            "Tümü":    f"Tümü ({total})",
            "Verb":    f"Verb ({counts_total['Verb']})",
            "Nomen":   f"Nomen ({counts_total['Nomen']})",
            "Adj/Adv": f"Adjective ({counts_total['Adj/Adv']})",
        }
        ft_keys = ["Tümü", "Verb", "Nomen", "Adj/Adv"]
        ft = st.selectbox(
            "Kelime türü", ft_keys, label_visibility="collapsed",
            index=ft_keys.index(st.session_state.filter_type),
            format_func=lambda x: display_map.get(x, x),
        )
        if ft != st.session_state.filter_type:
            st.session_state.filter_type = ft
            st.rerun()

        st.markdown("---")
        seen = len(st.session_state.progress)
        pct = int(seen / total * 100) if total else 0
        st.markdown(f"**İlerleme: %{pct}**")
        st.progress(pct / 100)
        st.caption(f"{seen} / {total} kelime")
        streak = st.session_state.daily_streak
        if streak > 0:
            st.markdown(f"🔥 **{streak} günlük seri!**")

        st.markdown("---")
        _render_leaderboard()



def _render_leaderboard() -> None:
    from services.gamification import get_level_info
    st.markdown("### 🏆 Liderlik Tablosu")

    users = st.session_state.get("users") or load_users_file()
    me = st.session_state.get("current_user", "")

    entries = []
    for uname, data in users.items():
        if not isinstance(data, dict):
            continue
        xp = data.get("total_xp", 0)
        streak = data.get("daily_streak", 0)
        learned = sum(1 for v in data.get("progress", {}).values() if v.get("status") == "easy")
        entries.append({"name": uname, "xp": xp, "streak": streak, "learned": learned})

    entries.sort(key=lambda e: e["xp"], reverse=True)

    medals = ["🥇", "🥈", "🥉"]
    for i, e in enumerate(entries[:10]):
        medal = medals[i] if i < 3 else f"{i+1}."
        level_info = get_level_info(e["xp"])
        is_me = e["name"] == me
        name_display = f"**{e['name']}**" if is_me else e["name"]
        bg = "rgba(74,144,217,0.15)" if is_me else "transparent"
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"padding:6px 8px;border-radius:8px;background:{bg};margin:2px 0;'>"
            f"<span>{medal} {name_display}</span>"
            f"<span style='font-size:0.8rem;opacity:0.75'>{level_info['level_title']}</span>"
            f"<span style='font-weight:700;color:#4a90d9'>{e['xp']} XP</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    if len(entries) > 10:
        my_rank = next((i + 1 for i, e in enumerate(entries) if e["name"] == me), None)
        if my_rank and my_rank > 10:
            st.caption(f"Senin sıran: #{my_rank}")


def render_bottom_nav() -> None:
    from core.session import (
        PAGE_HOME, PAGE_FLASH, PAGE_QUIZ, PAGE_GAMES,
        PAGE_CHALLENGE, PAGE_WORDLIST, PAGE_ADD, PAGE_STATS, PAGE_QUICK,
    )
    pages = [
        ("🏠", PAGE_HOME), ("⚡", PAGE_QUICK), ("📇", PAGE_FLASH), ("📝", PAGE_QUIZ),
        ("🎮", PAGE_GAMES), ("🏆", PAGE_CHALLENGE), ("📖", PAGE_WORDLIST),
        ("➕", PAGE_ADD), ("📊", PAGE_STATS),
    ]
    cols = st.columns(len(pages))
    for col, (icon, page) in zip(cols, pages):
        with col:
            btn_type = "primary" if st.session_state.page == page else "secondary"
            if st.button(icon, use_container_width=True, type=btn_type, key=f"nav_{page}"):
                st.session_state.page = page
                st.rerun()
