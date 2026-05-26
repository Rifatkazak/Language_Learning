import datetime
import random
import streamlit as st
from models.word import get_translation, get_display
from services.ai_service import get_ai_service
from services.gamification import add_xp
from storage.user_store import persist_current_user
from core.session import PAGE_FLASH, PAGE_QUIZ
from services.game_engine import make_quiz_question


def render(words: list, custom_words: list) -> None:
    st.markdown("# 🏆 Haftalık Challenge")
    st.markdown("Her hafta **30 kelime** çalışarak büyük ödüller kazan!")

    week_num = datetime.date.today().isocalendar()[1]
    year = datetime.date.today().year
    challenge_key = f"week_{year}_{week_num}"

    if challenge_key not in st.session_state:
        _render_type_selection(words, custom_words, challenge_key)
        return

    challenge = st.session_state[challenge_key]
    _render_active_challenge(words, custom_words, challenge, challenge_key)


def _render_type_selection(words, custom_words, challenge_key):
    st.markdown("### 🎯 Challenge Tipi Seç")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖 Auto Challenge", use_container_width=True, type="primary"):
            all_words = words + custom_words
            unseen = [w for w in all_words if w["word"] not in st.session_state.progress]
            if len(unseen) < 30:
                st.warning(f"⚠️ Yeterli yeni kelime yok! ({len(unseen)}/30)")
            else:
                target = unseen[:30]
                st.session_state[challenge_key] = _new_challenge(target, "auto")
                persist_current_user()
                st.rerun()
    with col2:
        if st.button("✏️ Manual Challenge", use_container_width=True, type="secondary"):
            st.session_state.show_manual_selection = True
            st.rerun()

    if st.session_state.get("show_manual_selection", False):
        _render_manual_selection(words, custom_words, challenge_key)


def _render_manual_selection(words, custom_words, challenge_key):
    st.markdown("---")
    st.markdown("### 📝 Manual Kelime Seçimi")
    st.caption("30 kelime seçin (en az 10)")
    all_words = words + custom_words
    filter_type = st.selectbox("Filtrele", ["Tümü", "Görülmemiş", "Zorlanılan", "Öğrenilen"])
    if filter_type == "Görülmemiş":
        avail = [w for w in all_words if w["word"] not in st.session_state.progress]
    elif filter_type == "Zorlanılan":
        avail = [w for w in all_words if st.session_state.progress.get(w["word"], {}).get("status") == "hard"]
    elif filter_type == "Öğrenilen":
        avail = [w for w in all_words if st.session_state.progress.get(w["word"], {}).get("status") == "easy"]
    else:
        avail = list(all_words)

    search = st.text_input("🔍 Kelime ara", placeholder="Almanca veya Türkçe...")
    if search:
        avail = [w for w in avail if search.lower() in w["word"].lower()
                 or search.lower() in get_translation(w["word"], words, custom_words).lower()]

    if "manual_selected" not in st.session_state:
        st.session_state.manual_selected = []

    words_per_page = 20
    if "manual_page" not in st.session_state:
        st.session_state.manual_page = 0
    start_idx = st.session_state.manual_page * words_per_page
    page_words = avail[start_idx: start_idx + words_per_page]

    st.markdown("**Seçmek için kelimelere tıkla:**")
    cols = st.columns(4)
    for idx, word_obj in enumerate(page_words):
        word_text = word_obj["word"]
        is_sel = word_text in st.session_state.manual_selected
        with cols[idx % 4]:
            if st.button(get_display(word_obj), key=f"sel_{word_text}_{idx}",
                         use_container_width=True, type="primary" if is_sel else "secondary"):
                if is_sel:
                    st.session_state.manual_selected.remove(word_text)
                else:
                    if len(st.session_state.manual_selected) < 30:
                        st.session_state.manual_selected.append(word_text)
                    else:
                        st.warning("⚠️ En fazla 30 kelime seçebilirsiniz!")
                st.rerun()

    total_pages = (len(avail) - 1) // words_per_page + 1 if avail else 1
    if total_pages > 1:
        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            if st.session_state.manual_page > 0 and st.button("◀ Önceki", key="man_prev"):
                st.session_state.manual_page -= 1; st.rerun()
        with p2:
            st.markdown(f"<p style='text-align:center'>{st.session_state.manual_page+1}/{total_pages}</p>", unsafe_allow_html=True)
        with p3:
            if st.session_state.manual_page < total_pages - 1 and st.button("Sonraki ▶", key="man_next"):
                st.session_state.manual_page += 1; st.rerun()

    st.markdown(f"### ✅ Seçilen Kelimeler ({len(st.session_state.manual_selected)}/30)")
    if st.session_state.manual_selected:
        sel_objs = [w for w in all_words if w["word"] in st.session_state.manual_selected]
        for w in sel_objs[:15]:
            st.markdown(f"- {get_display(w)} → {get_translation(w['word'], words, custom_words)}")
        if len(sel_objs) > 15:
            st.caption(f"...ve {len(sel_objs)-15} daha")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ Temizle", use_container_width=True):
                st.session_state.manual_selected = []; st.rerun()
        if len(st.session_state.manual_selected) >= 10:
            with c2:
                if st.button("🚀 Challenge Başlat", use_container_width=True, type="primary"):
                    sel_data = [w for w in all_words if w["word"] in st.session_state.manual_selected]
                    st.session_state[challenge_key] = _new_challenge(sel_data, "manual")
                    persist_current_user()
                    st.session_state.show_manual_selection = False
                    st.session_state.manual_selected = []
                    st.rerun()
        else:
            st.warning("En az 10 kelime seçmelisiniz!")

    if st.button("❌ İptal", use_container_width=True):
        st.session_state.show_manual_selection = False
        st.session_state.manual_selected = []
        st.rerun()
    st.stop()


def _new_challenge(target_words: list, challenge_type: str) -> dict:
    return {
        "completed": 0, "target": len(target_words), "claimed": False,
        "start_date": str(datetime.date.today()),
        "target_words": [w["word"] for w in target_words],
        "target_words_data": target_words,
        "completed_words": [],
        "flashcard_completed": False, "quiz_completed": False,
        "dialog_created": False, "dialog_content": None,
        "challenge_type": challenge_type,
    }


def _render_active_challenge(words, custom_words, challenge, challenge_key):
    badge = "🤖" if challenge.get("challenge_type") == "auto" else "✏️"
    st.markdown(f"### {badge} {challenge.get('challenge_type','auto').upper()} CHALLENGE")

    completed_count = 0
    for word in challenge["target_words"]:
        if word in st.session_state.progress:
            status = st.session_state.progress[word].get("status", "")
            if status == "easy":
                completed_count += 1
                if word not in challenge["completed_words"]:
                    challenge["completed_words"].append(word)

    challenge["completed"] = completed_count
    if not challenge.get("flashcard_completed", False):
        if all(w in st.session_state.progress for w in challenge["target_words"]):
            challenge["flashcard_completed"] = True
            st.balloons()

    st.session_state[challenge_key] = challenge

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎯 Hedef", f"{challenge['target']} kelime")
    col2.metric("✅ Öğrenilen", f"{challenge['completed']} kelime")
    col3.metric("📅 Kalan", f"{challenge['target'] - challenge['completed']} kelime")
    col4.metric("📇 Flashcard", "✅" if challenge.get("flashcard_completed") else "⏳")

    if challenge["target"] > 0:
        st.progress(challenge["completed"] / challenge["target"])

    st.markdown("---")

    if challenge["completed"] >= challenge["target"] > 0:
        if not challenge.get("claimed", False):
            st.balloons()
            st.success(f"🎉 TEBRİKLER! {challenge['target']} kelimeyi öğrendin!")
            add_xp(300)
            earned = st.session_state.get("earned_achievements", [])
            if "weekly_champion" not in earned:
                earned.append("weekly_champion")
                st.session_state.earned_achievements = earned
                st.markdown("🏅 **Yeni Rozet: Haftalık Şampiyon**")
            st.markdown("✨ **+300 XP kazandın!**")
            if st.button("🎁 Ödülü Al", key="claim_reward", use_container_width=True, type="primary"):
                challenge["claimed"] = True
                st.session_state[challenge_key] = challenge
                persist_current_user()
                st.rerun()
        else:
            st.success("🏆 Bu haftaki challenge'ı tamamladın!")
    else:
        st.info(f"📊 Bu hafta {challenge['completed']}/{challenge['target']} yeni kelime öğrendin.")

    st.markdown("---")
    st.markdown("### 🎯 Challenge Aksiyonları")
    target_list = [w for w in words + custom_words if w["word"] in challenge["target_words"]]

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📇 1. Flashcard Çalış", use_container_width=True, type="primary"):
            if target_list:
                unseen = [w for w in target_list if w["word"] not in st.session_state.progress]
                seen_ch = [w for w in target_list if w["word"] in st.session_state.progress]
                deck = unseen + seen_ch
                st.session_state.flash_deck = deck
                st.session_state.flash_idx = 0
                st.session_state.flash_flipped = False
                st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
                st.session_state.flash_challenge_mode = True
                st.session_state.current_challenge_key = challenge_key
                st.session_state.page = PAGE_FLASH
                st.rerun()

    with col2:
        if challenge.get("flashcard_completed"):
            if st.button("📝 2. Quiz Yap", use_container_width=True, type="secondary"):
                if target_list:
                    random.shuffle(target_list)
                    st.session_state.quiz_deck = target_list[:20]
                    st.session_state.quiz_idx = 0
                    st.session_state.quiz_session = {"correct": 0, "wrong": 0}
                    st.session_state.quiz_challenge_mode = True
                    make_quiz_question(words, custom_words)
                    st.session_state.page = PAGE_QUIZ
                    st.rerun()
        else:
            st.button("📝 2. Quiz Yap", use_container_width=True, disabled=True,
                      help="Önce tüm flashcard'ları tamamlamalısın!")

    with col3:
        if challenge.get("flashcard_completed"):
            if not challenge.get("dialog_created"):
                if st.button("💬 3. AI Diyalog Oluştur", use_container_width=True, type="secondary"):
                    with st.spinner("🤖 AI diyalog oluşturuyor..."):
                        ai = get_ai_service()
                        dialog = ai.create_challenge_dialog(
                            target_list,
                            lambda w: get_translation(w, words, custom_words),
                        )
                        challenge["dialog_content"] = dialog
                        challenge["dialog_created"] = True
                        st.session_state[challenge_key] = challenge
                        persist_current_user()
                        st.rerun()
            else:
                if st.button("💬 3. AI Diyalog Göster", use_container_width=True, type="secondary"):
                    st.session_state.show_challenge_dialog = True
                    st.rerun()
        else:
            st.button("💬 3. AI Diyalog Oluştur", use_container_width=True, disabled=True,
                      help="Önce flashcard'ları tamamlamalısın!")

    if st.session_state.get("show_challenge_dialog") and challenge.get("dialog_content"):
        st.markdown("---")
        st.markdown("## 💬 Haftalık Kelimelerle AI Diyalog")
        dialog_html = challenge["dialog_content"]
        for word_obj in target_list[:10]:
            word = word_obj["word"]
            if word in dialog_html:
                dialog_html = dialog_html.replace(
                    word,
                    f'<mark style="background:#ffd700;padding:2px 4px;border-radius:4px;">{word}</mark>',
                )
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);'
            f'border-radius:20px;padding:2rem;margin:1rem 0;">'
            f'<div style="color:white;font-size:1.1rem;line-height:1.8;">'
            f'{dialog_html.replace(chr(10),"<br>")}</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("❌ Kapat", use_container_width=True):
            st.session_state.show_challenge_dialog = False
            st.rerun()

    st.markdown("---")
    st.markdown("### 📖 Bu Haftaki Hedef Kelimeler")
    if challenge["target_words"]:
        learned = challenge["completed_words"]
        unlearned = [w for w in challenge["target_words"] if w not in learned]
        st.markdown(f"**Toplam: {len(challenge['target_words'])}** | ✅ {len(learned)} | 📝 {len(unlearned)}")
        cols = st.columns(3)
        for idx, word_text in enumerate(challenge["target_words"]):
            wobj = next((w for w in words + custom_words if w["word"] == word_text), None)
            if wobj:
                with cols[idx % 3]:
                    icon = "✅" if word_text in learned else "📝"
                    st.markdown(f"{icon} {get_display(wobj)}")

        if unlearned and not challenge.get("flashcard_completed"):
            if st.button("⚡ Kalan Kelimeleri Çalış", use_container_width=True):
                rem_list = [w for w in words + custom_words if w["word"] in unlearned]
                if rem_list:
                    st.session_state.flash_deck = rem_list
                    st.session_state.flash_idx = 0
                    st.session_state.flash_flipped = False
                    st.session_state.flash_challenge_mode = True
                    st.session_state.page = PAGE_FLASH
                    st.rerun()

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Yeni Challenge Başlat (Haftayı Sıfırla)", use_container_width=True):
            if challenge_key in st.session_state:
                del st.session_state[challenge_key]
            st.session_state.show_manual_selection = False
            st.session_state.manual_selected = []
            st.rerun()
