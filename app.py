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

# ── Handle Stripe return redirect (BEFORE auth check) ─────────────────────────
_qp = st.query_params
if "stripe_session" in _qp:
    _sid = _qp.get("stripe_session", "")
    _done_key = f"_stripe_done_{_sid[:24]}"
    if _sid and not st.session_state.get(_done_key):
        from services.stripe_service import validate_session
        from services.subscription import activate_stripe_subscription_for_user
        try:
            _result = validate_session(_sid)
            if _result:
                ok = activate_stripe_subscription_for_user(_result)
                st.session_state[_done_key] = True
                if ok:
                    st.session_state["_stripe_success"] = True
                else:
                    st.session_state["_stripe_error"] = "activate_failed"
            else:
                st.session_state["_stripe_error"] = f"validate_failed:{_sid[:16]}"
        except Exception as _e:
            st.session_state["_stripe_error"] = str(_e)
    st.query_params.clear()
    st.rerun()
elif "stripe_cancel" in _qp:
    st.query_params.clear()
    st.rerun()

if not is_logged_in():
    render_auth_gate()
    st.stop()

if st.session_state.pop("_stripe_success", False):
    st.toast("✅ Ödeme başarılı! AI üyeliğin aktif edildi.", icon="🎉")
_stripe_err = st.session_state.pop("_stripe_error", None)
if _stripe_err:
    st.error(f"Stripe aktivasyon hatası: {_stripe_err}")

WORDS = load_words()
custom_words = st.session_state.get("custom_words", [])

render_sidebar(WORDS, custom_words)
route(st.session_state.page, WORDS, custom_words)
