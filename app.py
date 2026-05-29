import streamlit as st

st.set_page_config(
    page_title="Vocardio",
    page_icon="/app/static/icon.jpeg",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <script>
    (function() {
        var manifest = document.createElement('link');
        manifest.rel = 'manifest';
        manifest.href = '/app/static/manifest.json';
        document.head.appendChild(manifest);

        var theme = document.createElement('meta');
        theme.name = 'theme-color';
        theme.content = '#4B6BFB';
        document.head.appendChild(theme);

        var appleCapable = document.createElement('meta');
        appleCapable.name = 'apple-mobile-web-app-capable';
        appleCapable.content = 'yes';
        document.head.appendChild(appleCapable);

        var appleTitle = document.createElement('meta');
        appleTitle.name = 'apple-mobile-web-app-title';
        appleTitle.content = 'Vocardio';
        document.head.appendChild(appleTitle);

        var appleIcon = document.createElement('link');
        appleIcon.rel = 'apple-touch-icon';
        appleIcon.href = '/app/static/icon.jpeg';
        document.head.appendChild(appleIcon);
    })();
    </script>
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
