import random
import streamlit as st
from services.spaced_repetition import build_adaptive_deck, build_deck_from_composition
from services.progress import filtered_words
from models.word import get_translation


def start_flash(words: list, custom_words: list) -> None:
    pool = filtered_words(words, custom_words)
    if not st.session_state.get("flash_include_untranslated", False):
        pool = [w for w in pool if w.get("translation") not in ("Çeviri yok", "—", None, "")]
    comp = st.session_state.get("flash_comp")
    if comp and any(comp.values()):
        deck = build_deck_from_composition(pool, comp, 30)
    else:
        deck = build_adaptive_deck(pool, st.session_state.progress, 30)
    st.session_state.flash_deck = deck
    st.session_state.flash_idx = 0
    st.session_state.flash_flipped = False
    st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
    st.session_state.ai_sentence = ""


def start_quiz(words: list, custom_words: list) -> None:
    qft = st.session_state.get("quiz_filter_type", "Karışık")
    all_pool = filtered_words(words, custom_words)
    effective = qft if qft not in ("Karışık", "Tümü") else st.session_state.get("filter_type", "Tümü")
    if effective not in ("Karışık", "Tümü"):
        all_pool = [w for w in all_pool if w.get("type") == effective]

    if st.session_state.get("quiz_include_untranslated", False):
        pool = all_pool
    else:
        translated = [w for w in all_pool if get_translation(w["word"], words, custom_words) not in ("Çeviri yok", "—")]
        pool = translated if len(translated) >= 10 else all_pool

    comp = st.session_state.get("quiz_comp")
    if comp:
        deck = build_deck_from_composition(pool, comp, 20)
    else:
        random.shuffle(pool)
        deck = pool[:20]

    st.session_state.quiz_deck = deck
    st.session_state.quiz_idx = 0
    st.session_state.quiz_session = {"correct": 0, "wrong": 0}
    make_quiz_question(words, custom_words)


def make_quiz_question(words: list, custom_words: list) -> None:
    idx = st.session_state.quiz_idx
    deck = st.session_state.quiz_deck
    if idx >= len(deck):
        st.session_state.quiz_state = None
        return
    word = deck[idx]
    all_w = words + custom_words

    qft = st.session_state.get("quiz_filter_type", "Karışık")
    effective = qft if qft not in ("Karışık", "Tümü") else st.session_state.get("filter_type", "Tümü")
    if effective not in ("Karışık", "Tümü"):
        same_type = [w for w in all_w if w.get("type") == effective and w["word"] != word["word"]]
    else:
        same_type = [w for w in all_w if w["word"] != word["word"]]

    candidates = [w for w in same_type
                  if get_translation(w["word"], words, custom_words) not in ("Çeviri yok", "—")]
    if len(candidates) < 3:
        candidates = same_type if len(same_type) >= 3 else [w for w in all_w if w["word"] != word["word"]]

    wrongs = random.sample(candidates, min(3, len(candidates)))
    options = random.sample([word] + wrongs, min(4, 1 + len(wrongs)))
    st.session_state.quiz_state = {
        "word": word,
        "options": options,
        "answered": None,
        "correct": None,
    }
