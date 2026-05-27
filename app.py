import streamlit as st

st.set_page_config(
    page_title="Goethe B1 Kelime Öğrenimi",
    page_icon="🇩🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.session import bootstrap_session
from core.auth import is_logged_in
from ui.styles import inject_css
from ui.navigation import render_auth_gate, render_sidebar
from storage.word_repo import load_words
from views.router import route

bootstrap_session()
inject_css()

if not is_logged_in():
    render_auth_gate()
    st.stop()

WORDS = load_words()
custom_words = st.session_state.get("custom_words", [])

render_sidebar(WORDS, custom_words)
route(st.session_state.page, WORDS, custom_words)
