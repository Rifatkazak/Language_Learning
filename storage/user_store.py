import datetime
import streamlit as st
from storage.supabase_client import get_supabase

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


def _row_to_user(row: dict) -> dict:
    return {
        "username": row.get("username", ""),
        "password_hash": row.get("password_hash", ""),
        "password_salt": row.get("password_salt", ""),
        "created_at": row.get("created_at", ""),
        "progress": row.get("progress") or {},
        "last_study_date": row.get("last_study_date"),
        "daily_streak": row.get("daily_streak", 0),
        "total_study_minutes": row.get("total_study_minutes", 0),
        "custom_words": row.get("custom_words") or [],
        "total_xp": row.get("total_xp", 0),
        "earned_achievements": row.get("earned_achievements") or [],
        "ai_cache": row.get("ai_cache") or {},
        "daily_tasks": row.get("daily_tasks") or {},
        "grace_period_used": row.get("grace_period_used", False),
        "challenges": row.get("challenges") or {},
        "word_groups": row.get("word_groups") or {},
    }


def load_users_file() -> dict:
    try:
        sb = get_supabase()
        resp = sb.table("users").select("*").execute()
        return {row["username"]: _row_to_user(row) for row in resp.data}
    except Exception:
        return {}


def save_users_file(users: dict) -> None:
    try:
        sb = get_supabase()
        for username, data in users.items():
            row = {
                "username": username,
                "password_hash": data.get("password_hash", ""),
                "password_salt": data.get("password_salt", ""),
                "created_at": data.get("created_at", ""),
                "progress": data.get("progress", {}),
                "last_study_date": data.get("last_study_date"),
                "daily_streak": data.get("daily_streak", 0),
                "total_study_minutes": int(data.get("total_study_minutes", 0)),
                "custom_words": data.get("custom_words", []),
                "total_xp": data.get("total_xp", 0),
                "earned_achievements": data.get("earned_achievements", []),
                "ai_cache": data.get("ai_cache", {}),
                "daily_tasks": data.get("daily_tasks", {}),
                "grace_period_used": data.get("grace_period_used", False),
                "challenges": data.get("challenges", {}),
                "word_groups": data.get("word_groups", {}),
            }
            sb.table("users").upsert(row).execute()
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
    raw = users.get(username)

    if not raw:
        try:
            sb = get_supabase()
            resp = sb.table("users").select("*").eq("username", username).single().execute()
            raw = _row_to_user(resp.data)
        except Exception:
            raw = {}

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
    st.session_state.word_groups = data.get("word_groups", {})
    st.session_state.current_user = username
    for k, v in data.get("challenges", {}).items():
        if isinstance(k, str) and k.startswith("week_"):
            st.session_state[k] = v


def persist_current_user() -> None:
    username = st.session_state.get("current_user")
    if not username:
        return

    users = st.session_state.get("users", {})
    existing = users.get(username, {})

    today = datetime.date.today()
    cy, cw, _ = today.isocalendar()

    def _keep_challenge(key: str) -> bool:
        try:
            _, year, week = key.split("_")
            weeks_ago = (cy * 52 + cw) - (int(year) * 52 + int(week))
            return 0 <= weeks_ago <= 3
        except (ValueError, AttributeError):
            return False

    weekly_challenges = {
        k: v for k, v in st.session_state.items()
        if isinstance(k, str) and k.startswith("week_") and isinstance(v, dict)
        and _keep_challenge(k)
    }

    user_row = {
        "username": username,
        "password_hash": existing.get("password_hash", ""),
        "password_salt": existing.get("password_salt", ""),
        "created_at": existing.get("created_at", ""),
        "progress": st.session_state.get("progress", {}),
        "last_study_date": st.session_state.get("last_study_date"),
        "daily_streak": st.session_state.get("daily_streak", 0),
        "total_study_minutes": int(st.session_state.get("total_study_minutes", 0)),
        "custom_words": st.session_state.get("custom_words", []),
        "total_xp": st.session_state.get("total_xp", 0),
        "earned_achievements": st.session_state.get("earned_achievements", []),
        "ai_cache": st.session_state.get("ai_cache", {}),
        "daily_tasks": st.session_state.get("daily_tasks", {}),
        "grace_period_used": st.session_state.get("grace_period_used", False),
        "challenges": weekly_challenges,
        "word_groups": st.session_state.get("word_groups", {}),
    }

    try:
        sb = get_supabase()
        sb.table("users").upsert(user_row).execute()
    except Exception:
        pass

    users[username] = user_row
    st.session_state["users"] = users


def publish_community_group(group_name: str, words: list, author: str) -> bool:
    try:
        sb = get_supabase()
        sb.table("community_groups").upsert(
            {
                "group_name": group_name,
                "author": author,
                "words": words,
                "word_count": len(words),
            },
            on_conflict="author,group_name",
        ).execute()
        return True
    except Exception:
        return False


def load_community_groups() -> list:
    try:
        sb = get_supabase()
        resp = sb.table("community_groups").select("*").order("import_count", desc=True).execute()
        return resp.data or []
    except Exception:
        return []


def increment_group_import(group_id: int) -> None:
    try:
        sb = get_supabase()
        row = sb.table("community_groups").select("import_count").eq("id", group_id).single().execute()
        current = (row.data or {}).get("import_count", 0)
        sb.table("community_groups").update({"import_count": current + 1}).eq("id", group_id).execute()
    except Exception:
        pass


def load_challenges_file() -> dict:
    try:
        sb = get_supabase()
        resp = sb.table("community_challenges").select("*").execute()
        return {row["week_key"]: row["data"] for row in resp.data}
    except Exception:
        return {}


def save_challenges_file(challenges: dict) -> None:
    try:
        sb = get_supabase()
        for week_key, data in challenges.items():
            sb.table("community_challenges").upsert({"week_key": week_key, "data": data}).execute()
    except Exception:
        pass
