import time
import streamlit as st
from storage.user_store import load_users_file, load_user_data

DEFAULTS = {
    "authenticated": False,
    "current_user": None,
    "progress": {},
    "page": "🏠 Ana Sayfa",
    "flash_deck": [],
    "flash_idx": 0,
    "flash_flipped": False,
    "flash_session": {"correct": 0, "wrong": 0, "skipped": 0},
    "quiz_deck": [],
    "quiz_idx": 0,
    "quiz_state": None,
    "quiz_session": {"correct": 0, "wrong": 0},
    "filter_type": "Tümü",
    "search": "",
    "daily_streak": 0,
    "last_study_date": None,
    "total_study_minutes": 0,
    "session_start": None,
    "ai_sentence": "",
    "custom_words": [],
    "flash_filter_type": "Karışık",
    "quiz_filter_type": "Karışık",
    "flash_comp": None,
    "quiz_comp": None,
    "flash_include_untranslated": False,
    "quiz_include_untranslated": False,
    "total_xp": 0,
    "earned_achievements": [],
    "ai_cache": {},
    "daily_tasks": {},
    "grace_period_used": False,
    "list_page": 0,
    "show_manual_selection": False,
    "manual_selected": [],
    "manual_page": 0,
    "show_challenge_dialog": False,
    "show_challenge_story": False,
    "show_challenge_chat": False,
    "flash_challenge_mode": False,
    "quiz_challenge_mode": False,
    # AI Conversation
    "conv_scenario": None,
    "conv_history": [],
    "conv_feedback": None,
    "conv_total_xp": 0,
    # Word groups
    "word_groups": {},
    "flash_active_group": None,
    "quiz_active_group": None,
}

# Page name constants — used everywhere so emoji typos don't silently break routing
PAGE_HOME      = "🏠 Ana Sayfa"
PAGE_FLASH     = "📇 Flashcards"
PAGE_QUIZ      = "📝 Quiz"
PAGE_GAMES     = "🎮 Kelime Oyunları"
PAGE_CHALLENGE = "🏆 Haftalık Görev"
PAGE_WORDLIST  = "📖 Kelime Listesi"
PAGE_ADD       = "➕ Kelime Ekle"
PAGE_STATS     = "📊 İstatistikler"
PAGE_QUICK     = "⚡ Hızlı Aksiyonlar"
PAGE_CONV      = "🗣️ AI Konuşma"
PAGE_ARTICLE   = "🎯 Artikel Trainer"

ALL_PAGES = [
    PAGE_HOME, PAGE_QUICK, PAGE_FLASH, PAGE_QUIZ, PAGE_CONV, PAGE_ARTICLE, PAGE_GAMES,
    PAGE_CHALLENGE, PAGE_WORDLIST, PAGE_ADD, PAGE_STATS,
]


def init_state() -> None:
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if st.session_state.session_start is None:
        st.session_state.session_start = time.time()


def bootstrap_session() -> None:
    init_state()
    if "users" not in st.session_state:
        st.session_state["users"] = load_users_file()
    # Load user data only once per login, not on every render
    if (
        st.session_state.get("current_user")
        and st.session_state.get("authenticated")
        and not st.session_state.get("_user_data_loaded")
    ):
        users = st.session_state["users"]
        if st.session_state["current_user"] in users:
            load_user_data(st.session_state["current_user"])
            st.session_state["_user_data_loaded"] = True
