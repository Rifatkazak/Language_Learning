import json
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


@st.cache_data
def load_words() -> list:
    path = DATA_DIR / "words.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)
