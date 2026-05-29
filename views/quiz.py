import streamlit as st
from models.word import get_translation, get_display
from services.game_engine import start_quiz, make_quiz_question
from services.progress import save_progress, filtered_words
from services.gamification import add_xp, update_task_progress, check_achievements, show_achievement_popup
from storage.user_store import persist_current_user
from core.session import PAGE_HOME
from core.i18n import t
from core.topics import display_group_name


def render(words: list, custom_words: list) -> None:
    st.markdown(t("quiz_title"))

    if not st.session_state.quiz_deck:
        _render_start_screen(words, custom_words)
    else:
        _render_question(words, custom_words)


def _render_start_screen(words, custom_words):
    pool = filtered_words(words, custom_words, ignore_search=True)

    # Group filter
    groups = st.session_state.get("word_groups", {})
    if groups:
        all_words_label = t("all_words_group")
        group_keys = list(groups.keys())
        group_display = [all_words_label] + [display_group_name(k) for k in group_keys]
        saved_key = st.session_state.get("quiz_active_group")
        saved_display = display_group_name(saved_key) if saved_key else all_words_label
        if saved_display not in group_display:
            saved_display = all_words_label
        sel_display = st.selectbox(t("group_filter_label"), group_display, index=group_display.index(saved_display), key="quiz_grp_sel")
        if sel_display == all_words_label:
            st.session_state["quiz_active_group"] = None
        else:
            sel_key = group_keys[group_display.index(sel_display) - 1]
            st.session_state["quiz_active_group"] = sel_key
            gwords = set(groups.get(sel_key, []))
            pool = [w for w in pool if w["word"] in gwords]

    mixed_label = t("quiz_opt_mixed")
    opts = [mixed_label, "Verb", "Nomen", "Adj/Adv"]
    saved = st.session_state.get("quiz_filter_type", mixed_label)
    if saved not in opts:
        saved = mixed_label
    qopt = st.selectbox(t("quiz_type_select"), opts, index=opts.index(saved))
    if qopt != st.session_state.get("quiz_filter_type"):
        st.session_state["quiz_filter_type"] = qopt

    include_untr = st.checkbox(
        t("include_untranslated"),
        value=st.session_state.get("quiz_include_untranslated", False),
    )
    st.session_state["quiz_include_untranslated"] = include_untr

    def word_count(wtype):
        return sum(
            1 for w in pool if w.get("type") == wtype and
            (include_untr or get_translation(w["word"], words, custom_words) not in ("Çeviri yok", "—"))
        )

    if qopt == mixed_label:
        counts = {wt: word_count(wt) for wt in ("Verb", "Nomen", "Adj/Adv")}
        comp_def = st.session_state.get("quiz_comp") or {"Verb": 0, "Nomen": 0, "Adj/Adv": 0}
        qv1 = st.number_input(t("quiz_verb_count"),    min_value=0, max_value=counts["Verb"],    value=int(comp_def.get("Verb", 0)))
        qv2 = st.number_input(t("quiz_nomen_count"),   min_value=0, max_value=counts["Nomen"],   value=int(comp_def.get("Nomen", 0)))
        qv3 = st.number_input(t("quiz_adjadv_count"),  min_value=0, max_value=counts["Adj/Adv"], value=int(comp_def.get("Adj/Adv", 0)))
        q_total = qv1 + qv2 + qv3
        if q_total:
            st.markdown(t("quiz_total_selected", q=q_total))
        col1, col2 = st.columns(2)
        with col1:
            if st.button(t("btn_quiz_custom")):
                st.session_state["quiz_comp"] = {"Verb": qv1, "Nomen": qv2, "Adj/Adv": qv3} if q_total else None
                start_quiz(words, custom_words)
                st.rerun()
        with col2:
            if st.button(t("btn_quiz_mixed"), type="primary"):
                st.session_state["quiz_comp"] = None
                start_quiz(words, custom_words)
                st.rerun()
    else:
        cnt = word_count(qopt)
        st.markdown(t("quiz_type_available", type=qopt, cnt=cnt))
        if st.button(t("btn_quiz_type", type=qopt), type="primary", use_container_width=True):
            st.session_state["quiz_comp"] = None
            start_quiz(words, custom_words)
            st.rerun()


def _render_question(words, custom_words):
    idx = st.session_state.quiz_idx
    deck = st.session_state.quiz_deck
    sess = st.session_state.quiz_session
    qs = st.session_state.quiz_state

    if qs is None or idx >= len(deck):
        _render_result(words, custom_words, deck, sess)
        return

    word = qs["word"]
    display = get_display(word)
    translation = get_translation(word["word"], words, custom_words)

    st.progress(idx / len(deck))
    st.caption(t("quiz_progress_caption", idx=idx + 1, total=len(deck), c=sess["correct"], w=sess["wrong"]))
    st.markdown(t("quiz_question_prompt"))
    art_color = {"der": "🔵", "die": "🔴", "das": "🟢", "": ""}
    art_ic = art_color.get(word.get("article", ""), "")
    st.markdown(f"## {art_ic} {display}  `{word['type']}`")
    st.markdown("---")

    answered = qs.get("answered")
    for opt in qs["options"]:
        opt_tr = get_translation(opt["word"], words, custom_words)
        if opt_tr in ("—", "Çeviri yok"):
            opt_tr = opt["word"]
        is_correct_opt = opt["word"] == word["word"]
        is_chosen = answered == opt["word"]

        if answered is None:
            if st.button(opt_tr, use_container_width=True, key=f"opt_{opt['word']}_{idx}"):
                correct = opt["word"] == word["word"]
                qs["answered"] = opt["word"]
                qs["correct"] = correct
                if correct:
                    sess["correct"] += 1
                else:
                    sess["wrong"] += 1
                save_progress(word["word"], "easy" if correct else "hard")
                update_task_progress("quiz")
                st.rerun()
        else:
            if is_correct_opt:
                st.success(f"✅ {opt_tr}")
            elif is_chosen:
                st.error(f"❌ {opt_tr}  ← seçtiğiniz")
            else:
                st.button(opt_tr, use_container_width=True, disabled=True, key=f"opt_d_{opt['word']}_{idx}")

    if answered:
        if qs["correct"]:
            st.success(t("quiz_correct"))
        else:
            st.error(t("quiz_wrong_answer", answer=translation))
        if st.button(t("btn_next_question"), type="primary"):
            st.session_state.quiz_idx += 1
            make_quiz_question(words, custom_words)
            st.rerun()


def _render_result(words, custom_words, deck, sess):
    total_q = len(deck)
    score = sess["correct"]
    pct = int(score / total_q * 100) if total_q else 0
    emoji = "🏆" if pct >= 80 else "💪" if pct >= 50 else "📚"

    # Completion bonus (only awarded once per session)
    if not st.session_state.get("quiz_bonus_awarded"):
        bonus = 50 if pct >= 80 else 25 if pct >= 50 else 10
        per_q_xp = score * 10 + sess["wrong"] * 3
        add_xp(bonus)
        new_badges = check_achievements()
        show_achievement_popup(new_badges)
        persist_current_user()
        st.session_state["quiz_bonus_awarded"] = True
        st.session_state["quiz_last_bonus"] = bonus
        st.session_state["quiz_last_per_q"] = per_q_xp

    bonus = st.session_state.get("quiz_last_bonus", 0)
    per_q_xp = st.session_state.get("quiz_last_per_q", 0)
    total_earned = per_q_xp + bonus

    st.markdown(t("quiz_done", emoji=emoji))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("metric_correct"), sess["correct"])
    c2.metric(t("metric_wrong"), sess["wrong"])
    c3.metric(t("metric_score"), f"%{pct}")
    c4.metric(t("metric_xp_earned"), f"+{total_earned}")
    st.progress(pct / 100)
    st.caption(t("quiz_xp_breakdown", pq=per_q_xp, b=bonus))

    if st.button(t("btn_try_again"), type="primary"):
        st.session_state.pop("quiz_bonus_awarded", None)
        start_quiz(words, custom_words)
        st.rerun()
    if st.button(t("btn_go_home")):
        st.session_state.pop("quiz_bonus_awarded", None)
        st.session_state.page = PAGE_HOME
        st.rerun()
