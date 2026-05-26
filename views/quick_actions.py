import datetime
import random
import streamlit as st
from core.session import PAGE_FLASH


def _todays_studied(words: list, custom_words: list) -> list:
    today = str(datetime.date.today())
    all_w = {w["word"]: w for w in words + custom_words}
    studied = []
    for word_key, info in st.session_state.progress.items():
        if info.get("last_seen") == today and word_key in all_w:
            studied.append(all_w[word_key])
    return studied


def render(words: list, custom_words: list) -> None:
    st.markdown("---")
    st.markdown("### ⚡ Hızlı Aksiyonlar")

    today_studied = _todays_studied(words, custom_words)

    col1, col2, col3 = st.columns(3)

    with col1:
        label = f"🔁 Bugünkü Tekrarlar ({len(today_studied)})"
        if st.button(label, use_container_width=True):
            if today_studied:
                random.shuffle(today_studied)
                st.session_state.flash_deck = today_studied
                st.session_state.flash_idx = 0
                st.session_state.flash_flipped = False
                st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
                st.session_state.page = PAGE_FLASH
                st.rerun()
            else:
                st.toast("Bugün henüz flashcard çalışmadın!", icon="💡")

    with col2:
        if st.button("🎲 Rastgele 10 Kelime", use_container_width=True):
            all_words = words + custom_words
            sample = random.sample(all_words, min(10, len(all_words)))
            st.session_state.flash_deck = sample
            st.session_state.flash_idx = 0
            st.session_state.flash_flipped = False
            st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
            st.session_state.page = PAGE_FLASH
            st.rerun()

    with col3:
        if st.button("💪 Sadece Zorlar", use_container_width=True):
            hard = [w for w in words + custom_words
                    if st.session_state.progress.get(w["word"], {}).get("status") == "hard"]
            if hard:
                st.session_state.flash_deck = hard[:15]
                st.session_state.flash_idx = 0
                st.session_state.flash_flipped = False
                st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
                st.session_state.page = PAGE_FLASH
                st.rerun()
            else:
                st.toast("Hiç zor kelimen yok! Harika gidiyorsun! 🎉", icon="🏆")
