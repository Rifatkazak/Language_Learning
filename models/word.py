import html as _html
from dataclasses import dataclass, field
from typing import Optional
import datetime


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


def get_translation(word_text: str, words: list, custom_words: list) -> str:
    if isinstance(word_text, dict):
        return word_text.get("translation", "Çeviri yok")
    for w in words:
        if w.get("word") == word_text:
            return w.get("translation", "Çeviri yok")
    for w in custom_words:
        if w.get("word") == word_text:
            return w.get("translation", "Çeviri yok")
    return "Çeviri yok"


def get_display(w: dict) -> str:
    art = w.get("article", "")
    word = w.get("word", "")
    art_safe = _html.escape(art) if art else ""
    word_safe = _html.escape(word)
    return f"{art_safe} {word_safe}".strip() if art_safe else word_safe


def get_all_words(words: list, custom_words: list) -> list:
    return words + custom_words
