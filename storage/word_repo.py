import json
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


@st.cache_data
def load_words() -> list:
    path = DATA_DIR / "words.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_word_levels() -> dict:
    """Loads word_levels.json (list format) and returns a {word: level} dict."""
    path = DATA_DIR / "word_levels.json"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {item["word"]: item["level"] for item in data if "word" in item and "level" in item}
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def save_word_levels(levels: dict) -> None:
    """Saves {word: level} dict back to word_levels.json in list format."""
    path = DATA_DIR / "word_levels.json"
    data = [{"word": w, "level": l} for w, l in levels.items()]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
