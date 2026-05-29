import streamlit as st
from services.scenario_service import load_scenarios, get_categories
from services.conversation_engine import ConversationEngine
from services.gamification import add_xp
from storage.user_store import persist_current_user


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
    st.markdown("# 🗣️ AI Konuşma Antrenörü")
    st.markdown(
        "Gerçek Almanya senaryolarında AI ile pratik yapın. "
        "Bir senaryo seçin ve konuşmaya başlayın!"
    )
    st.divider()

    categories = get_categories()
    cat_labels = ["Tümü"] + [c["name_tr"] for c in categories]

    selected_label = st.radio(
        "Kategori:",
        cat_labels,
        horizontal=True,
        key="conv_cat_filter",
        label_visibility="collapsed",
    )
    st.markdown("")

    all_scenarios = load_scenarios()
    if selected_label != "Tümü":
        cat_id = next(
            (c["id"] for c in categories if c["name_tr"] == selected_label),
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
        st.info("Bu kategoride senaryo bulunamadı.")
        return

    cols = st.columns(2, gap="medium")
    for i, sc in enumerate(filtered):
        with cols[i % 2]:
            _render_scenario_card(sc)


def _render_scenario_card(sc: dict) -> None:
    level_color = "#4a90d9" if "B1" in sc.get("cefr_level", "") else "#27ae60"
    context_snippet = sc.get("context_tr", "")[:90]
    if len(sc.get("context_tr", "")) > 90:
        context_snippet += "…"
    st.markdown(
        f"""<div class="conv-card">
            <div class="conv-card-icon">{sc.get('icon', '💬')}</div>
            <div class="conv-card-title">{sc['title']}</div>
            <div class="conv-card-sub">{sc.get('title_tr', '')}</div>
            <div style="margin:4px 0 7px">
                <span class="conv-badge"
                      style="border-color:{level_color};color:{level_color}">
                    {sc.get('cefr_level', 'B1')}
                </span>
                <span class="conv-cat-badge">{sc.get('category_tr', '')}</span>
            </div>
            <div class="conv-card-goal">{context_snippet}</div>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button(
        f"Başla → {sc['title']}",
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
            f"{scenario.get('title_tr', '')} • "
            f"{scenario.get('cefr_level', 'B1')} • "
            f"Siz: **{scenario.get('user_role', '')}**"
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
            f"<small style='color:#64748b'>{user_msgs} mesaj</small></div>",
            unsafe_allow_html=True,
        )

    if st.button("⬅ Senaryo Değiştir", key="conv_back", use_container_width=True):
        st.session_state.conv_scenario = None
        st.session_state.conv_history = []
        st.session_state.conv_total_xp = 0
        st.rerun()


def _render_chat(scenario: dict) -> None:
    engine = ConversationEngine(scenario)

    # ── Reference panels ──────────────────────────────────────────────────
    col_info, col_vocab = st.columns(2)
    with col_info:
        with st.expander("ℹ️ Senaryo Bağlamı", expanded=False):
            st.markdown(scenario.get("context_tr", ""))
            st.markdown(f"**Rolünüz:** {scenario.get('user_role', '')}")
            st.markdown(f"**AI Rolü:** {scenario.get('ai_role', '')}")
    with col_vocab:
        vocab_list = scenario.get("vocabulary", [])
        if vocab_list:
            with st.expander("📖 Senaryo Sözlüğü", expanded=False):
                chips = " ".join(
                    f"<span class='conv-vocab-chip'>{v['word']}"
                    f"<span class='conv-vocab-tr'> = {v['translation']}</span></span>"
                    for v in vocab_list
                )
                st.markdown(chips, unsafe_allow_html=True)

    st.markdown("")

    # ── Conversation history ───────────────────────────────────────────────
    for msg in st.session_state.get("conv_history", []):
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
        if msg["role"] == "user" and msg.get("feedback"):
            _render_feedback_card(msg["feedback"])

    # ── Exit button (mobile-friendly, bottom of chat) ─────────────────────
    if st.button("⬅ Konuşmayı Bitir / Senaryo Değiştir", key="conv_back_bottom", use_container_width=True):
        st.session_state.conv_scenario = None
        st.session_state.conv_history = []
        st.session_state.conv_total_xp = 0
        st.rerun()

    # ── New user input ─────────────────────────────────────────────────────
    if user_input := st.chat_input("Auf Deutsch antworten... 🇩🇪"):
        _handle_input(user_input.strip(), engine)


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
        st.toast(f"✅ Mükemmel Almanca! +{result['xp']} XP", icon="🎉")
    else:
        st.toast(f"📝 Düzeltme var. +{result['xp']} XP")

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
    header = "Harika Almanca!" if is_correct else "Küçük Düzeltme"

    parts: list[str] = [
        f"<p class='{hdr_cls}'>{icon} {header}</p>"
    ]

    if not is_correct and correction:
        parts.append(
            f"<p style='margin:0 0 3px;font-size:0.87rem'>"
            f"<strong>Daha iyi:</strong> <em>{correction}</em></p>"
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
