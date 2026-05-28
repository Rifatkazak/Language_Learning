import datetime
import streamlit as st
from storage.user_store import persist_current_user, sanitize_ai_example
from services.gamification import (
    check_and_update_streak, check_achievements, show_achievement_popup,
    update_task_progress, add_xp,
)


def save_progress(word: str, status: str) -> None:
    p = st.session_state.progress
    prev = p.get(word, {})

    prev_interval = prev.get("interval", 0)
    if status == "easy":
        if prev.get("status") == "easy" and prev_interval >= 7:
            new_interval = min(prev_interval * 2, 56)
        else:
            new_interval = 7
    elif status == "ok":
        new_interval = 3
    else:
        new_interval = 1

    next_review = datetime.date.today() + datetime.timedelta(days=new_interval)

    p[word] = {
        "status": status,
        "count": prev.get("count", 0) + 1,
        "last_seen": str(datetime.date.today()),
        "next_review": str(next_review),
        "interval": new_interval,
        "streak": prev.get("streak", 0) + (1 if status == "easy" else 0),
    }

    streak_result = check_and_update_streak()
    if streak_result.get("milestone_reached"):
        st.toast(f"🏆 {streak_result['milestone_reached']} günlük seri!", icon="🔥")

    xp_map = {"easy": 10, "ok": 5, "hard": 3}
    add_xp(xp_map.get(status, 5))

    update_task_progress("flashcard")
    if status == "hard":
        update_task_progress("hard_review")

    new_badges = check_achievements()
    show_achievement_popup(new_badges)

    persist_current_user()


def save_ai_example(word: str, text: str) -> None:
    """Persist an AI-generated sentence — only if it's not an error string."""
    clean = sanitize_ai_example(text)
    if clean:
        cache = st.session_state.get("ai_cache", {})
        cache[word] = clean
        st.session_state.ai_cache = cache
        persist_current_user()


def get_due_words(words: list, custom_words: list) -> list:
    today = str(datetime.date.today())
    all_w = words + custom_words
    due = []
    for w in all_w:
        p = st.session_state.progress.get(w["word"], {})
        if not p or p.get("next_review", "0") <= today:
            due.append(w)
    return due


def filtered_words(words: list, custom_words: list) -> list:
    ft = st.session_state.filter_type
    sq = st.session_state.search.lower().strip()
    all_w = words + custom_words
    result = []
    for w in all_w:
        if ft != "Tümü" and w.get("type") != ft:
            continue
        if sq and sq not in w.get("word", "").lower() and sq not in w.get("translation", "").lower():
            continue
        result.append({
            "word": w.get("word", ""),
            "article": w.get("article", ""),
            "type": w.get("type", ""),
            "translation": w.get("translation", ""),
            "custom": w.get("custom", False),
        })
    return result
