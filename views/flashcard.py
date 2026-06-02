import streamlit as st
from models.word import get_translation, get_display
from services.game_engine import start_flash
from services.progress import save_progress, save_ai_example, filtered_words
from services.gamification import ACHIEVEMENTS, add_xp, check_achievements, show_achievement_popup
from storage.user_store import persist_current_user
from storage.word_repo import load_word_levels
from services.ai_service import get_ai_service
from ui.components import flashcard_front_html, flashcard_back_html
from core.session import PAGE_HOME, PAGE_FLASH
from core.i18n import t
from core.topics import display_group_name


def _trigger_tts(word_text: str) -> None:
    cache_key = f"tts_bytes_{word_text}"
    if cache_key not in st.session_state:
        audio = get_ai_service().text_to_speech_bytes(word_text)
        if audio:
            st.session_state[cache_key] = audio
        else:
            st.toast(t("toast_ai_unavailable"), icon="⚠️")
            return
    st.session_state["tts_play_word"] = word_text
    st.rerun()


def _render_tts_audio(word_text: str) -> None:
    if st.session_state.get("tts_play_word") == word_text:
        audio_bytes = st.session_state.get(f"tts_bytes_{word_text}")
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        del st.session_state["tts_play_word"]


def render(words: list, custom_words: list) -> None:
    st.markdown(t("flash_title"))

    global_filter = st.session_state.get("filter_type", "Tümü")
    if global_filter != "Tümü":
        st.info(t("flash_filter_active", filter=global_filter))

    if not st.session_state.flash_deck:
        _render_start_screen(words, custom_words, global_filter)
    else:
        _render_study(words, custom_words)


def _render_start_screen(words, custom_words, global_filter):
    st.info(t("flash_start_hint"))
    pool = filtered_words(words, custom_words, ignore_search=True)
    if global_filter != "Tümü":
        pool = [w for w in pool if w.get("type") == global_filter]

    # Group filter
    groups = st.session_state.get("word_groups", {})
    if groups:
        all_words_label = t("all_words_group")
        group_keys = list(groups.keys())
        group_display = [all_words_label] + [display_group_name(k) for k in group_keys]
        saved_key = st.session_state.get("flash_active_group")
        saved_display = display_group_name(saved_key) if saved_key else all_words_label
        if saved_display not in group_display:
            saved_display = all_words_label
        sel_display = st.selectbox(t("group_filter_label"), group_display, index=group_display.index(saved_display), key="flash_grp_sel")
        if sel_display == all_words_label:
            st.session_state["flash_active_group"] = None
        else:
            sel_key = group_keys[group_display.index(sel_display) - 1]
            st.session_state["flash_active_group"] = sel_key
            gwords = set(groups.get(sel_key, []))
            pool = [w for w in pool if w["word"] in gwords]

    # Level filter
    word_levels = load_word_levels()
    if word_levels:
        lang = st.session_state.get("ui_lang", "tr")
        level_opts = (["Tümü", "A1", "A2", "B1"] if lang == "tr" else ["All", "A1", "A2", "B1"])
        saved_level = st.session_state.get("flash_level_filter", level_opts[0])
        if saved_level not in level_opts:
            saved_level = level_opts[0]
        sel_level = st.selectbox("Seviye / Level", level_opts, index=level_opts.index(saved_level), key="flash_level_sel")
        st.session_state["flash_level_filter"] = sel_level
        if sel_level not in ("Tümü", "All"):
            pool = [w for w in pool if word_levels.get(w["word"]) == sel_level]

    counts = {
        "Verb":    sum(1 for w in pool if w.get("type") == "Verb"),
        "Nomen":   sum(1 for w in pool if w.get("type") == "Nomen"),
        "Adj/Adv": sum(1 for w in pool if w.get("type") == "Adj/Adv"),
    }
    st.markdown(t("flash_pool_info", v=counts["Verb"], n=counts["Nomen"], a=counts["Adj/Adv"]))

    include_untr = st.checkbox(
        t("include_untranslated"),
        value=st.session_state.get("flash_include_untranslated", False),
        key="flash_untr_check",
    )
    st.session_state["flash_include_untranslated"] = include_untr

    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("btn_flash_start"), type="primary", use_container_width=True):
            st.session_state["flash_comp"] = None
            start_flash(words, custom_words)
            st.rerun()
    with col2:
        hard_count = sum(1 for v in st.session_state.progress.values() if v.get("status") == "hard")
        if hard_count > 0:
            if st.button(t("btn_hard_words", count=hard_count), use_container_width=True):
                hard_list = [w for w in words + custom_words
                             if st.session_state.progress.get(w.get("word"), {}).get("status") == "hard"]
                if global_filter != "Tümü":
                    hard_list = [w for w in hard_list if w.get("type") == global_filter]
                import random; random.shuffle(hard_list)
                st.session_state.flash_deck = hard_list[:30]
                st.session_state.flash_idx = 0
                st.session_state.flash_flipped = False
                st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
                st.rerun()


def _render_study(words, custom_words):
    idx = st.session_state.flash_idx
    deck = st.session_state.flash_deck
    sess = st.session_state.flash_session

    if idx >= len(deck):
        _render_session_end(words, custom_words, sess)
        return

    word = deck[idx]
    display = get_display(word)
    translation = get_translation(word["word"], words, custom_words)
    flipped = st.session_state.flash_flipped

    st.progress(idx / len(deck))
    c_prog, c_restart = st.columns([5, 1])
    with c_prog:
        st.caption(t("flash_progress_caption", idx=idx + 1, total=len(deck), c=sess["correct"], w=sess["wrong"], s=sess["skipped"]))
    with c_restart:
        if st.button("🔄", key="flash_restart", use_container_width=True, help=t("btn_new_round")):
            st.session_state.pop("flash_bonus_awarded", None)
            start_flash(words, custom_words)
            st.rerun()

    _render_tts_audio(word["word"])

    if not flipped:
        st.html(flashcard_front_html(word))
        c_flip, c_speak = st.columns([5, 1])
        with c_flip:
            if st.button(t("btn_flip"), use_container_width=True, type="primary", key=f"flip_{idx}"):
                st.session_state.flash_flipped = True
                st.rerun()
        with c_speak:
            if st.button("🔊", key=f"speak_front_{idx}", use_container_width=True):
                _trigger_tts(word["word"])
    else:
        p_info = st.session_state.progress.get(word["word"], {})
        count = p_info.get("count", 0)
        st.markdown(flashcard_back_html(word, translation, display, count), unsafe_allow_html=True)

        # AI example + pronounce
        ai_col1, ai_col2, ai_col3 = st.columns([3, 1, 1])
        with ai_col3:
            if st.button("🔊", key=f"speak_back_{idx}", use_container_width=True):
                _trigger_tts(word["word"])
        with ai_col2:
            if st.button(t("btn_ai_example"), use_container_width=True, key=f"ai_btn_{idx}"):
                with st.spinner(t("spinner_ai_sentence")):
                    ai = get_ai_service()
                    result = ai.generate_example_sentences(word["word"], translation)
                    if result:
                        st.session_state.ai_sentence = result
                        save_ai_example(word["word"], result)
                        earned = st.session_state.get("earned_achievements", [])
                        if "ai_user" not in earned:
                            earned.append("ai_user")
                            st.session_state.earned_achievements = earned
                            from services.gamification import add_xp
                            add_xp(20)
                            st.toast("🎉 Yeni rozet: 🤖 AI Destekli! (+20 XP)", icon="🏆")
                    else:
                        st.toast(t("toast_ai_unavailable"), icon="⚠️")
                st.rerun()

        ai_text = st.session_state.ai_sentence or st.session_state.get("ai_cache", {}).get(word["word"])
        if ai_text:
            st.markdown(
                f'<div class="ai-box">{ai_text.replace(chr(10), "<br>")}</div>',
                unsafe_allow_html=True,
            )

        # Word family
        st.markdown("<div style='margin-top:0.75rem'></div>", unsafe_allow_html=True)
        family_key = f"family_{word['word']}"
        cached_family = st.session_state.get("ai_cache", {}).get(family_key)
        if cached_family:
            st.markdown(t("word_family_label"))
            cols = st.columns(2)
            for i, item in enumerate(cached_family):
                with cols[i % 2]:
                    st.caption(f"• **{item['word']}** — {item['meaning']}")
        else:
            if st.button(t("btn_word_family"), key=f"family_btn_{idx}"):
                with st.spinner(t("spinner_word_family")):
                    ai_svc = get_ai_service()
                    family = ai_svc.generate_word_family(word["word"], translation)
                    if family:
                        cache = st.session_state.get("ai_cache", {})
                        cache[family_key] = family
                        st.session_state.ai_cache = cache
                        persist_current_user()
                st.rerun()

        st.markdown("---")
        st.markdown(t("flash_rating_prompt"))
        c1, c2, c3, c4 = st.columns(4)

        def rate(status, sess_key):
            save_progress(word["word"], status)
            st.session_state.flash_session[sess_key] += 1
            st.session_state.flash_idx += 1
            st.session_state.flash_flipped = False
            st.session_state.ai_sentence = ""
            st.rerun()

        with c1:
            if st.button(t("btn_knew_it"), use_container_width=True, type="primary", key=f"easy_{idx}"):
                rate("easy", "correct")
        with c2:
            if st.button(t("btn_struggled"), use_container_width=True, key=f"ok_{idx}"):
                rate("ok", "wrong")
        with c3:
            if st.button(t("btn_didnt_know"), use_container_width=True, key=f"hard_{idx}"):
                rate("hard", "wrong")
        with c4:
            if st.button(t("btn_skip"), use_container_width=True, key=f"skip_{idx}"):
                st.session_state.flash_session["skipped"] += 1
                st.session_state.flash_idx += 1
                st.session_state.flash_flipped = False
                st.session_state.ai_sentence = ""
                st.rerun()


def _render_session_end(words, custom_words, sess):
    total = sess["correct"] + sess["wrong"] + sess["skipped"]
    pct = int(sess["correct"] / total * 100) if total else 0

    if not st.session_state.get("flash_bonus_awarded"):
        bonus = 30 if pct >= 80 else 15 if pct >= 50 else 5
        add_xp(bonus)
        new_badges = check_achievements()
        show_achievement_popup(new_badges)
        persist_current_user()
        st.session_state["flash_bonus_awarded"] = True
        st.session_state["flash_last_bonus"] = bonus

    bonus = st.session_state.get("flash_last_bonus", 0)

    st.markdown(t("flash_round_done"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("metric_knew"), sess["correct"])
    c2.metric(t("metric_again"), sess["wrong"])
    c3.metric(t("metric_skipped"), sess["skipped"])
    c4.metric(t("metric_bonus_xp"), f"+{bonus}")
    if total:
        st.progress(sess["correct"] / total)
    if st.button(t("btn_new_round"), type="primary"):
        st.session_state.pop("flash_bonus_awarded", None)
        start_flash(words, custom_words)
        st.rerun()
    if st.button(t("btn_go_home")):
        st.session_state.pop("flash_bonus_awarded", None)
        st.session_state.page = PAGE_HOME
        st.rerun()
