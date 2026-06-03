import hashlib
import streamlit as st
import streamlit.components.v1 as _components
from services.scenario_service import load_scenarios, get_categories
from services.conversation_engine import ConversationEngine
from services.ai_service import get_ai_service, AIService
from services.gamification import add_xp
from storage.user_store import persist_current_user
from core.i18n import t


def _ui_lang() -> str:
    return st.session_state.get("ui_lang", "tr")


def _sc_text(sc: dict, key: str) -> str:
    """Return English field if EN mode, Turkish _tr field otherwise."""
    if _ui_lang() == "en":
        return sc.get(key, sc.get(key + "_tr", ""))
    return sc.get(key + "_tr", sc.get(key, ""))


def _cat_label(cat: dict) -> str:
    if _ui_lang() == "en":
        return cat["id"].replace("_", " ").title()
    return cat["name_tr"]


# ── CSS injected once per render ────────────────────────────────────────────

_CSS = """
<style>
/* ── Scenario selection cards ─────────────────────────────────────────── */
.conv-card {
    background: var(--background-color);
    border: 1.5px solid rgba(100,116,139,0.2);
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.5rem;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.conv-card:hover {
    border-color: var(--primary-color, #4a90d9);
    box-shadow: 0 4px 20px rgba(74,144,217,0.12);
}
.conv-card-icon  { font-size: 1.9rem; margin-bottom: 0.3rem; line-height: 1.2; }
.conv-card-title { font-size: 1rem; font-weight: 700; color: #1e293b; margin-bottom: 2px; }
.conv-card-sub   { font-size: 0.8rem; color: #64748b; margin-bottom: 6px; }
.conv-card-goal  { font-size: 0.78rem; color: #475569; margin-top: 3px; }

.conv-badge {
    display: inline-block;
    border: 1.5px solid;
    border-radius: 20px;
    padding: 1px 9px;
    font-size: 0.7rem;
    font-weight: 700;
    margin-right: 5px;
}
.conv-cat-badge {
    display: inline-block;
    background: #f1f5f9;
    color: #64748b;
    border-radius: 20px;
    padding: 1px 9px;
    font-size: 0.7rem;
    font-weight: 500;
}

/* ── Feedback card (appears after user chat bubble) ───────────────────── */
.conv-feedback {
    margin: 3px 0 10px 52px;
    padding: 10px 14px;
    border-radius: 0 8px 8px 0;
    font-size: 0.88rem;
    line-height: 1.5;
}
.conv-feedback-ok  { background: #f0fff4; border-left: 3px solid #27ae60; }
.conv-feedback-fix { background: #fffbeb; border-left: 3px solid #f59e0b; }

.conv-feedback-header-ok  { color: #1a5c30; font-weight: 700; margin: 0 0 3px; }
.conv-feedback-header-fix { color: #92400e; font-weight: 700; margin: 0 0 5px; }

/* ── Vocabulary chips ─────────────────────────────────────────────────── */
.conv-vocab-chip {
    display: inline-block;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.76rem;
    font-weight: 600;
    color: #1d4ed8;
    margin: 2px 3px 2px 0;
}
.conv-vocab-tr { font-weight: 400; color: #64748b; }

/* ── XP pill ──────────────────────────────────────────────────────────── */
.conv-xp-pill {
    display: inline-block;
    background: linear-gradient(90deg, #4a90d9, #27ae60);
    color: white;
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.78rem;
    font-weight: 700;
    margin-top: 6px;
}
</style>
"""


# ── Public entry point ────────────────────────────────────────────────────

def render(words: list, custom_words: list) -> None:  # noqa: ARG001
    st.markdown(_CSS, unsafe_allow_html=True)

    scenario = st.session_state.get("conv_scenario")

    if scenario is None:
        _render_selector()
        return

    # Guard: ensure history has at least the opening message
    if not st.session_state.get("conv_history"):
        engine = ConversationEngine(scenario)
        st.session_state.conv_history = [engine.get_opening_message()]

    _render_header(scenario)
    st.divider()
    _render_chat(scenario)


# ── Scenario selector ─────────────────────────────────────────────────────

def _render_selector() -> None:
    st.markdown(t("conv_title"))
    st.markdown(t("conv_subtitle"))
    st.divider()

    categories = get_categories()
    all_label = t("all")
    cat_labels = [all_label] + [_cat_label(c) for c in categories]

    selected_label = st.radio(
        t("conv_category_label"),
        cat_labels,
        horizontal=True,
        key="conv_cat_filter",
        label_visibility="collapsed",
    )
    st.markdown("")

    all_scenarios = load_scenarios()
    if selected_label != all_label:
        cat_id = next(
            (c["id"] for c in categories if _cat_label(c) == selected_label),
            None,
        )
        filtered = (
            [s for s in all_scenarios if s["category"] == cat_id]
            if cat_id
            else all_scenarios
        )
    else:
        filtered = all_scenarios

    if not filtered:
        st.info(t("conv_no_scenarios"))
        return

    cols = st.columns(2, gap="medium")
    for i, sc in enumerate(filtered):
        with cols[i % 2]:
            _render_scenario_card(sc)


def _render_scenario_card(sc: dict) -> None:
    level_color = "#4a90d9" if "B1" in sc.get("cefr_level", "") else "#27ae60"
    context_full = _sc_text(sc, "context")
    context_snippet = context_full[:90] + ("…" if len(context_full) > 90 else "")
    subtitle = _sc_text(sc, "title")
    cat_badge = _cat_label({"id": sc.get("category", ""), "name_tr": sc.get("category_tr", "")})
    st.markdown(
        f"""<div class="conv-card">
            <div class="conv-card-icon">{sc.get('icon', '💬')}</div>
            <div class="conv-card-title">{sc['title']}</div>
            <div class="conv-card-sub">{subtitle}</div>
            <div style="margin:4px 0 7px">
                <span class="conv-badge"
                      style="border-color:{level_color};color:{level_color}">
                    {sc.get('cefr_level', 'B1')}
                </span>
                <span class="conv-cat-badge">{cat_badge}</span>
            </div>
            <div class="conv-card-goal">{context_snippet}</div>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button(
        t("conv_btn_start", title=sc["title"]),
        key=f"conv_start_{sc['id']}",
        use_container_width=True,
        type="primary",
    ):
        _start_conversation(sc)
        st.rerun()


def _start_conversation(sc: dict) -> None:
    engine = ConversationEngine(sc)
    st.session_state.conv_scenario = sc
    st.session_state.conv_history = [engine.get_opening_message()]
    st.session_state.conv_feedback = None
    st.session_state.conv_total_xp = 0


# ── Active conversation ───────────────────────────────────────────────────

def _render_header(scenario: dict) -> None:
    c1, c2, c3 = st.columns([1, 5, 2])
    with c1:
        st.markdown(
            f"<span style='font-size:2.3rem;line-height:1.1'>"
            f"{scenario.get('icon', '💬')}</span>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(f"### {scenario['title']}")
        st.caption(
            f"{_sc_text(scenario, 'title')} • "
            f"{scenario.get('cefr_level', 'B1')} • "
            f"{t('conv_your_role', role=scenario.get('user_role', ''))}"
        )
    with c3:
        xp = st.session_state.get("conv_total_xp", 0)
        user_msgs = sum(
            1 for m in st.session_state.get("conv_history", [])
            if m["role"] == "user"
        )
        st.markdown(
            f"<div style='text-align:right;padding-top:4px'>"
            f"<span class='conv-xp-pill'>+{xp} XP</span><br>"
            f"<small style='color:#64748b'>{t('conv_msg_count', n=user_msgs)}</small></div>",
            unsafe_allow_html=True,
        )

    btn_col1, btn_col2 = st.columns([3, 1])
    with btn_col1:
        if st.button(t("btn_change_scenario"), key="conv_back", use_container_width=True):
            st.session_state.conv_scenario = None
            st.session_state.conv_history = []
            st.session_state.conv_total_xp = 0
            st.session_state.conv_voice_mode = False
            st.rerun()
    with btn_col2:
        voice_mode = st.session_state.get("conv_voice_mode", False)
        label = t("conv_voice_off") if voice_mode else t("conv_voice_on")
        if st.button(label, key="conv_voice_toggle", use_container_width=True,
                     help="Voice mode: speak with microphone, AI responds with audio"):
            new_mode = not voice_mode
            st.session_state.conv_voice_mode = new_mode
            st.session_state.pop("conv_voice_pending", None)
            st.session_state.pop("_voice_audio_hash", None)
            # Save conv state so browser redirect can restore it
            if new_mode:
                _save_active_conv()
            st.rerun()


def _render_chat(scenario: dict) -> None:
    engine = ConversationEngine(scenario)
    voice_mode = st.session_state.get("conv_voice_mode", False)

    # ── Reference panels ──────────────────────────────────────────────────
    col_info, col_vocab = st.columns(2)
    with col_info:
        with st.expander(t("conv_context_exp"), expanded=False):
            st.markdown(_sc_text(scenario, "context"))
            st.markdown(t("conv_your_role_label", role=scenario.get("user_role", "")))
            st.markdown(t("conv_ai_role_label", role=scenario.get("ai_role", "")))
    with col_vocab:
        vocab_list = scenario.get("vocabulary", [])
        if vocab_list:
            with st.expander(t("conv_vocab_exp"), expanded=False):
                chips = " ".join(
                    f"<span class='conv-vocab-chip'>{v['word']}"
                    f"<span class='conv-vocab-tr'> = {v['translation']}</span></span>"
                    for v in vocab_list
                )
                st.markdown(chips, unsafe_allow_html=True)

    st.markdown("")

    # ── Conversation history ───────────────────────────────────────────────
    for i, msg in enumerate(st.session_state.get("conv_history", [])):
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if voice_mode and msg["role"] == "assistant":
                if st.button("🔊", key=f"tts_replay_{i}", help=t("conv_voice_replay_help")):
                    audio_bytes = AIService.text_to_speech_bytes(msg["content"])
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        if msg["role"] == "user" and msg.get("feedback"):
            _render_feedback_card(msg["feedback"])

    # ── Auto-play TTS for latest AI response (set by _handle_input) ────────
    tts_text = st.session_state.pop("_voice_tts_text", None)
    if tts_text and voice_mode:
        with st.spinner("🔊"):
            audio_bytes = AIService.text_to_speech_bytes(tts_text)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)

    # ── Exit button (mobile-friendly, bottom of chat) ─────────────────────
    if st.button(t("btn_end_conversation"), key="conv_back_bottom", use_container_width=True):
        st.session_state.conv_scenario = None
        st.session_state.conv_history = []
        st.session_state.conv_total_xp = 0
        st.session_state.conv_voice_mode = False
        st.rerun()

    # ── Input area ─────────────────────────────────────────────────────────
    if voice_mode:
        _render_voice_input(engine)
    else:
        if user_input := st.chat_input("Auf Deutsch antworten... 🇩🇪"):
            _handle_input(user_input.strip(), engine)


def _save_active_conv() -> None:
    """Persist current conversation state so browser-redirect can restore it."""
    _sc = st.session_state.get("conv_scenario")
    if not _sc:
        return
    _ai_c = st.session_state.get("ai_cache", {})
    _hist = list(st.session_state.get("conv_history", []))
    _saved_len = len(_ai_c.get("__active_conv__", {}).get("history", []))
    if _saved_len != len(_hist) or _ai_c.get("__active_conv__", {}).get("scenario", {}).get("id") != _sc.get("id"):
        _ai_c["__active_conv__"] = {
            "scenario": _sc,
            "history": _hist,
            "total_xp": st.session_state.get("conv_total_xp", 0),
        }
        st.session_state.ai_cache = _ai_c
        persist_current_user()


def _render_voice_input(engine: ConversationEngine) -> None:
    ai = get_ai_service()

    # ── Pending transcription: waiting for user confirmation ──────────────
    pending = st.session_state.get("conv_voice_pending")
    if pending is not None:
        if pending:
            st.markdown(
                f"<div style='padding:0.8rem 1rem;background:#eff6ff;border:1.5px solid #3b82f6;"
                f"border-radius:10px;font-size:1rem;margin-bottom:0.5rem'>"
                f"🎤 <strong>{pending}</strong></div>",
                unsafe_allow_html=True,
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button(t("conv_voice_send"), type="primary", use_container_width=True, key="voice_send"):
                    text = pending
                    st.session_state.pop("conv_voice_pending", None)
                    st.session_state.pop("_voice_audio_hash", None)
                    st.session_state["_voice_attempt"] = st.session_state.get("_voice_attempt", 0) + 1
                    _handle_input(text, engine)
            with col2:
                if st.button(t("conv_voice_retry"), use_container_width=True, key="voice_retry"):
                    st.session_state.pop("conv_voice_pending", None)
                    st.session_state.pop("_voice_audio_hash", None)
                    st.session_state["_voice_attempt"] = st.session_state.get("_voice_attempt", 0) + 1
                    st.rerun()
        else:
            st.error(t("conv_voice_error"))
            if st.button(t("conv_voice_try_again"), key="voice_error_retry"):
                st.session_state.pop("conv_voice_pending", None)
                st.session_state.pop("_voice_audio_hash", None)
                st.session_state["_voice_attempt"] = st.session_state.get("_voice_attempt", 0) + 1
                st.rerun()
        return

    # ── Whisper mode (needs OPENAI_API_KEY) ───────────────────────────────
    if ai.has_whisper_key():
        attempt = st.session_state.get("_voice_attempt", 0)
        audio = st.audio_input(t("conv_voice_input_label"), key=f"voice_recorder_{attempt}")
        if audio is not None:
            audio_bytes = audio.read()
            audio_hash = hashlib.md5(audio_bytes).hexdigest()
            if st.session_state.get("_voice_audio_hash") != audio_hash:
                st.session_state["_voice_audio_hash"] = audio_hash
                with st.spinner(t("conv_voice_recognizing")):
                    text = ai.transcribe_audio(audio_bytes)
                st.session_state["conv_voice_pending"] = text or ""
                st.rerun()
        return

    # ── Free mode: browser Web Speech API (Chrome/Edge) ───────────────────
    st.caption(t("conv_voice_browser_hint"))

    # Save conv state NOW — before the JS redirect can cause a page reload.
    # On redirect, bootstrap_session restores ai_cache from DB, then reads __active_conv__.
    _save_active_conv()

    t_token = st.query_params.get("t", "")
    t_param = f"&t={t_token}" if t_token else ""

    _lbl_start     = t("conv_voice_btn_start")
    _lbl_listening = t("conv_voice_btn_listening")
    _lbl_speaking  = t("conv_voice_speaking_hint")
    _lbl_nosupport = t("conv_voice_no_support")
    _err_nospeech  = t("conv_voice_err_nospeech")
    _err_nomic     = t("conv_voice_err_nomic")
    _err_perm      = t("conv_voice_err_perm")
    _err_network   = t("conv_voice_err_network")

    _components.html(
        f"""
<html>
<head>
<style>
  body {{ margin: 0; font-family: sans-serif; }}
  #btn {{
    width: 100%; padding: 12px; border-radius: 24px; border: none;
    background: #4a90d9; color: white; font-size: 1rem; cursor: pointer;
    transition: background 0.2s;
  }}
  #btn.listening {{ background: #e74c3c; }}
  #status {{ font-size: 0.85rem; color: #64748b; margin-top: 6px; min-height: 20px; }}
  #error  {{ font-size: 0.85rem; color: #e74c3c; margin-top: 4px; }}
</style>
</head>
<body>
<button id="btn" onclick="toggle()">{_lbl_start}</button>
<div id="status"></div>
<div id="error"></div>
<script>
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SR) {{
  document.getElementById('btn').disabled = true;
  document.getElementById('btn').textContent = '{_lbl_nosupport}';
}} else {{
  const r = new SR();
  r.lang = 'de-DE';
  r.continuous = false;
  r.interimResults = false;
  let running = false;

  function toggle() {{
    if (running) {{ r.stop(); return; }}
    r.start();
  }}

  r.onstart = () => {{
    running = true;
    document.getElementById('btn').textContent = '{_lbl_listening}';
    document.getElementById('btn').className = 'listening';
    document.getElementById('status').textContent = '{_lbl_speaking}';
    document.getElementById('error').textContent = '';
  }};

  r.onend = () => {{
    running = false;
    document.getElementById('btn').textContent = '{_lbl_start}';
    document.getElementById('btn').className = '';
  }};

  r.onresult = (event) => {{
    const text = event.results[0][0].transcript;
    document.getElementById('status').textContent = '✓ ' + text;
    const encoded = encodeURIComponent(text);
    window.parent.location.href = window.parent.location.pathname + '?_v=' + encoded + '{t_param}';
  }};

  r.onerror = (e) => {{
    running = false;
    document.getElementById('btn').className = '';
    document.getElementById('btn').textContent = '{_lbl_start}';
    const msgs = {{
      'no-speech': '{_err_nospeech}',
      'audio-capture': '{_err_nomic}',
      'not-allowed': '{_err_perm}',
      'network': '{_err_network}',
    }};
    document.getElementById('error').textContent = msgs[e.error] || 'Error: ' + e.error;
  }};
}}
</script>
</body>
</html>
""",
        height=100,
        scrolling=False,
    )


def _handle_input(user_input: str, engine: ConversationEngine) -> None:
    if not user_input:
        return

    # Render user bubble immediately (visible in this render pass)
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # AI call
    history_snapshot = list(st.session_state.get("conv_history", []))
    with st.spinner("💭"):
        result = engine.send_message(user_input, history_snapshot)

    feedback = {
        "correction": result["correction"],
        "explanation": result["explanation"],
        "vocab": result["vocab"],
        "xp": result["xp"],
        "is_correct": result["is_correct"],
    }

    # Render feedback and AI reply immediately
    _render_feedback_card(feedback)
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(result["reply"])

    # Queue TTS for auto-play on next render (only in voice mode)
    if st.session_state.get("conv_voice_mode"):
        st.session_state["_voice_tts_text"] = result["reply"]

    # Persist to history (after rendering to avoid double display in this pass)
    st.session_state.conv_history.append({
        "role": "user",
        "content": user_input,
        "feedback": feedback,
    })
    st.session_state.conv_history.append({
        "role": "assistant",
        "content": result["reply"],
        "feedback": None,
    })

    # Gamification
    add_xp(result["xp"])
    st.session_state.conv_total_xp = (
        st.session_state.get("conv_total_xp", 0) + result["xp"]
    )

    # Milestone: balloons on 5th message in a session
    user_count = sum(
        1 for m in st.session_state.conv_history if m["role"] == "user"
    )
    if user_count == 5:
        st.balloons()

    if result["is_correct"]:
        st.toast(t("toast_perfect_german", n=result["xp"]), icon="🎉")
    else:
        st.toast(t("toast_correction", n=result["xp"]))

    # Keep conv state in ai_cache so browser voice redirect can restore it
    if st.session_state.get("conv_voice_mode"):
        _ai_c = st.session_state.get("ai_cache", {})
        _ai_c["__active_conv__"] = {
            "scenario": st.session_state.get("conv_scenario"),
            "history": st.session_state.conv_history,
            "total_xp": st.session_state.get("conv_total_xp", 0),
        }
        st.session_state.ai_cache = _ai_c

    persist_current_user()


# ── Feedback card ─────────────────────────────────────────────────────────

def _render_feedback_card(feedback: dict) -> None:
    is_correct = feedback.get("is_correct", True)
    correction = feedback.get("correction")
    explanation = feedback.get("explanation", "")
    vocab = feedback.get("vocab", [])
    xp = feedback.get("xp", 0)

    css_cls = "conv-feedback-ok" if is_correct else "conv-feedback-fix"
    hdr_cls = "conv-feedback-header-ok" if is_correct else "conv-feedback-header-fix"
    icon = "✅" if is_correct else "💡"
    header = t("conv_feedback_ok") if is_correct else t("conv_feedback_fix")

    parts: list[str] = [
        f"<p class='{hdr_cls}'>{icon} {header}</p>"
    ]

    if not is_correct and correction:
        parts.append(
            f"<p style='margin:0 0 3px;font-size:0.87rem'>"
            f"<strong>{t('conv_better_label')}</strong> <em>{correction}</em></p>"
        )
    if not is_correct and explanation:
        parts.append(
            f"<p style='margin:0;font-size:0.82rem;color:#64748b'>{explanation}</p>"
        )

    if vocab:
        chips = " ".join(
            f"<span class='conv-vocab-chip'>{v['word']}"
            f"<span class='conv-vocab-tr'> = {v['translation']}</span></span>"
            for v in vocab
        )
        parts.append(f"<div style='margin-top:7px'>{chips}</div>")

    parts.append(f"<div><span class='conv-xp-pill'>+{xp} XP</span></div>")

    st.markdown(
        f"<div class='conv-feedback {css_cls}'>{''.join(parts)}</div>",
        unsafe_allow_html=True,
    )
