import json
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"

_ERROR_MARKERS = (
    "AI Hatası", "AI Error", "Error code:", "insufficient_quota",
    "Quota exceeded", "invalid_request_error", "servis hatası",
)


def sanitize_ai_example(text) -> None:
    """Returns None if text looks like an error message."""
    if not text or not isinstance(text, str):
        return None
    for marker in _ERROR_MARKERS:
        if marker in text:
            return None
    return text


def load_users_file() -> dict:
    if not USERS_FILE.exists():
        return {}
    try:
        with open(USERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_users_file(users: dict) -> None:
    try:
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _migrate_user(user_data: dict) -> dict:
    """Move clean ai_example values from progress into ai_cache; strip errors."""
    progress = user_data.get("progress", {})
    ai_cache = user_data.get("ai_cache", {})

    for word, p in progress.items():
        if "ai_example" in p:
            clean = sanitize_ai_example(p.pop("ai_example"))
            if clean and word not in ai_cache:
                ai_cache[word] = clean

    user_data["ai_cache"] = ai_cache
    return user_data


def load_user_data(username: str) -> None:
    users = st.session_state.get("users", {})
    raw = users.get(username, {})
    data = _migrate_user(dict(raw))

    st.session_state.progress = data.get("progress", {})
    st.session_state.last_study_date = data.get("last_study_date")
    st.session_state.daily_streak = data.get("daily_streak", 0)
    st.session_state.total_study_minutes = data.get("total_study_minutes", 0)
    st.session_state.custom_words = data.get("custom_words", [])
    st.session_state.total_xp = data.get("total_xp", 0)
    raw_achievements = data.get("earned_achievements", [])
    st.session_state.earned_achievements = [
        x if isinstance(x, str) else x.get("id", "") for x in raw_achievements if x
    ]
    st.session_state.ai_cache = data.get("ai_cache", {})
    st.session_state.daily_tasks = data.get("daily_tasks", {})
    st.session_state.grace_period_used = data.get("grace_period_used", False)
    st.session_state.current_user = username


def persist_current_user() -> None:
    username = st.session_state.get("current_user")
    if not username:
        return
    users = st.session_state.get("users", {})
    existing = users.get(username, {})

    users[username] = {
        "password_hash": existing.get("password_hash", ""),
        "password_salt": existing.get("password_salt", ""),
        "created_at": existing.get("created_at", ""),
        "progress": st.session_state.get("progress", {}),
        "last_study_date": st.session_state.get("last_study_date"),
        "daily_streak": st.session_state.get("daily_streak", 0),
        "total_study_minutes": st.session_state.get("total_study_minutes", 0),
        "custom_words": st.session_state.get("custom_words", []),
        "total_xp": st.session_state.get("total_xp", 0),
        "earned_achievements": st.session_state.get("earned_achievements", []),
        "ai_cache": st.session_state.get("ai_cache", {}),
        "daily_tasks": st.session_state.get("daily_tasks", {}),
        "grace_period_used": st.session_state.get("grace_period_used", False),
    }
    save_users_file(users)
    st.session_state["users"] = users


CHALLENGES_FILE = DATA_DIR / "challenges.json"


def load_challenges_file() -> dict:
    if not CHALLENGES_FILE.exists():
        return {}
    try:
        with open(CHALLENGES_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_challenges_file(challenges: dict) -> None:
    try:
        CHALLENGES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CHALLENGES_FILE, "w", encoding="utf-8") as f:
            json.dump(challenges, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
