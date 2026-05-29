import datetime
import streamlit as st
from core.session import ALL_PAGES, PAGE_HOME, PAGE_ADMIN
from core.auth import is_logged_in, logout, login, register, set_password_for_legacy
from core.i18n import t, page_label
from storage.user_store import load_users_file, save_users_file, load_user_data
from storage.word_repo import load_words


def render_auth_gate() -> None:
    # Language toggle on login page
    col_sp, col_lang, col_theme = st.columns([6, 1, 1])
    with col_lang:
        lang = st.session_state.get("ui_lang", "tr")
        if st.button("🇬🇧 EN" if lang == "tr" else "🇹🇷 TR", key="login_lang"):
            st.session_state.ui_lang = "en" if lang == "tr" else "tr"
            st.rerun()
    with col_theme:
        dark = st.session_state.get("dark_mode", False)
        if st.button("🌙" if not dark else "☀️", key="login_theme"):
            st.session_state.dark_mode = not dark
            st.rerun()

    st.markdown(f"# 🃏 {t('app_title')}")
    st.markdown(f"*{t('login_subtitle')}*")
    st.markdown("---")

    with st.form("login_form"):
        uname = st.text_input(t("username"))
        pwd = st.text_input(t("password"), type="password")
        submitted = st.form_submit_button(t("login_btn"), type="primary", use_container_width=True)

    if submitted:
        uname = uname.strip().lower()
        if not uname:
            st.error(t("username_empty"))
            return
        if not pwd:
            st.error(t("password_empty"))
            return

        users = load_users_file()

        if uname not in users:
            if pwd != "kazak":
                st.error(t("wrong_password"))
                return
            ok, msg = register(uname, pwd)
            if ok:
                st.session_state.page = PAGE_HOME
                st.rerun()
            else:
                st.error(msg)
            return

        if not users[uname].get("password_hash"):
            ok, msg = set_password_for_legacy(uname, pwd)
            if ok:
                st.session_state.page = PAGE_HOME
                st.rerun()
            else:
                st.error(msg)
            return

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
        st.markdown(f"## 🃏 {t('app_title')}")
        st.markdown(f"👤 **{st.session_state.get('current_user', '')}**")

        # Theme + language toggles
        c1, c2 = st.columns(2)
        with c1:
            dark = st.session_state.get("dark_mode", False)
            if st.button("☀️ Light" if dark else "🌙 Dark", use_container_width=True, key="sb_theme"):
                st.session_state.dark_mode = not dark
                st.rerun()
        with c2:
            lang = st.session_state.get("ui_lang", "tr")
            if st.button("🇬🇧 EN" if lang == "tr" else "🇹🇷 TR", use_container_width=True, key="sb_lang"):
                st.session_state.ui_lang = "en" if lang == "tr" else "tr"
                st.rerun()

        if st.button(t("logout_btn"), use_container_width=True):
            logout()
            st.rerun()
        st.markdown("---")

        from services.ai_service import get_ai_service
        ai = get_ai_service()
        if ai.is_available():
            st.sidebar.success(f"✅ {t('ai_active')}")
        else:
            st.sidebar.error(f"❌ {t('ai_inactive')}")

        st.markdown("---")
        st.markdown(f"### ⏰ {t('reminder')}")
        last_study = st.session_state.get("last_study_date")
        if last_study:
            last_date = datetime.date.fromisoformat(last_study)
            days_since = (datetime.date.today() - last_date).days
            if days_since == 0:
                st.success(f"✅ {t('studied_today')}")
            elif days_since == 1:
                st.warning(f"⚠️ {t('studied_yesterday')}")
            else:
                st.error(f"📅 {t('not_studied', n=days_since)}")

        if st.session_state.get("current_user") == "rifat":
            if st.button("⚙️ Admin", use_container_width=True, key="sidebar_admin"):
                st.session_state.page = PAGE_ADMIN
                st.rerun()

        st.markdown("---")
        for pg in ALL_PAGES:
            btn_type = "primary" if st.session_state.page == pg else "secondary"
            label = page_label(pg)
            if st.button(label, use_container_width=True, type=btn_type, key=f"sidebar_{pg}"):
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
        all_label = t("all")
        display_map = {
            "Tümü":    f"{all_label} ({total})",
            "Verb":    f"Verb ({counts_total['Verb']})",
            "Nomen":   f"Nomen ({counts_total['Nomen']})",
            "Adj/Adv": f"Adjective ({counts_total['Adj/Adv']})",
        }
        ft_keys = ["Tümü", "Verb", "Nomen", "Adj/Adv"]
        ft = st.selectbox(
            t("word_type"), ft_keys, label_visibility="collapsed",
            index=ft_keys.index(st.session_state.filter_type),
            format_func=lambda x: display_map.get(x, x),
        )
        if ft != st.session_state.filter_type:
            st.session_state.filter_type = ft
            st.rerun()

        st.markdown("---")
        seen = len(st.session_state.progress)
        pct = int(seen / total * 100) if total else 0
        st.markdown(f"**{t('progress')}: %{pct}**")
        st.progress(pct / 100)
        st.caption(t("words_progress", seen=seen, total=total))
        streak = st.session_state.daily_streak
        if streak > 0:
            st.markdown(f"🔥 **{t('streak', n=streak)}**")

        st.markdown("---")
        _render_leaderboard()



def _render_leaderboard() -> None:
    from services.gamification import get_level_info
    st.markdown(f"### 🏆 {t('leaderboard')}")

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
            st.caption(t("your_rank", rank=my_rank))


def render_bottom_nav() -> None:
    from core.session import (
        PAGE_HOME, PAGE_FLASH, PAGE_QUIZ, PAGE_GAMES,
        PAGE_CHALLENGE, PAGE_WORDLIST, PAGE_ADD, PAGE_STATS, PAGE_QUICK,
        PAGE_CONV, PAGE_ARTICLE,
    )
    pages = [
        ("🏠", PAGE_HOME), ("⚡", PAGE_QUICK), ("📇", PAGE_FLASH), ("📝", PAGE_QUIZ),
        ("🗣️", PAGE_CONV), ("🎯", PAGE_ARTICLE), ("🎮", PAGE_GAMES), ("🏆", PAGE_CHALLENGE),
        ("📖", PAGE_WORDLIST), ("➕", PAGE_ADD), ("📊", PAGE_STATS),
    ]
    cols = st.columns(len(pages))
    for col, (icon, page) in zip(cols, pages):
        with col:
            btn_type = "primary" if st.session_state.page == page else "secondary"
            if st.button(icon, use_container_width=True, type=btn_type, key=f"nav_{page}"):
                st.session_state.page = page
                st.rerun()
