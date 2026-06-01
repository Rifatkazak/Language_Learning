import difflib
import random
import streamlit as st
from core.i18n import t
from services.ai_service import get_ai_service
from services.gamification import add_xp
from storage.user_store import persist_current_user

GRAMMAR_TOPICS = [
    ("nominativ",            "kasus",  "Nominativ"),
    ("akkusativ",            "kasus",  "Akkusativ"),
    ("dativ",                "kasus",  "Dativ"),
    ("genitiv",              "kasus",  "Genitiv"),
    ("prasens",              "zeit",   "Präsens"),
    ("perfekt_gr",           "zeit",   "Perfekt"),
    ("prateritum_gr",        "zeit",   "Präteritum"),
    ("futur1",               "zeit",   "Futur I"),
    ("modalverben",          "verben", "Modalverben"),
    ("konjunktiv2",          "verben", "Konjunktiv II"),
    ("passiv",               "verben", "Passiv"),
    ("trennbare_verben",     "verben", "Trennbare Verben"),
    ("adjektivdeklination",  "sonst",  "Adjektivdeklination"),
    ("relativsatze",         "sonst",  "Relativsätze"),
    ("wechselprapositionen", "sonst",  "Wechselpräpositionen"),
    ("baglac_koord",   "baglac", "und / aber / oder / denn / sondern"),
    ("baglac_subord",  "baglac", "weil / dass / wenn / ob / damit"),
    ("baglac_temp",    "baglac", "als / wenn / bevor / nachdem / während"),
    ("baglac_konzess", "baglac", "obwohl / trotzdem / jedoch / dennoch"),
]

GROUPS = ["kasus", "zeit", "verben", "sonst", "baglac"]

# Built-in reference cards: (bağlaç, yapı, tr_anlam, en_meaning)
CONJUNCTION_DATA: dict[str, list[tuple[str, str, str, str]]] = {
    "baglac_koord": [
        ("und",     "A und B",            "ve",                    "and"),
        ("aber",    "A, aber B",          "ama / fakat",           "but"),
        ("oder",    "A oder B",           "veya / ya da",          "or"),
        ("denn",    "A, denn B  (V2)",    "çünkü (ana cümle)",     "because (main clause)"),
        ("sondern", "nicht A, sondern B", "aksine / bilakis",      "but rather"),
    ],
    "baglac_subord": [
        ("weil",   "…, weil + verb-final",  "çünkü (yan cümle)",       "because (sub. clause)"),
        ("dass",   "…, dass + verb-final",  "…olduğu / ki",            "that"),
        ("wenn",   "…, wenn + verb-final",  "eğer / …dığında",         "if / when"),
        ("ob",     "…, ob + verb-final",    "…olup olmadığı",          "whether"),
        ("damit",  "…, damit + verb-final", "…için / -sın diye",       "so that"),
        ("da",     "…, da + verb-final",    "…olduğundan",             "since / as"),
    ],
    "baglac_temp": [
        ("als",     "…, als + verb-final",     "…dığında (geçmiş, tek seferlik)", "when (past, one-time)"),
        ("wenn",    "…, wenn + verb-final",    "…dığında (şimdi / tekrar)",       "when (present / repeated)"),
        ("bevor",   "…, bevor + verb-final",   "…den önce",                       "before"),
        ("nachdem", "…, nachdem + verb-final", "…den sonra",                      "after"),
        ("während", "…, während + verb-final", "…iken / -rken",                   "while"),
        ("seitdem", "…, seitdem + verb-final", "…den beri",                       "since (time)"),
    ],
    "baglac_konzess": [
        ("obwohl",   "…, obwohl + verb-final",  "her ne kadar…-se de",        "although"),
        ("obgleich", "…, obgleich + verb-final", "her ne kadar (resmi dil)",   "although (formal)"),
        ("trotzdem", "S1. Trotzdem + V2",        "buna rağmen",                "nevertheless"),
        ("jedoch",   "S1, jedoch + V2",          "bununla birlikte / ancak",   "however"),
        ("dennoch",  "S1. Dennoch + V2",         "yine de / buna karşın",      "yet / still"),
    ],
}

_BAGLAC_TITLE = {
    "baglac_koord":   ("Sıralayan / Koordinierende Konjunktionen", "Coordinating Conjunctions"),
    "baglac_subord":  ("Bağımlı / Subordinierende Konjunktionen",  "Subordinating Conjunctions"),
    "baglac_temp":    ("Zaman / Temporale Konjunktionen",          "Temporal Conjunctions"),
    "baglac_konzess": ("Karşıt / Konzessive Konjunktionen",        "Concessive Conjunctions"),
}


def _topic_de(tid: str) -> str:
    return next((tde for t_id, _, tde in GRAMMAR_TOPICS if t_id == tid), tid)


def _render_conjunction_card(tid: str) -> None:
    data = CONJUNCTION_DATA.get(tid)
    if not data:
        return
    lang = st.session_state.get("ui_lang", "tr")
    titles = _BAGLAC_TITLE.get(tid, ("Bağlaçlar", "Conjunctions"))
    title = titles[1] if lang == "en" else titles[0]
    col_head = "Anlam" if lang == "tr" else "Meaning"
    structure_head = "Yapı" if lang == "tr" else "Structure"
    st.markdown(f"#### 🔗 {title}")
    rows = [
        f"| Bağlaç | {structure_head} | {col_head} |",
        "|--------|-----------------|------|",
    ]
    for conj, usage, tr_m, en_m in data:
        meaning = tr_m if lang == "tr" else en_m
        rows.append(f"| **{conj}** | `{usage}` | {meaning} |")
    st.markdown("\n".join(rows))


def render(words: list, custom_words: list) -> None:
    st.markdown(t("grammar_title"))
    st.caption(t("grammar_subtitle"))

    tab_lesson, tab_quiz = st.tabs([t("grammar_tab_lesson"), t("grammar_tab_quiz")])
    with tab_lesson:
        _render_lesson(words, custom_words)
    with tab_quiz:
        _render_quiz(words, custom_words)


# ─── LESSON ───────────────────────────────────────────────────────────────────

def _render_lesson(words: list, custom_words: list) -> None:
    ai_cache = st.session_state.get("ai_cache", {})
    group_labels = [t(f"grammar_group_{g}") for g in GROUPS]
    group_tabs = st.tabs(group_labels)

    for tab, group in zip(group_tabs, GROUPS):
        with tab:
            group_topics = [(tid, tde) for tid, tg, tde in GRAMMAR_TOPICS if tg == group]
            cols = st.columns(2)
            for i, (tid, tde) in enumerate(group_topics):
                with cols[i % 2]:
                    is_cached = f"grammar_{tid}" in ai_cache
                    label = f"✅ {tde}" if is_cached else tde
                    if st.button(label, key=f"gram_{tid}", use_container_width=True):
                        st.session_state["grammar_selected_topic"] = tid
                        st.rerun()

    selected_tid = st.session_state.get("grammar_selected_topic")
    if not selected_tid:
        st.info(t("grammar_select_hint"))
        return

    topic_de = _topic_de(selected_tid)
    cache_key = f"grammar_{selected_tid}"

    st.markdown("---")
    st.markdown(f"### 📖 {topic_de}")

    _render_conjunction_card(selected_tid)

    if cache_key in ai_cache:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.caption(t("grammar_cached_note"))
        with col2:
            if st.button(t("grammar_regenerate"), key="gram_regen"):
                del ai_cache[cache_key]
                st.session_state["ai_cache"] = ai_cache
                persist_current_user()
                st.rerun()
        st.markdown(ai_cache[cache_key])
    else:
        if st.button(t("grammar_btn_generate"), type="primary", key="gram_generate"):
            all_words = words + custom_words
            sample = random.sample(all_words, min(12, len(all_words)))
            with st.spinner(t("grammar_spinner")):
                ai = get_ai_service()
                lesson = ai.generate_grammar_lesson(selected_tid, topic_de, sample)
                if lesson:
                    ai_cache[cache_key] = lesson
                    st.session_state["ai_cache"] = ai_cache
                    persist_current_user()
                    st.rerun()
                else:
                    st.toast(t("toast_ai_unavailable"), icon="⚠️")


# ─── QUIZ ─────────────────────────────────────────────────────────────────────

def _render_quiz(words: list, custom_words: list) -> None:
    if st.session_state.get("grammar_quiz_questions"):
        _render_quiz_play()
    else:
        _render_quiz_setup(words, custom_words)


_MIXED_ID = "__mixed__"


def _mixed_topics_str() -> tuple[str, str]:
    """Returns (display_label, topics_for_ai) for mixed mode."""
    chosen = []
    for group in GROUPS:
        group_topics = [(tid, tde) for tid, tg, tde in GRAMMAR_TOPICS if tg == group]
        if group_topics:
            chosen.append(random.choice(group_topics))
    topics_str = ", ".join(tde for _, tde in chosen)
    return t("grammar_quiz_mixed"), topics_str


def _render_quiz_setup(words: list, custom_words: list) -> None:
    st.markdown(t("grammar_quiz_intro"))

    mixed_label = t("grammar_quiz_mixed")
    all_opts = [(_MIXED_ID, mixed_label)] + [(tid, tde) for tid, _, tde in GRAMMAR_TOPICS]
    topic_labels = [tde for _, tde in all_opts]

    sel_idx = st.selectbox(
        t("grammar_quiz_topic_label"),
        range(len(topic_labels)),
        format_func=lambda i: topic_labels[i],
        key="gram_quiz_topic_sel",
    )
    tid, tde = all_opts[sel_idx]

    quiz_type = st.radio(
        t("grammar_quiz_type_label"),
        ["mc", "write"],
        format_func=lambda x: t("grammar_quiz_mc") if x == "mc" else t("grammar_quiz_write"),
        horizontal=True,
        key="gram_quiz_type_radio",
    )

    if st.button(t("grammar_quiz_start_btn"), type="primary", key="gram_quiz_start"):
        all_words = words + custom_words
        sample = random.sample(all_words, min(10, len(all_words)))

        if tid == _MIXED_ID:
            display_label, topics_for_ai = _mixed_topics_str()
            quiz_topic_id = _MIXED_ID
        else:
            display_label, topics_for_ai = tde, tde
            quiz_topic_id = tid

        with st.spinner(t("grammar_quiz_spinner")):
            ai = get_ai_service()
            qs = ai.generate_grammar_quiz(quiz_topic_id, topics_for_ai, sample, quiz_type)
            if qs:
                st.session_state["grammar_quiz_questions"] = qs
                st.session_state["grammar_quiz_idx"] = 0
                st.session_state["grammar_quiz_session"] = {"correct": 0, "wrong": 0}
                st.session_state["grammar_quiz_type"] = quiz_type
                st.session_state["grammar_quiz_topic"] = (quiz_topic_id, display_label)
                st.session_state["grammar_quiz_answered"] = False
                st.session_state["grammar_quiz_correct"] = None
                st.rerun()
            else:
                st.toast(t("toast_ai_unavailable"), icon="⚠️")


def _render_quiz_play() -> None:
    questions = st.session_state.get("grammar_quiz_questions", [])
    idx = st.session_state.get("grammar_quiz_idx", 0)
    sess = st.session_state.get("grammar_quiz_session", {"correct": 0, "wrong": 0})
    quiz_type = st.session_state.get("grammar_quiz_type", "mc")
    _, tde = st.session_state.get("grammar_quiz_topic") or ("", "")
    answered = st.session_state.get("grammar_quiz_answered", False)
    is_correct = st.session_state.get("grammar_quiz_correct", None)

    if idx >= len(questions):
        _render_quiz_end(sess)
        return

    q = questions[idx]
    total = len(questions)

    st.progress(idx / total)
    st.caption(t("grammar_quiz_progress", i=idx + 1, tot=total, c=sess["correct"], w=sess["wrong"]))
    st.markdown(f"**{t('grammar_quiz_topic_header')}: {tde}**")
    st.markdown(f"### {q['question']}")

    if quiz_type == "mc":
        options = q.get("options", [])
        if not answered:
            cols = st.columns(2)
            for i, opt in enumerate(options):
                with cols[i % 2]:
                    if st.button(opt, key=f"gq_opt_{idx}_{i}", use_container_width=True):
                        correct = (opt.strip() == q["answer"].strip())
                        sess["correct" if correct else "wrong"] += 1
                        st.session_state["grammar_quiz_session"] = sess
                        st.session_state["grammar_quiz_answered"] = True
                        st.session_state["grammar_quiz_correct"] = correct
                        st.rerun()
        else:
            if is_correct:
                st.success(t("grammar_quiz_correct"))
            else:
                st.error(t("grammar_quiz_wrong", answer=q["answer"]))
            if q.get("explanation"):
                st.info(f"💡 {q['explanation']}")
            is_last = idx + 1 >= total
            lbl = t("grammar_quiz_finish_btn") if is_last else t("grammar_quiz_next_btn")
            if st.button(lbl, type="primary", key=f"gq_next_{idx}"):
                st.session_state["grammar_quiz_idx"] = idx + 1
                st.session_state["grammar_quiz_answered"] = False
                st.session_state["grammar_quiz_correct"] = None
                st.rerun()
    else:
        if not answered:
            user_ans = st.text_input(
                t("grammar_quiz_write_label"),
                key=f"gq_write_{idx}",
                placeholder=t("grammar_quiz_write_placeholder"),
            )
            if st.button(t("grammar_quiz_check_btn"), key=f"gq_check_{idx}"):
                correct_ans = q["answer"].strip().lower()
                user_clean = user_ans.strip().lower()
                ratio = difflib.SequenceMatcher(None, user_clean, correct_ans).ratio()
                correct = ratio >= 0.75
                sess["correct" if correct else "wrong"] += 1
                st.session_state["grammar_quiz_session"] = sess
                st.session_state["grammar_quiz_answered"] = True
                st.session_state["grammar_quiz_correct"] = correct
                st.session_state[f"gq_user_ans_{idx}"] = user_ans
                st.rerun()
        else:
            user_ans = st.session_state.get(f"gq_user_ans_{idx}", "")
            st.text_input(
                t("grammar_quiz_write_label"), value=user_ans,
                disabled=True, key=f"gq_write_dis_{idx}",
            )
            if is_correct:
                st.success(t("grammar_quiz_correct"))
            else:
                st.warning(t("grammar_quiz_write_answer", answer=q["answer"]))
            if q.get("explanation"):
                st.info(f"💡 {q['explanation']}")
            is_last = idx + 1 >= total
            lbl = t("grammar_quiz_finish_btn") if is_last else t("grammar_quiz_next_btn")
            if st.button(lbl, type="primary", key=f"gq_next_w_{idx}"):
                st.session_state["grammar_quiz_idx"] = idx + 1
                st.session_state["grammar_quiz_answered"] = False
                st.session_state["grammar_quiz_correct"] = None
                st.rerun()

    st.markdown("---")
    if st.button(t("grammar_quiz_quit_btn"), key="gq_quit"):
        st.session_state["grammar_quiz_questions"] = []
        st.session_state["grammar_quiz_idx"] = 0
        st.rerun()


def _render_quiz_end(sess: dict) -> None:
    total = sess["correct"] + sess["wrong"]
    pct = int(sess["correct"] / total * 100) if total else 0
    bonus = 20 if pct >= 80 else 10 if pct >= 50 else 5
    add_xp(bonus)
    persist_current_user()

    st.markdown(t("grammar_quiz_done"))
    c1, c2, c3 = st.columns(3)
    c1.metric(t("metric_correct"), sess["correct"])
    c2.metric(t("metric_wrong"), sess["wrong"])
    c3.metric(t("metric_bonus_xp"), f"+{bonus}")
    if total:
        st.progress(sess["correct"] / total)
    if st.button(t("grammar_quiz_again_btn"), type="primary"):
        st.session_state["grammar_quiz_questions"] = []
        st.session_state["grammar_quiz_idx"] = 0
        st.rerun()
    if st.button(t("btn_go_home")):
        from core.session import PAGE_HOME
        st.session_state["grammar_quiz_questions"] = []
        st.session_state["grammar_quiz_idx"] = 0
        st.session_state.page = PAGE_HOME
        st.rerun()
