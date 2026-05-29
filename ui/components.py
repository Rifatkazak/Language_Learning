import datetime
import streamlit as st
from services.gamification import (
    get_level_info, generate_daily_tasks, ACHIEVEMENTS,
)
from services.analytics import analyze_weak_patterns
from core.i18n import t


def render_streak_widget() -> None:
    streak = st.session_state.get("daily_streak", 0)
    if streak == 0:
        st.info(t("streak_start_today"))
        return

    fire_map = {range(1, 4): "🌱", range(4, 8): "🔥", range(8, 15): "🔥🔥",
                range(15, 31): "⚡🔥", range(31, 101): "🏆🔥"}
    fire = "🔥"
    for r, emoji in fire_map.items():
        if streak in r:
            fire = emoji
            break

    st.markdown(f"### {fire} {t('streak_title', n=streak)}")
    today = datetime.date.today()
    day_names = t("day_names_tr").split(",")
    days_html = ""
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        day_str = str(day)
        day_name = day_names[day.weekday()]
        studied = any(v.get("last_seen") == day_str for v in st.session_state.progress.values())
        color = "#27ae60" if studied else ("#f39c12" if i == 0 else "#e0e0e0")
        emoji = "✅" if studied else ("👆" if i == 0 else "○")
        days_html += (
            f'<div style="text-align:center;padding:4px;">'
            f'<div style="width:32px;height:32px;border-radius:50%;background:{color};'
            f'display:flex;align-items:center;justify-content:center;font-size:0.7rem;'
            f'color:white;margin:auto;">{emoji}</div>'
            f'<div style="font-size:0.65rem;color:#888;margin-top:2px;">{day_name}</div>'
            f'</div>'
        )
    st.markdown(
        f'<div style="display:flex;justify-content:space-around;background:#f8f9fa;'
        f'border-radius:12px;padding:8px;">{days_html}</div>',
        unsafe_allow_html=True,
    )


def render_xp_bar() -> None:
    xp = st.session_state.get("total_xp", 0)
    info = get_level_info(xp)
    st.markdown(f"**{info['level_title']}** · {xp} XP")
    st.progress(info["progress"])
    if info["xp_to_next"] > 0:
        st.caption(t("xp_next_level", n=info["xp_to_next"]))


def render_daily_tasks() -> None:
    tasks = generate_daily_tasks()
    st.markdown(t("daily_tasks_title"))
    total_xp = sum(tk["xp"] for tk in tasks)
    earned_xp = sum(tk["xp"] for tk in tasks if tk["completed"])
    st.progress(earned_xp / total_xp if total_xp else 0)
    st.caption(t("daily_xp_progress", earned=earned_xp, total=total_xp))
    for task in tasks:
        col1, col2, col3 = st.columns([0.5, 3, 1])
        with col1:
            st.markdown(f"### {task['icon']}")
        with col2:
            task_key = f"task_{task['id']}"
            task_title = t(task_key, n=task.get("target", ""))
            if task["completed"]:
                st.markdown(f"~~{task_title}~~ ✅")
            else:
                st.markdown(f"**{task_title}**")
                prog = task["current"] / task["target"] if task["target"] else 0
                st.progress(prog)
                st.caption(f"{task['current']}/{task['target']}")
        with col3:
            st.markdown(f"**+{task['xp']} XP**")


def render_weak_analysis(words: list, custom_words: list) -> None:
    from core.session import PAGE_FLASH
    analysis = analyze_weak_patterns(words, custom_words)
    st.markdown(t("weak_analysis_title"))
    col1, col2, col3 = st.columns(3)
    for col, (wtype, counts) in zip([col1, col2, col3], analysis["by_type"].items()):
        total = sum(counts.values())
        hard_pct = int(counts.get("hard", 0) / total * 100) if total else 0
        easy_pct = int(counts.get("easy", 0) / total * 100) if total else 0
        color = "#e74c3c" if hard_pct > 30 else ("#f39c12" if hard_pct > 15 else "#27ae60")
        with col:
            st.markdown(
                f'<div style="background:{color}22;border-left:4px solid {color};'
                f'border-radius:8px;padding:12px;">'
                f'<div style="font-weight:700">{wtype}</div>'
                f'<div style="font-size:1.4rem;font-weight:700;color:{color}">%{hard_pct} zor</div>'
                f'<div style="font-size:0.8rem;color:#666">%{easy_pct} öğrenildi</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    if analysis["recommended_focus"]:
        focus = analysis["recommended_focus"]
        st.info(t("weak_recommendation", focus=focus))
        if st.button(t("btn_study_focus", focus=focus), type="primary", key="weak_analysis_btn"):
            pool = [w for w in words + custom_words if w.get("type") == focus]
            hard_first = sorted(
                pool,
                key=lambda w: st.session_state.progress.get(w["word"], {}).get("status", "") == "hard",
                reverse=True,
            )
            st.session_state.flash_deck = hard_first[:25]
            st.session_state.flash_idx = 0
            st.session_state.flash_flipped = False
            st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
            st.session_state.page = PAGE_FLASH
            st.rerun()


def flashcard_front_html(word: dict) -> str:
    article = word.get("article", "")
    if article not in ("der", "die", "das"):
        article = ""
    art_class = f"article-{article}" if article else ""
    type_map = {
        "Verb":    t("type_verb"),
        "Nomen":   t("type_noun"),
        "Adj/Adv": t("type_adjadv"),
    }
    raw_type = word.get("type", "")
    type_label = type_map.get(raw_type, raw_type)
    type_class = f"type-{raw_type}" if raw_type else "type-Unknown"
    art_html = f'<div class="{art_class}">{article}</div>' if article else ""
    return (
        f'<div class="flashcard flashcard-front">'
        f'{art_html}'
        f'<div class="word-big">{word["word"]}</div>'
        f'<span class="type-badge {type_class}">{type_label}</span>'
        f'<div style="margin-top:1rem;opacity:0.6;font-size:0.82rem">{t("flash_front_hint")}</div>'
        f'</div>'
    )


def flashcard_back_html(word: dict, translation: str, display: str, count: int) -> str:
    count_html = (
        f'<div style="font-size:0.85rem;opacity:0.6;margin-top:0.5rem">{t("flash_seen_count", n=count)}</div>'
        if count else ""
    )
    return (
        f'<div class="flashcard flashcard-back">'
        f'<div style="opacity:0.7;font-size:1rem;margin-bottom:0.3rem">{display}</div>'
        f'<div class="word-tr">{translation}</div>'
        f'{count_html}'
        f'</div>'
    )
