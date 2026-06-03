import datetime
import streamlit as st
from core.session import ALL_PAGES, PAGE_HOME, PAGE_ADMIN
from core.auth import is_logged_in, logout, login, register, set_password_for_legacy
from core.i18n import t, page_label
from storage.user_store import load_users_file, save_users_file, load_user_data
from storage.word_repo import load_words


def render_auth_gate() -> None:
    col_sp, col_lang = st.columns([7, 1])
    with col_lang:
        lang = st.session_state.get("ui_lang", "tr")
        if st.button("🇬🇧 EN" if lang == "tr" else "🇹🇷 TR", key="login_lang"):
            st.session_state.ui_lang = "en" if lang == "tr" else "tr"
            st.rerun()

    st.markdown(f"# 🃏 {t('app_title')}")
    st.markdown(f"*{t('login_subtitle')}*")
    st.markdown("---")

    tab_login, tab_register = st.tabs([t("tab_login"), t("tab_register")])

    with tab_login:
        with st.form("login_form"):
            uname = st.text_input(t("username"), key="li_uname")
            pwd = st.text_input(t("password"), type="password", key="li_pwd")
            submitted = st.form_submit_button(t("login_btn"), type="primary", use_container_width=True)

        if submitted:
            uname = uname.strip().lower()
            if not uname:
                st.error(t("username_empty"))
            elif not pwd:
                st.error(t("password_empty"))
            else:
                users = load_users_file()
                if uname not in users:
                    st.error(t("user_not_found"))
                elif not users[uname].get("password_hash"):
                    ok, msg = set_password_for_legacy(uname, pwd)
                    if ok:
                        st.session_state.page = PAGE_HOME
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    ok, msg = login(uname, pwd)
                    if ok:
                        st.session_state.page = PAGE_HOME
                        st.rerun()
                    else:
                        st.error(msg)

    with tab_register:
        st.info(t("register_trial_info"))
        with st.form("register_form"):
            new_uname = st.text_input(t("username"), key="reg_uname")
            new_pwd = st.text_input(t("password"), type="password", key="reg_pwd")
            new_pwd2 = st.text_input(t("password_confirm"), type="password", key="reg_pwd2")
            reg_ok = st.form_submit_button(t("register_btn"), type="primary", use_container_width=True)

        if reg_ok:
            new_uname = new_uname.strip().lower()
            if not new_uname:
                st.error(t("username_empty"))
            elif not new_pwd:
                st.error(t("password_empty"))
            elif new_pwd != new_pwd2:
                st.error(t("passwords_no_match"))
            else:
                ok, msg = register(new_uname, new_pwd)
                if ok:
                    st.toast(t("register_success"), icon="🎉")
                    st.session_state.page = PAGE_HOME
                    st.rerun()
                else:
                    st.error(msg)


def render_sidebar(words: list, custom_words: list) -> None:
    with st.sidebar:
        st.markdown(f"## 🃏 {t('app_title')}")
        st.markdown(f"👤 **{st.session_state.get('current_user', '')}**")

        # Language toggle
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

        # Trial / subscription status
        user = st.session_state.get("current_user", "")
        if user and user != "rifat" and ai.is_available():
            ai_cache = st.session_state.get("ai_cache", {})
            if ai_cache.get("__subscription_active__"):
                st.success(f"✅ {t('subscription_active')}")
            else:
                days = ai.trial_days_remaining()
                if days > 0:
                    st.info(f"⏳ {t('trial_days_left', n=days)}")
                elif days == 0:
                    st.warning(f"⚠️ {t('trial_last_day')}")
                else:
                    st.error(f"🔒 {t('trial_expired')}")

                    # ── Stripe payment button ──────────────────────────────
                    from services.stripe_service import is_configured, create_checkout_session
                    if "_checkout_url" in st.session_state:
                        checkout_url = st.session_state["_checkout_url"]
                        st.markdown(
                            f'<a href="{checkout_url}" target="_top" style="display:block;'
                            f'text-align:center;background:#635BFF;color:#fff;padding:0.55rem 0;'
                            f'border-radius:8px;text-decoration:none;font-weight:600;'
                            f'margin:0.4rem 0">💳 {t("stripe_go_to_payment")}</a>',
                            unsafe_allow_html=True,
                        )
                        if st.button(t("btn_cancel"), key="sb_cancel_checkout", use_container_width=True):
                            st.session_state.pop("_checkout_url", None)
                            st.rerun()
                    elif is_configured():
                        if st.button(f"💳 {t('stripe_subscribe_btn')}", key="sb_subscribe",
                                     use_container_width=True, type="primary"):
                            with st.spinner(t("stripe_creating")):
                                url, err = create_checkout_session(user)
                            if url:
                                st.session_state["_checkout_url"] = url
                                st.rerun()
                            else:
                                st.error(f"{t('stripe_error')}: {err}")

                    # ── Promo code ─────────────────────────────────────────
                    with st.expander(t("promo_have_code")):
                        code = st.text_input(t("promo_code_label"), key="sb_promo_input")
                        if st.button(t("promo_apply_btn"), key="sb_promo_btn", use_container_width=True, type="primary"):
                            from services.subscription import apply_promo_code
                            ok, msg = apply_promo_code(code)
                            if ok:
                                st.rerun()
                            else:
                                st.error(msg)

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
        PAGE_CONV, PAGE_ARTICLE, PAGE_GRAMMAR, PAGE_EXAM,
    )
    pages = [
        ("🏠", PAGE_HOME), ("⚡", PAGE_QUICK), ("📇", PAGE_FLASH), ("📝", PAGE_QUIZ), ("📚", PAGE_GRAMMAR),
        ("🗣️", PAGE_CONV), ("🎯", PAGE_ARTICLE), ("📋", PAGE_EXAM), ("🎮", PAGE_GAMES), ("🏆", PAGE_CHALLENGE),
        ("📖", PAGE_WORDLIST), ("➕", PAGE_ADD), ("📊", PAGE_STATS),
    ]
    cols = st.columns(len(pages))
    for col, (icon, page) in zip(cols, pages):
        with col:
            btn_type = "primary" if st.session_state.page == page else "secondary"
            if st.button(icon, use_container_width=True, type=btn_type, key=f"nav_{page}"):
                st.session_state.page = page
                st.rerun()
