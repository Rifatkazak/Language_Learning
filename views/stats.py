import datetime
import streamlit as st
from models.word import get_translation, get_display
from services.progress import get_due_words
from services.ai_service import get_ai_service
from services.game_engine import start_flash
from storage.user_store import persist_current_user
from ui.components import render_weak_analysis
from core.session import PAGE_FLASH
from core.i18n import t


def render(words: list, custom_words: list) -> None:
    st.markdown(t("stats_title"))

    p = st.session_state.progress
    total = len(words) + len(custom_words)
    seen = len(p)
    hard = sum(1 for v in p.values() if v.get("status") == "hard")
    ok = sum(1 for v in p.values() if v.get("status") == "ok")
    easy = sum(1 for v in p.values() if v.get("status") == "easy")
    unseen = total - seen
    due = len(get_due_words(words, custom_words))

    st.markdown(t("stats_overview"))
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(t("metric_total"), total)
    c2.metric(t("metric_learned"), easy)
    c3.metric(t("metric_in_progress"), ok)
    c4.metric(t("metric_hard_stat"), hard)
    c5.metric(t("metric_due_today"), due)

    streak = st.session_state.daily_streak
    if streak > 0:
        st.markdown(t("stats_streak", n=streak))

    st.markdown("---")
    st.markdown(t("stats_dist_chart"))
    chart_data = {
        t("chart_learned"):     easy,
        t("chart_in_progress"): ok,
        t("chart_hard"):        hard,
        t("chart_unseen"):      unseen,
    }
    if any(v > 0 for v in chart_data.values()):
        st.bar_chart(chart_data)

    st.markdown("---")
    st.markdown(t("stats_by_type"))
    type_stats: dict = {}
    for w in words + custom_words:
        wt = w["type"]
        pi = p.get(w["word"], {})
        sv = pi.get("status", "unseen")
        if wt not in type_stats:
            type_stats[wt] = {"total": 0, "easy": 0, "ok": 0, "hard": 0, "unseen": 0}
        type_stats[wt]["total"] += 1
        type_stats[wt][sv] += 1
    for wt, stats in type_stats.items():
        pct2 = int(stats["easy"] / stats["total"] * 100) if stats["total"] else 0
        st.markdown(t("stats_type_row", t=wt, n=stats["total"], pct=pct2))
        st.progress(pct2 / 100)

    st.markdown("---")
    st.markdown(t("stats_hardest"))
    hard_words = [(word, info) for word, info in p.items() if info.get("status") == "hard"]
    hard_words.sort(key=lambda x: x[1].get("count", 0), reverse=True)
    if hard_words:
        for word, info in hard_words[:15]:
            wobj = next((w for w in words + custom_words if w["word"] == word), None)
            if wobj:
                col1, col2, col3 = st.columns([2, 2, 1])
                col1.write(f"**{get_display(wobj)}**")
                col2.write(get_translation(word, words, custom_words))
                col3.write(f"❌ {info.get('count', 0)}×")
    else:
        st.info(t("stats_no_hard"))

    st.markdown("---")
    render_weak_analysis(words, custom_words)

    st.markdown("---")
    st.markdown(t("stats_ai_section"))
    hard_words_list = [word for word, info in p.items() if info.get("status") == "hard"]
    if st.button(t("btn_ai_analyze"), use_container_width=True):
        with st.spinner(t("spinner_ai_analysis")):
            ai = get_ai_service()
            user_stats = {
                "total_xp": st.session_state.get("total_xp", 0),
                "streak": st.session_state.get("daily_streak", 0),
                "total_words": len(p),
            }
            analysis = ai.analyze_weak_words(hard_words_list, user_stats)
            st.info(f"💡 {analysis}")

    st.markdown("---")
    st.markdown(t("stats_quick_actions"))
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("btn_study_hard"), use_container_width=True, type="primary"):
            hard_list = [
                next((w for w in words + custom_words if w["word"] == word), None)
                for word, info in p.items() if info.get("status") == "hard"
            ]
            hard_list = [w for w in hard_list if w]
            if hard_list:
                import random; random.shuffle(hard_list)
                st.session_state.flash_deck = hard_list[:25]
                st.session_state.flash_idx = 0
                st.session_state.flash_flipped = False
                st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
                st.session_state.page = PAGE_FLASH
                st.rerun()
            else:
                st.warning(t("stats_no_hard_warning"))
    with col2:
        if st.button(t("btn_reset_progress"), use_container_width=True):
            if st.checkbox(t("stats_reset_confirm")):
                st.session_state.progress = {}
                st.session_state.daily_streak = 0
                persist_current_user()
                st.rerun()

    st.markdown("---")
    st.markdown(t("stats_learning_speed"))
    last_7 = []
    for i in range(6, -1, -1):
        day_str = str(datetime.date.today() - datetime.timedelta(days=i))
        last_7.append(sum(1 for v in p.values() if v.get("last_seen") == day_str))
    st.bar_chart({t("chart_studied_words"): last_7})
    st.caption(t("stats_last7_caption"))

    if seen > 0 and easy > 0:
        start_date = st.session_state.get("start_date", datetime.date.today())
        if isinstance(start_date, str):
            try:
                start_date = datetime.date.fromisoformat(start_date)
            except Exception:
                start_date = datetime.date.today()
        days_elapsed = max(1, (datetime.date.today() - start_date).days)
        wpd = easy / days_elapsed
        remaining = total - easy
        days_left = int(remaining / max(wpd, 1))
        st.info(t("stats_eta", n=days_left))
