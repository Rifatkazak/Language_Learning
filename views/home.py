import datetime
import streamlit as st
from models.word import get_translation, get_display
from services.progress import get_due_words
from services.game_engine import start_flash, start_quiz
from ui.components import render_streak_widget, render_xp_bar, render_daily_tasks
from core.session import PAGE_FLASH, PAGE_QUIZ
from core.i18n import t


def render(words: list, custom_words: list) -> None:
    st.markdown(t("home_title"))
    st.markdown(t("home_welcome"))

    p = st.session_state.progress
    total = len(words) + len(custom_words)
    seen = len(p)
    hard = sum(1 for v in p.values() if v.get("status") == "hard")
    easy = sum(1 for v in p.values() if v.get("status") == "easy")
    due_today = len(get_due_words(words, custom_words))

    if due_today > 0:
        st.markdown(
            f"<div style='padding:1.1rem 1.4rem;margin:0.6rem 0 1rem 0;"
            f"background:linear-gradient(135deg,#fef3c7,#fde68a);"
            f"border-left:5px solid #f59e0b;border-radius:12px;"
            f"box-shadow:0 2px 8px rgba(245,158,11,0.15);'>"
            f"<div style='font-size:1.3rem;font-weight:700;color:#92400e'>"
            f"⏰ {t('home_due_banner', due_today=due_today)}</div>"
            f"<div style='font-size:0.85rem;color:#78350f;margin-top:0.2rem'>"
            f"{t('home_due_sub')}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if st.button(t("home_review_now"), type="primary", use_container_width=True, key="home_due_cta"):
            start_flash(words, custom_words)
            st.session_state.page = PAGE_FLASH
            st.rerun()
        st.markdown("---")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(t("metric_total"), total)
    c2.metric(t("metric_seen"), seen)
    c3.metric(t("metric_due_today"), due_today)
    c4.metric(t("metric_hard"), hard)
    c5.metric(t("metric_learned"), easy)

    st.markdown("---")
    pct = int(seen / total * 100) if total else 0
    st.markdown(f"#### {t('home_progress_pct', pct=pct)}")
    st.progress(pct / 100)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        render_streak_widget()
    with col2:
        render_xp_bar()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(t("home_fc_section"))
        st.markdown(t("home_fc_sub", due_today=due_today))
        if st.button(t("start_flashcard"), use_container_width=True, type="primary"):
            start_flash(words, custom_words)
            st.session_state.page = PAGE_FLASH
            st.rerun()
    with col2:
        st.markdown(t("home_quiz_section"))
        st.markdown(t("home_quiz_sub"))
        if st.button(t("start_quiz"), use_container_width=True, type="primary"):
            start_quiz(words, custom_words)
            st.session_state.page = PAGE_QUIZ
            st.rerun()

    st.markdown("---")
    render_daily_tasks()

    st.markdown("---")
    day_idx = datetime.date.today().toordinal() % total if total > 0 else 0
    all_w = words + custom_words
    if all_w:
        day_word = all_w[day_idx]
        st.markdown(t("word_of_day"))
        col1, col2 = st.columns([1, 2])
        with col1:
            art_color = {"der": "🔵", "die": "🔴", "das": "🟢", "": "⚪"}
            ic = art_color.get(day_word.get("article", ""), "⚪")
            st.markdown(f"## {ic} {get_display(day_word)}")
            st.markdown(f"*{day_word['type']}*")
        with col2:
            st.markdown(f"### {get_translation(day_word['word'], words, custom_words)}")
            p_info = st.session_state.progress.get(day_word["word"], {})
            if p_info:
                status_icons = {
                    "easy": t("status_easy"),
                    "ok": t("status_ok"),
                    "hard": t("status_hard_label"),
                }
                st.caption(status_icons.get(p_info.get("status", ""), ""))
