import html as _html
from dataclasses import dataclass, field
from typing import Optional
import datetime
import streamlit as st


@dataclass
class Word:
    word: str
    article: str = ""
    type: str = ""
    translation: str = ""
    custom: bool = False
    notes: str = ""


@dataclass
class WordProgress:
    status: str = "unseen"
    count: int = 0
    last_seen: Optional[str] = None
    next_review: Optional[str] = None
    streak: int = 0


def _tr_key() -> str:
    lang = st.session_state.get("ui_lang", "tr")
    return "translation_en" if lang == "en" else "translation"


def _fallback(w: dict) -> str:
    key = _tr_key()
    return w.get(key) or w.get("translation") or ("No translation" if key == "translation_en" else "Çeviri yok")


def get_translation(word_text: str, words: list, custom_words: list) -> str:
    if isinstance(word_text, dict):
        return _fallback(word_text)
    for w in words:
        if w.get("word") == word_text:
            return _fallback(w)
    for w in custom_words:
        if w.get("word") == word_text:
            return _fallback(w)
    return "No translation" if _tr_key() == "translation_en" else "Çeviri yok"


def get_display(w: dict) -> str:
    art = w.get("article", "")
    word = w.get("word", "")
    art_safe = _html.escape(art) if art else ""
    word_safe = _html.escape(word)
    return f"{art_safe} {word_safe}".strip() if art_safe else word_safe


def get_all_words(words: list, custom_words: list) -> list:
    return words + custom_words
