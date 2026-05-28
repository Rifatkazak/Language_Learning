import streamlit as st
from models.word import get_translation, get_display
from services.game_engine import start_flash
from services.progress import save_progress, save_ai_example, filtered_words
from services.gamification import ACHIEVEMENTS, add_xp, check_achievements, show_achievement_popup
from storage.user_store import persist_current_user
from services.ai_service import get_ai_service
from ui.components import flashcard_front_html, flashcard_back_html
from core.session import PAGE_HOME, PAGE_FLASH


def render(words: list, custom_words: list) -> None:
    st.markdown("# 📇 Flashcard Çalışması")

    global_filter = st.session_state.get("filter_type", "Tümü")
    if global_filter != "Tümü":
        st.info(f"🔍 **Global filtre: {global_filter}** — Yalnızca {global_filter} türündeki kelimeler gösteriliyor.")

    if not st.session_state.flash_deck:
        _render_start_screen(words, custom_words, global_filter)
    else:
        _render_study(words, custom_words)


def _render_start_screen(words, custom_words, global_filter):
    st.info("Başlamak için aşağıdaki butona tıklayın.")
    pool = filtered_words(words, custom_words)
    if global_filter != "Tümü":
        pool = [w for w in pool if w.get("type") == global_filter]

    counts = {
        "Verb":    sum(1 for w in pool if w.get("type") == "Verb"),
        "Nomen":   sum(1 for w in pool if w.get("type") == "Nomen"),
        "Adj/Adv": sum(1 for w in pool if w.get("type") == "Adj/Adv"),
    }
    st.markdown(f"**Mevcut havuz:** Verb: {counts['Verb']} • Nomen: {counts['Nomen']} • Adj/Adv: {counts['Adj/Adv']}")

    include_untr = st.checkbox(
        "Çevirisi olmayanları da dahil et",
        value=st.session_state.get("flash_include_untranslated", False),
        key="flash_untr_check",
    )
    st.session_state["flash_include_untranslated"] = include_untr

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Flashcard Başlat", type="primary", use_container_width=True):
            st.session_state["flash_comp"] = None
            start_flash(words, custom_words)
            st.rerun()
    with col2:
        hard_count = sum(1 for v in st.session_state.progress.values() if v.get("status") == "hard")
        if hard_count > 0:
            if st.button(f"❌ Zorlu Kelimeler ({hard_count})", use_container_width=True):
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
    st.caption(f"Kart {idx+1} / {len(deck)}  |  ✅ {sess['correct']}  ❌ {sess['wrong']}  ⏭️ {sess['skipped']}")

    if not flipped:
        st.html(flashcard_front_html(word))
        if st.button("🔄 Çevir", use_container_width=True, type="primary"):
            st.session_state.flash_flipped = True
            st.rerun()
    else:
        p_info = st.session_state.progress.get(word["word"], {})
        count = p_info.get("count", 0)
        st.markdown(flashcard_back_html(word, translation, display, count), unsafe_allow_html=True)

        # AI example
        ai_col1, ai_col2 = st.columns([3, 1])
        with ai_col2:
            if st.button("🤖 AI Örnek Cümle", use_container_width=True, key=f"ai_btn_{idx}"):
                with st.spinner("AI cümle üretiyor..."):
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
                        st.toast("AI şu an kullanılamıyor.", icon="⚠️")
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
            st.markdown("**🔗 Kelime Ailesi:**")
            cols = st.columns(2)
            for i, item in enumerate(cached_family):
                with cols[i % 2]:
                    st.caption(f"• **{item['word']}** — {item['meaning']}")
        else:
            if st.button("🔗 Kelime Ailesi", key=f"family_btn_{idx}"):
                with st.spinner("AI kelime ailesi hazırlıyor..."):
                    ai_svc = get_ai_service()
                    family = ai_svc.generate_word_family(word["word"], translation)
                    if family:
                        cache = st.session_state.get("ai_cache", {})
                        cache[family_key] = family
                        st.session_state.ai_cache = cache
                        persist_current_user()
                st.rerun()

        st.markdown("---")
        st.markdown("**Bu kelimeyi nasıl buldunuz?**")
        c1, c2, c3, c4 = st.columns(4)

        def rate(status, sess_key):
            save_progress(word["word"], status)
            st.session_state.flash_session[sess_key] += 1
            st.session_state.flash_idx += 1
            st.session_state.flash_flipped = False
            st.session_state.ai_sentence = ""
            st.rerun()

        with c1:
            if st.button("✅ Bildim", use_container_width=True, type="primary", key=f"easy_{idx}"):
                rate("easy", "correct")
        with c2:
            if st.button("🤔 Zorlandım", use_container_width=True, key=f"ok_{idx}"):
                rate("ok", "wrong")
        with c3:
            if st.button("❌ Bilmedim", use_container_width=True, key=f"hard_{idx}"):
                rate("hard", "wrong")
        with c4:
            if st.button("⏭️ Atla", use_container_width=True, key=f"skip_{idx}"):
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

    st.markdown("## 🎉 Tur Tamamlandı!")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Bildim", sess["correct"])
    c2.metric("🔄 Tekrar", sess["wrong"])
    c3.metric("⏭️ Atladım", sess["skipped"])
    c4.metric("⚡ Bonus XP", f"+{bonus}")
    if total:
        st.progress(sess["correct"] / total)
    if st.button("🔄 Yeni Tur Başlat", type="primary"):
        st.session_state.pop("flash_bonus_awarded", None)
        start_flash(words, custom_words)
        st.rerun()
    if st.button("🏠 Ana Sayfaya Dön"):
        st.session_state.pop("flash_bonus_awarded", None)
        st.session_state.page = PAGE_HOME
        st.rerun()
