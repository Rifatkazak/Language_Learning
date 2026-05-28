import datetime
import random
import streamlit as st
from models.word import get_translation, get_display
from services.ai_service import get_ai_service
from services.gamification import add_xp
from storage.user_store import (
    persist_current_user, load_challenges_file, save_challenges_file, load_users_file,
)
from core.session import PAGE_FLASH, PAGE_QUIZ
from services.game_engine import make_quiz_question


def render(words: list, custom_words: list) -> None:
    week_num = datetime.date.today().isocalendar()[1]
    year = datetime.date.today().year
    challenge_key = f"week_{year}_{week_num}"

    st.markdown("# 🏆 Haftalık Challenge")
    st.caption(f"Hafta {week_num} · {year}")

    tab_personal, tab_community = st.tabs(["📋 Kişisel", "🌍 Topluluk"])

    with tab_personal:
        if challenge_key not in st.session_state:
            _render_type_selection(words, custom_words, challenge_key)
        else:
            _render_active_challenge(words, custom_words, st.session_state[challenge_key], challenge_key)

    with tab_community:
        _render_community_tab(words, custom_words, challenge_key)


# ── Community Tab ─────────────────────────────────────────────────────────────

def _render_community_tab(words: list, custom_words: list, challenge_key: str) -> None:
    challenges = load_challenges_file()
    shared = challenges.get(challenge_key)

    if shared:
        _render_shared_view(words, custom_words, challenge_key, shared)
        return

    st.markdown(
        "<div style='text-align:center;padding:2.5rem 1rem;'>"
        "<div style='font-size:2.5rem;margin-bottom:0.75rem;'>🌍</div>"
        "<p style='font-weight:600;font-size:1.05rem;margin-bottom:0.25rem;'>Bu hafta topluluk challenge'ı yok.</p>"
        "<p style='font-size:0.85rem;color:#64748b;'>Kişisel challenge'ını paylaşarak ilk başlatan sen ol!</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    personal = st.session_state.get(challenge_key)
    if personal:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🌍 Challenge'ımı Paylaş", type="primary", use_container_width=True):
                challenges[challenge_key] = {
                    "created_by": st.session_state.get("current_user", "?"),
                    "created_at": str(datetime.date.today()),
                    "challenge_type": personal.get("challenge_type", "manual"),
                    "target_words": personal.get("target_words", []),
                    "target_words_data": personal.get("target_words_data", []),
                }
                save_challenges_file(challenges)
                st.success("✅ Challenge toplulukla paylaşıldı!")
                st.rerun()
    else:
        st.info("Önce Kişisel sekmesinden bir challenge oluştur.")


def _render_shared_view(words: list, custom_words: list, challenge_key: str, shared: dict) -> None:
    creator = shared.get("created_by", "?")
    created_at = shared.get("created_at", "")
    target_words = shared.get("target_words", [])
    c_type_label = "🤖 Auto" if shared.get("challenge_type") == "auto" else "✏️ Manual"

    with st.container(border=True):
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.markdown("**Bu Haftanın Topluluk Challenge'ı**")
            st.caption(f"Oluşturan: **{creator}** · {created_at} · {c_type_label}")
        with col_b:
            st.metric("Kelime", len(target_words))

    # Participant leaderboard
    all_users = load_users_file()
    me = st.session_state.get("current_user", "")
    participants = []
    for uname, udata in all_users.items():
        if not isinstance(udata, dict):
            continue
        prog = udata.get("progress", {})
        completed = sum(1 for w in target_words if prog.get(w, {}).get("status") == "easy")
        if completed > 0 or uname == me:
            participants.append({"name": uname, "completed": completed})

    # Merge current user's live progress (may be more up-to-date than file)
    live_completed = sum(
        1 for w in target_words
        if st.session_state.get("progress", {}).get(w, {}).get("status") == "easy"
    )
    for p in participants:
        if p["name"] == me:
            p["completed"] = live_completed

    participants.sort(key=lambda x: x["completed"], reverse=True)

    if participants:
        st.markdown("##### Katılımcı Sıralaması")
        medals = ["🥇", "🥈", "🥉"]
        for i, p in enumerate(participants):
            pct = p["completed"] / len(target_words) if target_words else 0
            is_me = p["name"] == me
            medal = medals[i] if i < 3 else f"{i + 1}."
            bg = "rgba(74,144,217,0.08)" if is_me else "transparent"
            name_html = f"<strong>{p['name']}</strong>" if is_me else p["name"]
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:0.75rem;padding:8px 10px;"
                f"border-radius:8px;background:{bg};margin:2px 0;'>"
                f"<span style='min-width:24px;font-size:1rem;'>{medal}</span>"
                f"<span style='flex:1;font-size:0.9rem;'>{name_html}</span>"
                f"<span style='font-size:0.8rem;color:#64748b;min-width:40px;text-align:right;'>"
                f"{p['completed']}/{len(target_words)}</span>"
                f"<div style='width:72px;background:#e2e8f0;border-radius:4px;height:6px;margin-left:8px;'>"
                f"<div style='width:{int(pct * 100)}%;background:#4a90d9;border-radius:4px;height:6px;'></div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    personal = st.session_state.get(challenge_key)
    if not personal:
        all_words = words + custom_words
        target_data = shared.get("target_words_data") or [
            w for w in all_words if w["word"] in target_words
        ]
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🤝 Challenge'a Katıl", type="primary", use_container_width=True):
                st.session_state[challenge_key] = _new_challenge(
                    target_data, shared.get("challenge_type", "auto")
                )
                persist_current_user()
                st.success("✅ Katıldın! Kişisel sekmesine geç.")
                st.rerun()
    else:
        st.info(f"Bu challenge'dasın — ilerleme: {live_completed}/{len(target_words)}")

    with st.expander(f"📖 Kelime Listesi ({len(target_words)} kelime)"):
        all_words = words + custom_words
        cols = st.columns(3)
        for idx, word_text in enumerate(target_words):
            wobj = next((w for w in all_words if w["word"] == word_text), None)
            status = st.session_state.get("progress", {}).get(word_text, {}).get("status", "")
            icon = "✅" if status == "easy" else "📝"
            with cols[idx % 3]:
                if wobj:
                    st.caption(f"{icon} {get_display(wobj)}")
                else:
                    st.caption(f"{icon} {word_text}")


# ── Personal Tab ──────────────────────────────────────────────────────────────

def _render_type_selection(words, custom_words, challenge_key):
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### Challenge Tipi Seç")
    st.caption("Her hafta 30 kelime çalışarak büyük ödüller kazan!")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("🤖 **Auto Challenge**")
            st.caption("Filtrene göre rastgele kelimeler seçilir")
        if st.button("Auto Başlat", use_container_width=True, type="primary", key="auto_btn"):
            st.session_state.show_auto_filters = True
            st.session_state.show_manual_selection = False
            st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("✏️ **Manual Challenge**")
            st.caption("Hangi kelimeleri çalışacağını sen seç")
        if st.button("Manuel Seç", use_container_width=True, type="secondary", key="manual_btn"):
            st.session_state.show_manual_selection = True
            st.session_state.show_auto_filters = False
            st.rerun()

    if st.session_state.get("show_auto_filters", False):
        _render_auto_filters(words, custom_words, challenge_key)

    if st.session_state.get("show_manual_selection", False):
        _render_manual_selection(words, custom_words, challenge_key)


def _render_auto_filters(words, custom_words, challenge_key):
    st.markdown("---")
    st.markdown("##### 🤖 Auto Challenge Filtresi")
    all_words = words + custom_words

    col1, col2 = st.columns(2)
    with col1:
        word_type = st.selectbox(
            "Kelime Türü",
            ["Tümü", "Verb", "Nomen", "Adj/Adv"],
            key="auto_word_type",
        )
    with col2:
        difficulty = st.selectbox(
            "Durum",
            ["Görülmemiş", "Zorlanılan", "Tümü"],
            key="auto_difficulty",
        )

    if difficulty == "Görülmemiş":
        pool = [w for w in all_words if w["word"] not in st.session_state.progress]
    elif difficulty == "Zorlanılan":
        pool = [w for w in all_words if st.session_state.progress.get(w["word"], {}).get("status") == "hard"]
    else:
        pool = list(all_words)

    if word_type != "Tümü":
        pool = [w for w in pool if w.get("type") == word_type]

    count = min(30, len(pool))
    st.caption(f"Uygun kelime: **{len(pool)}** · {count} tanesi rastgele seçilecek")

    c1, c2, c3 = st.columns([1, 2, 1])
    if len(pool) >= 10:
        with c2:
            if st.button(f"🚀 {count} Kelimeyle Başlat", use_container_width=True, type="primary", key="auto_start_final"):
                selected = random.sample(pool, count)
                st.session_state[challenge_key] = _new_challenge(selected, "auto")
                st.session_state.show_auto_filters = False
                persist_current_user()
                st.rerun()
    else:
        st.warning(f"⚠️ Bu filtrelerle yeterli kelime yok! ({len(pool)} kelime, en az 10 gerekli)")

    if st.button("❌ İptal", key="auto_cancel", use_container_width=True):
        st.session_state.show_auto_filters = False
        st.rerun()


def _render_manual_selection(words, custom_words, challenge_key):
    st.markdown("---")
    st.markdown("##### Kelime Seçimi")
    all_words = words + custom_words

    col_f, col_s = st.columns([1, 2])
    with col_f:
        filter_type = st.selectbox(
            "Filtrele", ["Tümü", "Görülmemiş", "Zorlanılan", "Öğrenilen"],
            label_visibility="collapsed",
        )
    with col_s:
        search = st.text_input("Ara", placeholder="Almanca veya Türkçe...", label_visibility="collapsed")

    if filter_type == "Görülmemiş":
        avail = [w for w in all_words if w["word"] not in st.session_state.progress]
    elif filter_type == "Zorlanılan":
        avail = [w for w in all_words if st.session_state.progress.get(w["word"], {}).get("status") == "hard"]
    elif filter_type == "Öğrenilen":
        avail = [w for w in all_words if st.session_state.progress.get(w["word"], {}).get("status") == "easy"]
    else:
        avail = list(all_words)

    if search:
        avail = [
            w for w in avail
            if search.lower() in w["word"].lower()
            or search.lower() in get_translation(w["word"], words, custom_words).lower()
        ]

    if "manual_selected" not in st.session_state:
        st.session_state.manual_selected = []

    words_per_page = 20
    if "manual_page" not in st.session_state:
        st.session_state.manual_page = 0

    selected_count = len(st.session_state.manual_selected)
    st.caption(f"Seçilen: **{selected_count}/30**")

    start_idx = st.session_state.manual_page * words_per_page
    page_words = avail[start_idx: start_idx + words_per_page]

    cols = st.columns(4)
    for idx, word_obj in enumerate(page_words):
        word_text = word_obj["word"]
        is_sel = word_text in st.session_state.manual_selected
        with cols[idx % 4]:
            if st.button(
                get_display(word_obj),
                key=f"sel_{word_text}_{idx}",
                use_container_width=True,
                type="primary" if is_sel else "secondary",
            ):
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
                st.session_state.manual_page -= 1
                st.rerun()
        with p2:
            st.markdown(
                f"<p style='text-align:center;font-size:0.85rem;'>"
                f"{st.session_state.manual_page + 1}/{total_pages}</p>",
                unsafe_allow_html=True,
            )
        with p3:
            if st.session_state.manual_page < total_pages - 1 and st.button("Sonraki ▶", key="man_next"):
                st.session_state.manual_page += 1
                st.rerun()

    if st.session_state.manual_selected:
        st.markdown("---")
        sel_objs = [w for w in all_words if w["word"] in st.session_state.manual_selected]
        with st.expander(f"✅ Seçilen Kelimeler ({selected_count}/30)"):
            for w in sel_objs:
                st.caption(f"• {get_display(w)} → {get_translation(w['word'], words, custom_words)}")

        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("🗑️ Temizle", use_container_width=True):
                st.session_state.manual_selected = []
                st.rerun()
        if selected_count >= 10:
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


def _new_challenge(target_words: list, challenge_type: str) -> dict:
    return {
        "completed": 0, "target": len(target_words), "claimed": False,
        "start_date": str(datetime.date.today()),
        "target_words": [w["word"] for w in target_words],
        "target_words_data": target_words,
        "completed_words": [],
        "flashcard_completed": False, "quiz_completed": False,
        "dialog_created": False, "dialog_content": None,
        "story_created": False, "story_content": None,
        "chat_history": [],
        "challenge_type": challenge_type,
    }


def _render_active_challenge(words, custom_words, challenge, challenge_key):
    badge = "🤖" if challenge.get("challenge_type") == "auto" else "✏️"
    st.caption(f"{badge} {challenge.get('challenge_type', 'auto').upper()} CHALLENGE · başlangıç {challenge.get('start_date', '')}")

    # Sync completed words from live progress
    completed_count = 0
    for word in challenge["target_words"]:
        if st.session_state.progress.get(word, {}).get("status") == "easy":
            completed_count += 1
            if word not in challenge["completed_words"]:
                challenge["completed_words"].append(word)

    challenge["completed"] = completed_count
    if not challenge.get("flashcard_completed") and all(
        w in st.session_state.progress for w in challenge["target_words"]
    ):
        challenge["flashcard_completed"] = True

    st.session_state[challenge_key] = challenge

    total = challenge["target"]
    pct = completed_count / total if total else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Hedef", f"{total} kelime")
    col2.metric("Öğrenilen", f"{completed_count}")
    col3.metric("Kalan", f"{total - completed_count}")
    col4.metric("Flashcard", "✅" if challenge.get("flashcard_completed") else "⏳")

    st.markdown(
        f"<div style='background:#e2e8f0;border-radius:8px;height:8px;margin:0.75rem 0 1.25rem;'>"
        f"<div style='background:linear-gradient(90deg,#4a90d9,#27ae60);border-radius:8px;"
        f"height:8px;width:{int(pct * 100)}%;transition:width 0.5s;'></div></div>",
        unsafe_allow_html=True,
    )

    if completed_count >= total > 0:
        if not challenge.get("claimed"):
            st.success(f"🎉 TEBRİKLER! {total} kelimeyi öğrendin!")
            add_xp(300)
            earned = st.session_state.get("earned_achievements", [])
            if "weekly_champion" not in earned:
                earned.append("weekly_champion")
                st.session_state.earned_achievements = earned
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🎁 Ödülü Al (+300 XP)", key="claim_reward", use_container_width=True, type="primary"):
                    challenge["claimed"] = True
                    st.session_state[challenge_key] = challenge
                    persist_current_user()
                    st.rerun()
        else:
            st.success("🏆 Bu haftaki challenge'ı tamamladın!")
    else:
        st.info(f"Bu hafta **{completed_count}/{total}** kelime öğrendin.")

    st.markdown("---")
    st.markdown("##### Aksiyonlar")
    target_list = [w for w in words + custom_words if w["word"] in challenge["target_words"]]

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📇 1. Flashcard Çalış", use_container_width=True, type="primary"):
            if target_list:
                unseen = [w for w in target_list if w["word"] not in st.session_state.progress]
                seen_ch = [w for w in target_list if w["word"] in st.session_state.progress]
                st.session_state.flash_deck = unseen + seen_ch
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
                if st.button("💬 3. AI Diyalog", use_container_width=True, type="secondary"):
                    with st.spinner("AI diyalog oluşturuyor..."):
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
                if st.button("💬 3. Diyalogu Göster", use_container_width=True, type="secondary"):
                    st.session_state.show_challenge_dialog = True
                    st.rerun()
        else:
            st.button("💬 3. AI Diyalog", use_container_width=True, disabled=True,
                      help="Önce flashcard'ları tamamlamalısın!")

    if st.session_state.get("show_challenge_dialog") and challenge.get("dialog_content"):
        st.markdown("---")
        dialog_html = challenge["dialog_content"]
        for word_obj in target_list[:10]:
            word = word_obj["word"]
            if word in dialog_html:
                dialog_html = dialog_html.replace(
                    word,
                    f'<mark style="background:rgba(255,215,0,0.25);padding:2px 5px;'
                    f'border-radius:4px;border:1px solid rgba(255,215,0,0.5);">{word}</mark>',
                )
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#1e3a5f 0%,#16213e 100%);'
            f'border-radius:16px;padding:1.5rem 2rem;margin:1rem 0;">'
            f'<div style="color:white;font-size:1rem;line-height:1.9;">'
            f'{dialog_html.replace(chr(10), "<br>")}</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Kapat", use_container_width=True):
            st.session_state.show_challenge_dialog = False
            st.rerun()

    # ── Story + Chat ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### Ek Çalışmalar")
    col_s, col_c = st.columns(2)

    with col_s:
        if not challenge.get("story_created"):
            if st.button("📖 4. Haftalık Hikaye Oluştur", use_container_width=True, type="secondary"):
                with st.spinner("AI hikaye yazıyor..."):
                    ai = get_ai_service()
                    story = ai.generate_challenge_story(
                        target_list,
                        lambda w: get_translation(w, words, custom_words),
                    )
                    challenge["story_content"] = story
                    challenge["story_created"] = True
                    st.session_state[challenge_key] = challenge
                    persist_current_user()
                st.rerun()
        else:
            label = "📖 4. Hikayeyi Gizle" if st.session_state.get("show_challenge_story") else "📖 4. Hikayeyi Göster"
            if st.button(label, use_container_width=True, type="secondary"):
                st.session_state.show_challenge_story = not st.session_state.get("show_challenge_story", False)
                st.rerun()

    with col_c:
        label_c = "💬 5. Sohbeti Kapat" if st.session_state.get("show_challenge_chat") else "💬 5. Kelime Sohbeti"
        if st.button(label_c, use_container_width=True, type="secondary"):
            st.session_state.show_challenge_chat = not st.session_state.get("show_challenge_chat", False)
            st.rerun()

    if st.session_state.get("show_challenge_story") and challenge.get("story_content"):
        _render_story_section(challenge, target_list, challenge_key)

    if st.session_state.get("show_challenge_chat"):
        _render_chat_section(challenge, target_list, words, custom_words, challenge_key)

    st.markdown("---")
    st.markdown("##### Bu Haftanın Kelimeleri")
    if challenge["target_words"]:
        learned = challenge["completed_words"]
        unlearned = [w for w in challenge["target_words"] if w not in learned]
        st.caption(
            f"Toplam {len(challenge['target_words'])} · ✅ {len(learned)} öğrenildi · 📝 {len(unlearned)} kaldı"
        )
        cols = st.columns(3)
        for idx, word_text in enumerate(challenge["target_words"]):
            wobj = next((w for w in words + custom_words if w["word"] == word_text), None)
            if wobj:
                with cols[idx % 3]:
                    icon = "✅" if word_text in learned else "📝"
                    st.caption(f"{icon} {get_display(wobj)}")

        if unlearned and not challenge.get("flashcard_completed"):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
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
        if st.button("🔄 Yeni Challenge Başlat", use_container_width=True):
            if challenge_key in st.session_state:
                del st.session_state[challenge_key]
            st.session_state.show_manual_selection = False
            st.session_state.manual_selected = []
            st.session_state.show_challenge_story = False
            st.session_state.show_challenge_chat = False
            st.rerun()


def _render_story_section(challenge: dict, target_list: list, challenge_key: str) -> None:
    st.markdown("---")
    story_html = challenge["story_content"]
    for word_obj in target_list:
        w = word_obj["word"]
        if w in story_html:
            story_html = story_html.replace(
                w,
                f'<mark style="background:rgba(255,215,0,0.28);padding:1px 5px;'
                f'border-radius:3px;border:1px solid rgba(255,215,0,0.45);">{w}</mark>',
            )
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1a2744 0%,#0f172a 100%);'
        f'border-radius:16px;padding:1.75rem 2rem;margin:0.5rem 0;">'
        f'<div style="color:#e2e8f0;font-size:0.97rem;line-height:2;">'
        f'{story_html.replace(chr(10), "<br>")}</div></div>',
        unsafe_allow_html=True,
    )


def _render_chat_section(
    challenge: dict, target_list: list,
    words: list, custom_words: list, challenge_key: str,
) -> None:
    st.markdown("---")
    st.caption("Bu haftanın kelimeleriyle Almanca konuşma pratiği. AI kelimeleri doğal olarak kullanır ve hatalarını düzeltir.")

    chat_history = challenge.get("chat_history", [])

    # Başlangıç mesajı yoksa AI'ı başlat
    if not chat_history:
        ai = get_ai_service()
        target_words = [w["word"] for w in target_list]
        first_msg = ai.chat_with_challenge_words([], target_words)
        if first_msg:
            chat_history.append({"role": "assistant", "content": first_msg})
            challenge["chat_history"] = chat_history
            st.session_state[challenge_key] = challenge
            persist_current_user()

    # Mesajları göster
    chat_box = st.container(height=380)
    with chat_box:
        for msg in chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Kullanıcı girişi
    user_input = st.chat_input("Almanca veya Türkçe yaz...", key="challenge_chat_input")
    if user_input:
        chat_history.append({"role": "user", "content": user_input})
        ai = get_ai_service()
        target_words = [w["word"] for w in target_list]
        response = ai.chat_with_challenge_words(chat_history, target_words)
        chat_history.append({
            "role": "assistant",
            "content": response or "Bir sorun olustu, tekrar yazar misin?",
        })
        challenge["chat_history"] = chat_history[-24:]
        st.session_state[challenge_key] = challenge
        persist_current_user()
        st.rerun()

    if chat_history:
        if st.button("🗑️ Sohbeti Sıfırla", key="clear_challenge_chat"):
            challenge["chat_history"] = []
            st.session_state[challenge_key] = challenge
            persist_current_user()
            st.rerun()
