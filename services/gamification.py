import datetime
import streamlit as st
from storage.user_store import persist_current_user

ACHIEVEMENTS = {
    "streak_3":      {"title": "🔥 İlk Alev",         "desc": "3 günlük seri",         "xp": 30},
    "streak_7":      {"title": "⚡ Haftalık Kahraman", "desc": "7 günlük seri",         "xp": 100},
    "streak_30":     {"title": "🏆 Aylık Efsane",      "desc": "30 günlük seri",        "xp": 500},
    "words_50":      {"title": "📚 Başlangıç",         "desc": "50 kelime öğrenildi",   "xp": 50},
    "words_100":     {"title": "📖 Öğrenci",           "desc": "100 kelime öğrenildi",  "xp": 150},
    "words_250":     {"title": "🎓 Kapsamlı",          "desc": "250 kelime öğrenildi",  "xp": 300},
    "words_500":     {"title": "🌟 Uzman",             "desc": "500 kelime öğrenildi",  "xp": 750},
    "quiz_perfect":  {"title": "💯 Mükemmel",          "desc": "Quiz'den 100% aldın",   "xp": 75},
    "quiz_100":      {"title": "🧠 Quiz Ustası",       "desc": "100 quiz sorusu",       "xp": 200},
    "hard_conqueror":{"title": "💪 Zorluğu Yendi",     "desc": "10 zorlu kelimeyi öğrendin", "xp": 100},
    "early_bird":    {"title": "🌅 Sabah Kuşu",        "desc": "Sabah 7'den önce çalıştın", "xp": 25},
    "night_owl":     {"title": "🦉 Gece Baykuşu",      "desc": "Gece yarısından sonra çalıştın", "xp": 25},
    "ai_user":       {"title": "🤖 AI Destekli",       "desc": "İlk AI örnek cümle aldın", "xp": 20},
    "weekly_champion":{"title":"🏅 Haftalık Şampiyon", "desc": "Haftalık challenge tamamlandı","xp":200},
}

LEVELS = [
    (0,     "🌱 Başlangıç", "#95a5a6"),
    (100,   "📚 Öğrenci",   "#3498db"),
    (300,   "✏️ Çalışkan",  "#2ecc71"),
    (600,   "🎯 Odaklı",    "#e67e22"),
    (1000,  "⚡ Hızlı",     "#e74c3c"),
    (1500,  "🏅 Yetenekli", "#9b59b6"),
    (2500,  "🎓 Bilgili",   "#1abc9c"),
    (4000,  "🌟 Uzman",     "#f39c12"),
    (6000,  "🏆 Usta",      "#e74c3c"),
    (10000, "👑 Efsane",    "#ffd700"),
]


def get_level_info(xp: int) -> dict:
    current = LEVELS[0]
    nxt = LEVELS[1]
    for i, entry in enumerate(LEVELS):
        if xp >= entry[0]:
            current = entry
            nxt = LEVELS[i + 1] if i + 1 < len(LEVELS) else None

    if nxt:
        progress = (xp - current[0]) / (nxt[0] - current[0])
        xp_to_next = nxt[0] - xp
        next_title = nxt[1]
    else:
        progress = 1.0
        xp_to_next = 0
        next_title = "MAX"

    return {
        "level_title": current[1],
        "level_color": current[2],
        "next_level": next_title,
        "progress": min(progress, 1.0),
        "xp_to_next": xp_to_next,
    }


def add_xp(amount: int) -> None:
    st.session_state.total_xp = st.session_state.get("total_xp", 0) + amount


def check_and_update_streak() -> dict:
    today = datetime.date.today()
    today_str = str(today)
    yesterday_str = str(today - datetime.timedelta(days=1))

    last_date = st.session_state.get("last_study_date")
    current_streak = st.session_state.get("daily_streak", 0)
    grace_used = st.session_state.get("grace_period_used", False)

    result = {"current_streak": current_streak, "milestone_reached": None,
              "streak_broken": False, "grace_period_available": False}

    if last_date == today_str:
        return result

    if last_date == yesterday_str:
        new_streak = current_streak + 1
        st.session_state.daily_streak = new_streak
        st.session_state.last_study_date = today_str
        result["current_streak"] = new_streak
        milestones = [3, 7, 14, 30, 50, 100]
        if new_streak in milestones:
            result["milestone_reached"] = new_streak
            achievements = st.session_state.get("earned_achievements", [])
            achievements.append({"type": "streak", "value": new_streak, "date": today_str})
            st.session_state.earned_achievements = achievements
    elif last_date:
        days_missed = (today - datetime.date.fromisoformat(last_date)).days
        if current_streak >= 30 and not grace_used and days_missed == 2:
            result["grace_period_available"] = True
        else:
            result["streak_broken"] = current_streak > 3
            if not result["grace_period_available"]:
                st.session_state.daily_streak = 1
                st.session_state.last_study_date = today_str
    else:
        st.session_state.daily_streak = 1
        st.session_state.last_study_date = today_str

    persist_current_user()
    return result


def check_achievements() -> list:
    raw = st.session_state.get("earned_achievements", [])
    # Normalize: old data may contain dicts instead of string IDs
    earned = set(x if isinstance(x, str) else x.get("id", "") for x in raw if x)
    new_badges = []
    p = st.session_state.progress
    easy_count = sum(1 for v in p.values() if v.get("status") == "easy")
    streak = st.session_state.get("daily_streak", 0)

    checks = [
        ("streak_3",  streak >= 3),
        ("streak_7",  streak >= 7),
        ("streak_30", streak >= 30),
        ("words_50",  easy_count >= 50),
        ("words_100", easy_count >= 100),
        ("words_250", easy_count >= 250),
        ("words_500", easy_count >= 500),
    ]
    hour = datetime.datetime.now().hour
    if 5 <= hour < 7:
        checks.append(("early_bird", True))
    elif hour >= 23 or hour < 2:
        checks.append(("night_owl", True))

    for badge_id, condition in checks:
        if condition and badge_id not in earned:
            new_badges.append(badge_id)
            earned.add(badge_id)
            add_xp(ACHIEVEMENTS[badge_id]["xp"])

    if new_badges:
        st.session_state.earned_achievements = list(earned)
        persist_current_user()
    return new_badges


def show_achievement_popup(badge_ids: list) -> None:
    for bid in badge_ids:
        badge = ACHIEVEMENTS.get(bid, {})
        st.toast(
            f"{badge.get('title','🏅')} — {badge.get('desc','')} (+{badge.get('xp',0)} XP)",
            icon="🎉",
        )


def generate_daily_tasks() -> list:
    today_str = str(datetime.date.today())
    cached = st.session_state.get("daily_tasks", {})
    if cached.get("date") == today_str:
        return cached.get("tasks", [])

    p = st.session_state.progress
    hard_count = sum(1 for v in p.values() if v.get("status") == "hard")
    daily_target = min(20, max(10, hard_count + 5))

    tasks = [
        {"id": "flashcard_daily", "title": f"{daily_target} Flashcard Çalış",
         "icon": "📇", "xp": 50, "target": daily_target, "current": 0,
         "type": "flashcard", "completed": False},
        {"id": "quiz_daily", "title": "10 Quiz Sorusu Çöz",
         "icon": "📝", "xp": 40, "target": 10, "current": 0,
         "type": "quiz", "completed": False},
    ]
    if hard_count >= 3:
        tasks.append({
            "id": "hard_words", "title": f"{min(5,hard_count)} Zorlu Kelimeyi Tekrarla",
            "icon": "💪", "xp": 60, "target": min(5, hard_count), "current": 0,
            "type": "hard_review", "completed": False,
        })
    if datetime.date.today().weekday() == 6:
        tasks.append({
            "id": "weekly_review", "title": "Haftalık Büyük Test (30 Soru)",
            "icon": "🏆", "xp": 150, "target": 30, "current": 0,
            "type": "weekly", "completed": False,
        })

    st.session_state.daily_tasks = {"date": today_str, "tasks": tasks, "total_xp_earned": 0}
    persist_current_user()
    return tasks


def update_task_progress(task_type: str, increment: int = 1) -> int:
    tasks_data = st.session_state.get("daily_tasks", {})
    tasks = tasks_data.get("tasks", [])
    xp_earned = 0
    for task in tasks:
        if task["type"] == task_type and not task["completed"]:
            task["current"] = min(task["current"] + increment, task["target"])
            if task["current"] >= task["target"]:
                task["completed"] = True
                xp_earned += task["xp"]
                st.balloons()
    if xp_earned > 0:
        add_xp(xp_earned)
        tasks_data["total_xp_earned"] = tasks_data.get("total_xp_earned", 0) + xp_earned
    # Always reassign so Streamlit detects the mutation, and persist progress
    st.session_state.daily_tasks = tasks_data
    persist_current_user()
    return xp_earned
