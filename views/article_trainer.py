import random
import streamlit as st

from services.gamification import add_xp
from services.ai_service import get_ai_service
from storage.user_store import persist_current_user
from models.word import get_translation
from core.i18n import t


_CASES = ["Nominativ", "Akkusativ", "Dativ"]


def render(words: list, custom_words: list) -> None:
    st.markdown("# 🎯 Artikel Trainer")
    st.caption(t("article_subtitle"))

    nomen_pool = [w for w in (words + custom_words) if w.get("type") == "Nomen" and w.get("article")]
    if len(nomen_pool) < 3:
        st.warning(t("article_no_nouns"))
        return

    tab1, tab2 = st.tabs([t("tab_artikel_drill"), t("tab_kasus_quiz")])
    with tab1:
        _render_artikel_drill(nomen_pool)
    with tab2:
        _render_kasus_quiz(nomen_pool, words, custom_words)


# ── Artikel Drill ─────────────────────────────────────────────────────────────

def _init_drill():
    defaults = {
        "art_drill_word": None,
        "art_drill_answered": False,
        "art_drill_result": None,
        "art_drill_correct_count": 0,
        "art_drill_total_count": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _next_drill_word(pool: list) -> None:
    st.session_state.art_drill_word = random.choice(pool)
    st.session_state.art_drill_answered = False
    st.session_state.art_drill_result = None


def _render_artikel_drill(pool: list) -> None:
    _init_drill()

    if st.session_state.art_drill_word is None:
        _next_drill_word(pool)

    w = st.session_state.art_drill_word
    correct_article = w.get("article", "").lower()
    total = st.session_state.art_drill_total_count
    correct = st.session_state.art_drill_correct_count
    pct = int(correct / total * 100) if total else 0

    c1, c2, c3 = st.columns(3)
    c1.metric(t("metric_question_num"), total)
    c2.metric(t("metric_correct_label"), correct)
    c3.metric(t("metric_success_label"), f"%{pct}")
    st.markdown("---")

    st.markdown(
        f"<div style='text-align:center;padding:2rem 1rem;"
        f"background:linear-gradient(135deg,#f8fafc,#e2e8f0);"
        f"border-radius:14px;margin-bottom:1.2rem;'>"
        f"<div style='font-size:0.85rem;color:#64748b;margin-bottom:0.4rem'>{t('article_drill_prompt')}</div>"
        f"<div style='font-size:2.6rem;font-weight:700;color:#1e293b'>___ {w['word']}</div>"
        f"<div style='font-size:0.95rem;color:#475569;margin-top:0.4rem'>"
        f"{w.get('translation','')}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    disabled = st.session_state.art_drill_answered
    b1, b2, b3 = st.columns(3)
    pressed = None
    with b1:
        if st.button("🔵 der", use_container_width=True, type="primary", disabled=disabled, key="art_der"):
            pressed = "der"
    with b2:
        if st.button("🔴 die", use_container_width=True, type="primary", disabled=disabled, key="art_die"):
            pressed = "die"
    with b3:
        if st.button("🟢 das", use_container_width=True, type="primary", disabled=disabled, key="art_das"):
            pressed = "das"

    if pressed is not None and not disabled:
        st.session_state.art_drill_total_count += 1
        if pressed == correct_article:
            st.session_state.art_drill_correct_count += 1
            st.session_state.art_drill_result = "correct"
            add_xp(5)
            persist_current_user()
        else:
            st.session_state.art_drill_result = "wrong"
        st.session_state.art_drill_answered = True
        st.rerun()

    if st.session_state.art_drill_answered:
        if st.session_state.art_drill_result == "correct":
            st.success(t("article_drill_correct", art=correct_article, word=w["word"]))
        else:
            st.error(t("article_drill_wrong", art=correct_article, word=w["word"]))

        if st.button(t("btn_next_arrow"), use_container_width=True, type="primary", key="art_next"):
            _next_drill_word(pool)
            st.rerun()


# ── Kasus Quiz ────────────────────────────────────────────────────────────────

def _init_kasus():
    defaults = {
        "kasus_word": None,
        "kasus_case": None,
        "kasus_data": None,
        "kasus_answered": False,
        "kasus_result": None,
        "kasus_correct_count": 0,
        "kasus_total_count": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _load_next_kasus(pool: list, words: list, custom_words: list) -> None:
    word = random.choice(pool)
    case = random.choice(_CASES)
    cache_key = f"kasus_{word['word']}_{case}"
    cache = st.session_state.get("ai_cache", {})

    if cache_key in cache and isinstance(cache[cache_key], dict):
        data = cache[cache_key]
    else:
        ai = get_ai_service()
        translation = word.get("translation") or get_translation(word["word"], words, custom_words)
        data = ai.generate_case_sentence(
            word=word["word"],
            article=word.get("article", ""),
            translation=translation,
            case=case,
        )
        if data:
            cache[cache_key] = data
            st.session_state.ai_cache = cache
            persist_current_user()

    st.session_state.kasus_word = word
    st.session_state.kasus_case = case
    st.session_state.kasus_data = data
    st.session_state.kasus_answered = False
    st.session_state.kasus_result = None


def _render_kasus_quiz(pool: list, words: list, custom_words: list) -> None:
    _init_kasus()

    ai = get_ai_service()
    if not ai.is_available():
        st.error(t("article_ai_inactive"))
        return

    total = st.session_state.kasus_total_count
    correct = st.session_state.kasus_correct_count
    pct = int(correct / total * 100) if total else 0
    c1, c2, c3 = st.columns(3)
    c1.metric(t("metric_question_num"), total)
    c2.metric(t("metric_correct_label"), correct)
    c3.metric(t("metric_success_label"), f"%{pct}")
    st.markdown("---")

    if st.session_state.kasus_word is None:
        with st.spinner(t("spinner_ai_sentence_kasus")):
            _load_next_kasus(pool, words, custom_words)
        st.rerun()

    data = st.session_state.kasus_data
    word = st.session_state.kasus_word
    case = st.session_state.kasus_case

    if data is None:
        st.warning(t("kasus_ai_failed"))
        if st.button(t("btn_retry"), type="primary", key="kasus_retry"):
            with st.spinner(t("spinner_retry")):
                _load_next_kasus(pool, words, custom_words)
            st.rerun()
        return

    full_word = f"{word.get('article','')} {word['word']}".strip()
    st.markdown(
        f"<div style='padding:1.4rem 1.2rem;"
        f"background:linear-gradient(135deg,#eff6ff,#dbeafe);"
        f"border-left:4px solid #4a90d9;border-radius:10px;margin-bottom:1rem;'>"
        f"<div style='font-size:0.78rem;color:#64748b;margin-bottom:0.3rem'>"
        f"Kelime: <strong>{full_word}</strong></div>"
        f"<div style='font-size:1.2rem;color:#1e293b;font-weight:600'>"
        f"{data['sentence']}</div>"
        f"<div style='font-size:0.85rem;color:#475569;margin-top:0.4rem;font-style:italic'>"
        f"🇹🇷 {data['translation']}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown(t("kasus_question", word=word["word"]))

    disabled = st.session_state.kasus_answered
    cols = st.columns(3)
    pressed = None
    for col, c in zip(cols, _CASES):
        with col:
            if st.button(c, use_container_width=True, type="primary", disabled=disabled, key=f"kasus_{c}"):
                pressed = c

    if pressed is not None and not disabled:
        st.session_state.kasus_total_count += 1
        if pressed == case:
            st.session_state.kasus_correct_count += 1
            st.session_state.kasus_result = "correct"
            add_xp(10)
            persist_current_user()
        else:
            st.session_state.kasus_result = "wrong"
        st.session_state.kasus_answered = True
        st.rerun()

    if st.session_state.kasus_answered:
        if st.session_state.kasus_result == "correct":
            st.success(t("kasus_correct", case=case))
        else:
            st.error(t("kasus_wrong", case=case))
        if data.get("explanation"):
            st.info(f"💡 {data['explanation']}")

        if st.button(t("btn_next_arrow"), use_container_width=True, type="primary", key="kasus_next"):
            with st.spinner(t("spinner_ai_sentence_kasus")):
                _load_next_kasus(pool, words, custom_words)
            st.rerun()
