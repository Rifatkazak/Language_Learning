import streamlit as st

st.set_page_config(
    page_title="Vocardio",
    page_icon="/app/static/icon.jpeg",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <link rel="manifest" href="/app/static/manifest.json">
    <link rel="icon" href="/app/static/icon.jpeg">
    <meta name="theme-color" content="#4B6BFB">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Vocardio">
    <link rel="apple-touch-icon" href="/app/static/icon.jpeg">
    """,
    unsafe_allow_html=True,
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
