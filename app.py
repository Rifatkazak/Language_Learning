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
try:
    _qp = st.query_params
    _qp_keys = list(_qp.keys())
    if "stripe_session" in _qp_keys:
        _sid = str(_qp["stripe_session"])
        _done_key = f"_stripe_done_{_sid[:24]}"
        if _sid and not st.session_state.get(_done_key):
            from services.stripe_service import validate_session
            from services.subscription import activate_stripe_subscription_for_user
            import traceback as _tb
            try:
                _result = validate_session(_sid)
                if _result:
                    ok = activate_stripe_subscription_for_user(_result)
                    st.session_state[_done_key] = True
                    st.session_state["_stripe_success"] = ok
                    if not ok:
                        st.session_state["_stripe_error"] = "activate_failed"
                else:
                    st.session_state["_stripe_error"] = f"validate_none:{_sid[:20]}"
            except Exception as _e:
                import traceback
                st.session_state["_stripe_error"] = traceback.format_exc()
        _saved_t = _qp.get("t")
        st.query_params.clear()
        if _saved_t:
            st.query_params["t"] = _saved_t
        st.rerun()
    elif "stripe_cancel" in _qp_keys:
        _saved_t = _qp.get("t")
        st.query_params.clear()
        if _saved_t:
            st.query_params["t"] = _saved_t
        st.rerun()
except Exception as _outer_e:
    st.session_state["_stripe_error"] = f"outer:{type(_outer_e).__name__}:{_outer_e}"

if not is_logged_in():
    render_auth_gate()
    st.stop()

# ── Handle browser voice mode redirect (after auth so ai_cache is loaded) ─────
try:
    _qv = st.query_params.get("_v")
    if _qv:
        import urllib.parse as _upl
        from core.session import PAGE_CONV
        _vtext = _upl.unquote(_qv)
        st.query_params.pop("_v", None)
        _active = st.session_state.get("ai_cache", {}).get("__active_conv__")
        if _active and _active.get("scenario"):
            st.session_state.conv_scenario = _active["scenario"]
            st.session_state.conv_history = _active.get("history", [])
            st.session_state.conv_total_xp = _active.get("total_xp", 0)
        st.session_state.conv_voice_mode = True
        if _vtext:
            st.session_state["conv_voice_pending"] = _vtext
        st.session_state.page = PAGE_CONV
except Exception:
    pass

if st.session_state.pop("_stripe_success", False):
    st.toast("✅ Ödeme başarılı! AI üyeliğin aktif edildi.", icon="🎉")
_stripe_err = st.session_state.pop("_stripe_error", None)
if _stripe_err:
    st.error(f"Stripe aktivasyon hatası: {_stripe_err}")

WORDS = load_words()
custom_words = st.session_state.get("custom_words", [])

render_sidebar(WORDS, custom_words)
route(st.session_state.page, WORDS, custom_words)
