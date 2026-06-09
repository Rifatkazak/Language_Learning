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
from core.i18n import t
from core.topics import display_group_name
from services.game_engine import make_quiz_question


def render(words: list, custom_words: list) -> None:
    week_num = datetime.date.today().isocalendar()[1]
    year = datetime.date.today().year
    challenge_key = f"week_{year}_{week_num}"

    st.markdown(t("challenge_title"))
    st.caption(t("challenge_week_caption", n=week_num, year=year))

    tab_personal, tab_community = st.tabs([t("tab_personal"), t("tab_community")])

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
        f"<p style='font-weight:600;font-size:1.05rem;margin-bottom:0.25rem;'>{t('community_no_challenge')}</p>"
        f"<p style='font-size:0.85rem;color:#64748b;'>{t('community_be_first')}</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    personal = st.session_state.get(challenge_key)
    if personal:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(t("btn_share_challenge"), type="primary", use_container_width=True):
                challenges[challenge_key] = {
                    "created_by": st.session_state.get("current_user", "?"),
                    "created_at": str(datetime.date.today()),
                    "challenge_type": personal.get("challenge_type", "manual"),
                    "target_words": personal.get("target_words", []),
                    "target_words_data": personal.get("target_words_data", []),
                }
                save_challenges_file(challenges)
                st.success(t("challenge_shared"))
                st.rerun()
    else:
        st.info(t("community_create_first"))


def _render_shared_view(words: list, custom_words: list, challenge_key: str, shared: dict) -> None:
    creator = shared.get("created_by", "?")
    created_at = shared.get("created_at", "")
    target_words = shared.get("target_words", [])
    c_type_label = "🤖 Auto" if shared.get("challenge_type") == "auto" else "✏️ Manual"

    with st.container(border=True):
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.markdown(t("community_this_week"))
            st.caption(t("community_created_by", u=creator, date=created_at, type=c_type_label))
        with col_b:
            st.metric(t("metric_words"), len(target_words))

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

    live_completed = sum(
        1 for w in target_words
        if st.session_state.get("progress", {}).get(w, {}).get("status") == "easy"
    )
    for p in participants:
        if p["name"] == me:
            p["completed"] = live_completed

    participants.sort(key=lambda x: x["completed"], reverse=True)

    if participants:
        st.markdown(t("community_leaderboard"))
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
            if st.button(t("btn_join_challenge"), type="primary", use_container_width=True):
                st.session_state[challenge_key] = _new_challenge(
                    target_data, shared.get("challenge_type", "auto")
                )
                persist_current_user()
                st.success(t("challenge_joined"))
                st.rerun()
    else:
        st.info(t("challenge_in_progress", c=live_completed, t=len(target_words)))

    with st.expander(t("challenge_word_list_exp", n=len(target_words))):
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
    st.markdown(t("challenge_type_header"))
    st.caption(t("challenge_type_sub"))
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown(t("challenge_auto_label"))
            st.caption(t("challenge_auto_desc"))
        if st.button(t("btn_auto_start"), use_container_width=True, type="primary", key="auto_btn"):
            st.session_state.show_auto_filters = True
            st.session_state.show_manual_selection = False
            st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown(t("challenge_manual_label"))
            st.caption(t("challenge_manual_desc"))
        if st.button(t("btn_manual_select"), use_container_width=True, type="secondary", key="manual_btn"):
            st.session_state.show_manual_selection = True
            st.session_state.show_auto_filters = False
            st.rerun()

    if st.session_state.get("show_auto_filters", False):
        _render_auto_filters(words, custom_words, challenge_key)

    if st.session_state.get("show_manual_selection", False):
        _render_manual_selection(words, custom_words, challenge_key)


def _render_auto_filters(words, custom_words, challenge_key):
    st.markdown("---")
    st.markdown(t("auto_filter_header"))
    all_words = words + custom_words

    # Group filter
    groups = st.session_state.get("word_groups", {})
    pool = list(all_words)
    if groups:
        all_label_grp = t("all_words_group")
        group_keys = list(groups.keys())
        group_opts = [all_label_grp] + [display_group_name(k) for k in group_keys]
        saved_grp = st.session_state.get("ch_auto_group")
        saved_disp = display_group_name(saved_grp) if saved_grp else all_label_grp
        if saved_disp not in group_opts:
            saved_disp = all_label_grp
        sel_grp = st.selectbox(t("group_filter_label"), group_opts, index=group_opts.index(saved_disp), key="ch_auto_grp_sel")
        if sel_grp == all_label_grp:
            st.session_state["ch_auto_group"] = None
        else:
            sel_key = group_keys[group_opts.index(sel_grp) - 1]
            st.session_state["ch_auto_group"] = sel_key
            gwords = set(groups.get(sel_key, []))
            pool = [w for w in pool if w["word"] in gwords]

    col1, col2 = st.columns(2)
    with col1:
        word_type = st.selectbox(
            t("auto_word_type"),
            [t("all"), "Verb", "Nomen", "Adj/Adv"],
            key="auto_word_type",
        )
    with col2:
        difficulty = st.selectbox(
            t("auto_difficulty_label"),
            [t("status_unseen"), t("status_struggling"), t("all")],
            key="auto_difficulty",
        )

    all_label = t("all")
    unseen_label = t("status_unseen")
    struggling_label = t("status_struggling")

    if difficulty == unseen_label:
        pool = [w for w in pool if w["word"] not in st.session_state.progress]
    elif difficulty == struggling_label:
        pool = [w for w in pool if st.session_state.progress.get(w["word"], {}).get("status") == "hard"]

    if word_type != all_label:
        pool = [w for w in pool if w.get("type") == word_type]

    count = min(30, len(pool))
    st.caption(t("auto_pool_info", n=len(pool), count=count))

    c1, c2, c3 = st.columns([1, 2, 1])
    if len(pool) >= 10:
        with c2:
            if st.button(t("btn_auto_start_final", n=count), use_container_width=True, type="primary", key="auto_start_final"):
                selected = random.sample(pool, count)
                st.session_state[challenge_key] = _new_challenge(selected, "auto")
                st.session_state.show_auto_filters = False
                persist_current_user()
                st.rerun()
    else:
        st.warning(t("auto_not_enough", n=len(pool)))

    if st.button(t("btn_cancel"), key="auto_cancel", use_container_width=True):
        st.session_state.show_auto_filters = False
        st.rerun()


def _render_manual_selection(words, custom_words, challenge_key):
    st.markdown("---")
    st.markdown(t("manual_select_header"))
    all_words = words + custom_words

    all_label = t("all")
    unseen_label = t("status_unseen")
    struggling_label = t("status_struggling")
    learned_label = t("status_learned")

    # Group filter
    groups = st.session_state.get("word_groups", {})
    base_pool = list(all_words)
    if groups:
        all_label_grp = t("all_words_group")
        group_keys = list(groups.keys())
        group_opts = [all_label_grp] + [display_group_name(k) for k in group_keys]
        saved_grp = st.session_state.get("ch_manual_group")
        saved_disp = display_group_name(saved_grp) if saved_grp else all_label_grp
        if saved_disp not in group_opts:
            saved_disp = all_label_grp
        sel_grp = st.selectbox(t("group_filter_label"), group_opts, index=group_opts.index(saved_disp), key="ch_manual_grp_sel")
        if sel_grp == all_label_grp:
            st.session_state["ch_manual_group"] = None
        else:
            sel_key = group_keys[group_opts.index(sel_grp) - 1]
            st.session_state["ch_manual_group"] = sel_key
            gwords = set(groups.get(sel_key, []))
            base_pool = [w for w in base_pool if w["word"] in gwords]

    col_f, col_s = st.columns([1, 2])
    with col_f:
        filter_type = st.selectbox(
            t("manual_filter_label"),
            [all_label, unseen_label, struggling_label, learned_label],
            label_visibility="collapsed",
        )
    with col_s:
        search = st.text_input(t("search_label"), placeholder=t("search_placeholder"), label_visibility="collapsed")

    if filter_type == unseen_label:
        avail = [w for w in base_pool if w["word"] not in st.session_state.progress]
    elif filter_type == struggling_label:
        avail = [w for w in base_pool if st.session_state.progress.get(w["word"], {}).get("status") == "hard"]
    elif filter_type == learned_label:
        avail = [w for w in base_pool if st.session_state.progress.get(w["word"], {}).get("status") == "easy"]
    else:
        avail = list(base_pool)

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
    st.caption(t("manual_selected_count", n=selected_count))

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
                        st.warning(t("manual_max_reached"))
                st.rerun()

    total_pages = (len(avail) - 1) // words_per_page + 1 if avail else 1
    if total_pages > 1:
        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            if st.session_state.manual_page > 0 and st.button(t("btn_prev"), key="man_prev"):
                st.session_state.manual_page -= 1
                st.rerun()
        with p2:
            st.markdown(
                f"<p style='text-align:center;font-size:0.85rem;'>"
                f"{st.session_state.manual_page + 1}/{total_pages}</p>",
                unsafe_allow_html=True,
            )
        with p3:
            if st.session_state.manual_page < total_pages - 1 and st.button(t("btn_next_page"), key="man_next"):
                st.session_state.manual_page += 1
                st.rerun()

    if st.session_state.manual_selected:
        st.markdown("---")
        sel_objs = [w for w in all_words if w["word"] in st.session_state.manual_selected]
        with st.expander(t("manual_selected_exp", n=selected_count)):
            for w in sel_objs:
                st.caption(f"• {get_display(w)} → {get_translation(w['word'], words, custom_words)}")

        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button(t("btn_clear"), use_container_width=True):
                st.session_state.manual_selected = []
                st.rerun()
        if selected_count >= 10:
            with c2:
                if st.button(t("btn_challenge_start"), use_container_width=True, type="primary"):
                    sel_data = [w for w in all_words if w["word"] in st.session_state.manual_selected]
                    st.session_state[challenge_key] = _new_challenge(sel_data, "manual")
                    persist_current_user()
                    st.session_state.show_manual_selection = False
                    st.session_state.manual_selected = []
                    st.rerun()
        else:
            st.warning(t("manual_min_warning"))

    if st.button(t("btn_cancel"), use_container_width=True):
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
    col1.metric(t("metric_target"), t("metric_words_val", n=total))
    col2.metric(t("metric_learned_count"), f"{completed_count}")
    col3.metric(t("metric_remaining"), f"{total - completed_count}")
    col4.metric(t("metric_flashcard"), "✅" if challenge.get("flashcard_completed") else "⏳")

    st.markdown(
        f"<div style='background:#e2e8f0;border-radius:8px;height:8px;margin:0.75rem 0 1.25rem;'>"
        f"<div style='background:linear-gradient(90deg,#4a90d9,#27ae60);border-radius:8px;"
        f"height:8px;width:{int(pct * 100)}%;transition:width 0.5s;'></div></div>",
        unsafe_allow_html=True,
    )

    if completed_count >= total > 0:
        if not challenge.get("claimed"):
            st.success(t("challenge_congrats", n=total))
            add_xp(300)
            earned = st.session_state.get("earned_achievements", [])
            if "weekly_champion" not in earned:
                earned.append("weekly_champion")
                st.session_state.earned_achievements = earned
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(t("btn_claim_reward"), key="claim_reward", use_container_width=True, type="primary"):
                    challenge["claimed"] = True
                    st.session_state[challenge_key] = challenge
                    persist_current_user()
                    st.rerun()
        else:
            st.success(t("challenge_completed"))
    else:
        st.info(t("challenge_progress_info", c=completed_count, t=total))

    st.markdown("---")
    st.markdown(t("challenge_actions"))
    target_list = [w for w in words + custom_words if w["word"] in challenge["target_words"]]

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(t("btn_ch_flashcard"), use_container_width=True, type="primary"):
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
            if st.button(t("btn_ch_quiz"), use_container_width=True, type="secondary"):
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
            st.button(t("btn_ch_quiz"), use_container_width=True, disabled=True,
                      help=t("ch_quiz_disabled_help"))

    with col3:
        if challenge.get("flashcard_completed"):
            if not challenge.get("dialog_created"):
                if st.button(t("btn_ch_dialog"), use_container_width=True, type="secondary"):
                    with st.spinner(t("spinner_ai_dialog")):
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
                if st.button(t("btn_ch_show_dialog"), use_container_width=True, type="secondary"):
                    st.session_state.show_challenge_dialog = True
                    st.rerun()
        else:
            st.button(t("btn_ch_dialog"), use_container_width=True, disabled=True,
                      help=t("ch_dialog_disabled_help"))

    if st.session_state.get("show_challenge_dialog") and challenge.get("dialog_content"):
        st.markdown("---")
        dialog_html = challenge["dialog_content"]
        for word_obj in target_list[:10]:
            word = word_obj["word"]
            if word in dialog_html:
                dialog_html = dialog_html.replace(
                    word,
                    f'<mark style="background:#fef08a;padding:2px 6px;border-radius:4px;'
                    f'border:1px solid #facc15;font-weight:600;color:#1e293b;">{word}</mark>',
                )
        st.markdown(
            f'<div style="background:#f0f6ff;border:1px solid #bfdbfe;'
            f'border-left:4px solid #3b82f6;border-radius:12px;'
            f'padding:1.5rem 2rem;margin:1rem 0;">'
            f'<div style="color:#1e293b;font-size:1rem;line-height:1.9;">'
            f'{dialog_html.replace(chr(10), "<br>")}</div></div>',
            unsafe_allow_html=True,
        )
        if st.button(t("btn_close"), use_container_width=True):
            st.session_state.show_challenge_dialog = False
            st.rerun()

    # ── Story + Chat ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(t("challenge_extra"))
    col_s, col_c = st.columns(2)

    with col_s:
        if not challenge.get("story_created"):
            if st.button(t("btn_ch_story"), use_container_width=True, type="secondary"):
                with st.spinner(t("spinner_ai_story")):
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
            label = t("btn_ch_hide_story") if st.session_state.get("show_challenge_story") else t("btn_ch_show_story")
            if st.button(label, use_container_width=True, type="secondary"):
                st.session_state.show_challenge_story = not st.session_state.get("show_challenge_story", False)
                st.rerun()

    with col_c:
        label_c = t("btn_ch_close_chat") if st.session_state.get("show_challenge_chat") else t("btn_ch_open_chat")
        if st.button(label_c, use_container_width=True, type="secondary"):
            st.session_state.show_challenge_chat = not st.session_state.get("show_challenge_chat", False)
            st.rerun()

    if st.session_state.get("show_challenge_story") and challenge.get("story_content"):
        _render_story_section(challenge, target_list, challenge_key)

    if st.session_state.get("show_challenge_chat"):
        _render_chat_section(challenge, target_list, words, custom_words, challenge_key)

    st.markdown("---")
    st.markdown(t("challenge_this_week_words"))
    if challenge["target_words"]:
        learned = challenge["completed_words"]
        unlearned = [w for w in challenge["target_words"] if w not in learned]
        st.caption(t("challenge_words_caption", t=len(challenge["target_words"]), l=len(learned), u=len(unlearned)))
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
                if st.button(t("btn_study_remaining"), use_container_width=True):
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
        if st.button(t("btn_new_challenge"), use_container_width=True):
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
                f'<mark style="background:#fef08a;padding:2px 6px;border-radius:4px;'
                f'border:1px solid #facc15;font-weight:600;color:#1e293b;">{w}</mark>',
            )
    st.markdown(
        f'<div style="background:#fffbeb;border:1px solid #fde68a;'
        f'border-left:4px solid #f59e0b;border-radius:12px;'
        f'padding:1.75rem 2rem;margin:0.5rem 0;">'
        f'<div style="color:#1e293b;font-size:0.97rem;line-height:2;">'
        f'{story_html.replace(chr(10), "<br>")}</div></div>',
        unsafe_allow_html=True,
    )


def _render_chat_section(
    challenge: dict, target_list: list,
    words: list, custom_words: list, challenge_key: str,
) -> None:
    st.markdown("---")
    st.caption(t("challenge_chat_caption"))

    chat_history = challenge.get("chat_history", [])

    if not chat_history:
        ai = get_ai_service()
        target_words = [w["word"] for w in target_list]
        first_msg = ai.chat_with_challenge_words([], target_words)
        if first_msg:
            chat_history.append({"role": "assistant", "content": first_msg})
            challenge["chat_history"] = chat_history
            st.session_state[challenge_key] = challenge
            persist_current_user()

    chat_box = st.container(height=380)
    with chat_box:
        for msg in chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    user_input = st.chat_input(t("challenge_chat_placeholder"), key="challenge_chat_input")
    if user_input:
        chat_history.append({"role": "user", "content": user_input})
        ai = get_ai_service()
        target_words = [w["word"] for w in target_list]
        response = ai.chat_with_challenge_words(chat_history, target_words)
        chat_history.append({
            "role": "assistant",
            "content": response or t("challenge_chat_error"),
        })
        challenge["chat_history"] = chat_history[-24:]
        st.session_state[challenge_key] = challenge
        persist_current_user()
        st.rerun()

    if chat_history:
        if st.button(t("btn_reset_chat"), key="clear_challenge_chat"):
            challenge["chat_history"] = []
            st.session_state[challenge_key] = challenge
            persist_current_user()
            st.rerun()
