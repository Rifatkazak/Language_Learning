import json
import streamlit as st
from pathlib import Path
from models.word import get_translation, get_display
from services.progress import filtered_words
from services.ai_service import get_ai_service
from storage.user_store import (
    persist_current_user,
    publish_community_group,
    load_community_groups,
    increment_group_import,
)
from core.i18n import t

_LEVELS_PATH = Path(__file__).parent.parent / "data" / "word_levels.json"


def _load_word_levels() -> dict:
    try:
        with open(_LEVELS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_word_levels(levels: dict) -> None:
    with open(_LEVELS_PATH, "w", encoding="utf-8") as f:
        json.dump(levels, f, ensure_ascii=False, indent=2)


def _run_level_classification(words: list, custom_words: list) -> None:
    ai = get_ai_service()
    levels = _load_word_levels()
    all_words = [w for w in (words + custom_words) if w["word"] not in levels]
    if not all_words:
        st.toast("Tüm kelimeler zaten seviyelendirilmiş!", icon="✅")
        return
    lang = st.session_state.get("ui_lang", "tr")
    batch_size = 80
    batches = [all_words[i:i + batch_size] for i in range(0, len(all_words), batch_size)]
    label = "AI seviyeleri belirleniyor..." if lang == "tr" else "AI is classifying levels..."
    bar = st.progress(0, text=label)
    for idx, batch in enumerate(batches):
        result = ai.classify_words_by_level(batch)
        levels.update(result)
        bar.progress((idx + 1) / len(batches))
    _save_word_levels(levels)
    bar.empty()
    msg = f"{len(levels)} kelime seviyelendirildi!" if lang == "tr" else f"{len(levels)} words classified!"
    st.toast(msg, icon="🏅")

_AUTO_TOPICS = [
    "Work & Career", "Health & Body", "Home & Living", "Travel & Transport",
    "Education", "Sports & Hobbies", "Food & Drink", "Family & Relationships",
    "Bureaucracy & Law", "Nature & Environment", "Shopping", "Technology & Media",
    "Emotions & Personality", "Time & Calendar", "Other",
]

_TOPIC_TR = {
    "Work & Career":           "İş & Kariyer",
    "Health & Body":           "Sağlık & Vücut",
    "Home & Living":           "Ev & Yaşam",
    "Travel & Transport":      "Seyahat & Ulaşım",
    "Education":               "Eğitim",
    "Sports & Hobbies":        "Spor & Hobiler",
    "Food & Drink":            "Yiyecek & İçecek",
    "Family & Relationships":  "Aile & İlişkiler",
    "Bureaucracy & Law":       "Bürokrasi & Hukuk",
    "Nature & Environment":    "Doğa & Çevre",
    "Shopping":                "Alışveriş",
    "Technology & Media":      "Teknoloji & Medya",
    "Emotions & Personality":  "Duygular & Kişilik",
    "Time & Calendar":         "Zaman & Takvim",
    "Other":                   "Diğer",
}


def render(words: list, custom_words: list) -> None:
    _render_community_section()
    st.divider()
    st.markdown(t("wordlist_title"))

    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input(
            "🔍 Ara", value=st.session_state.search,
            placeholder=t("wordlist_search_placeholder"), label_visibility="collapsed",
        )
        if search != st.session_state.search:
            st.session_state.search = search
            st.rerun()
    with col2:
        ft_map = {
            "Tümü":    t("all"),
            "Verb":    t("type_verbs"),
            "Nomen":   t("type_nouns"),
            "Adj/Adv": t("type_adjadv"),
        }
        ft = st.selectbox(
            t("type_filter_label"), list(ft_map.keys()), format_func=lambda x: ft_map[x],
            label_visibility="collapsed",
            index=list(ft_map.keys()).index(st.session_state.filter_type),
        )
        if ft != st.session_state.filter_type:
            st.session_state.filter_type = ft
            st.rerun()

    # Level tabs
    word_levels = _load_word_levels()
    lang = st.session_state.get("ui_lang", "tr")
    has_levels = bool(word_levels)

    level_tabs_label = ["Tümü", "A1", "A2", "B1"] if lang == "tr" else ["All", "A1", "A2", "B1"]
    level_tab_all, level_tab_a1, level_tab_a2, level_tab_b1 = st.tabs(level_tabs_label)

    fw = filtered_words(words, custom_words)

    def _render_word_table(word_list: list) -> None:
        st.caption(t("wordlist_showing", n=len(word_list)))
        if not word_list:
            btn_label = "🏅 Seviyeleri Ata (AI)" if lang == "tr" else "🏅 Assign Levels (AI)"
            st.info("Bu seviyede henüz kelime yok. Önce seviyeleri atayın." if lang == "tr" else "No words at this level yet. Assign levels first.")
            if st.button(btn_label, key="assign_levels_empty", use_container_width=True):
                _run_level_classification(words, custom_words)
                st.rerun()
            return

        status_icon = {"easy": "✅", "ok": "🤔", "hard": "❌"}
        article_color = {"der": "🔵", "die": "🔴", "das": "🟢", "": "⚪"}

        PAGE_SIZE = 50
        page_key = f"list_page_{st.session_state.get('_active_level', 'all')}"
        if page_key not in st.session_state:
            st.session_state[page_key] = 0
        total_pages = (len(word_list) - 1) // PAGE_SIZE + 1 if word_list else 1
        start = st.session_state[page_key] * PAGE_SIZE
        page_words = word_list[start:start + PAGE_SIZE]

        h1, h2, h3, h4, h5, h6 = st.columns([0.5, 2, 2, 1.2, 0.8, 1])
        h1.markdown("**#**")
        h2.markdown(t("col_header_german"))
        h3.markdown(t("col_header_turkish"))
        h4.markdown(t("col_header_type"))
        h5.markdown(t("col_header_status"))
        h6.markdown(t("col_header_group"))
        st.markdown("<hr style='margin:4px 0'>", unsafe_allow_html=True)

        for i, w in enumerate(page_words, start=start + 1):
            c1, c2, c3, c4, c5, c6 = st.columns([0.5, 2, 2, 1.2, 0.8, 1])
            p_info = st.session_state.progress.get(w["word"], {})
            status = p_info.get("status", "")
            art = w.get("article", "")
            c1.write(i)
            c2.write(f"{article_color.get(art,'⚪')} **{art} {w['word']}**" if art else f"**{w['word']}**")
            c3.write(get_translation(w["word"], words, custom_words))
            c4.write(w["type"])
            c5.write(status_icon.get(status, "—"))
            with c6:
                groups = st.session_state.get("word_groups", {})
                in_groups = [g for g, ws in groups.items() if w["word"] in ws]
                label = f"📌{len(in_groups)}" if in_groups else t("btn_add_to_group")
                with st.popover(label, use_container_width=True):
                    _group_popover(w["word"])

        if total_pages > 1:
            st.markdown("---")
            pc1, pc2, pc3 = st.columns([1, 2, 1])
            with pc1:
                if st.session_state[page_key] > 0 and st.button(t("btn_prev"), key=f"list_prev_{page_key}"):
                    st.session_state[page_key] -= 1
                    st.rerun()
            with pc2:
                st.markdown(
                    f"<p style='text-align:center'>{t('page_indicator', cur=st.session_state[page_key] + 1, total=total_pages)}</p>",
                    unsafe_allow_html=True,
                )
            with pc3:
                if st.session_state[page_key] < total_pages - 1 and st.button(t("btn_next_page"), key=f"list_next_{page_key}"):
                    st.session_state[page_key] += 1
                    st.rerun()

    with level_tab_all:
        st.session_state["_active_level"] = "all"
        if not has_levels:
            btn_label = "🏅 Seviyeleri Ata (AI)" if lang == "tr" else "🏅 Assign Levels (AI)"
            btn_help = "DeepSeek AI ile tüm kelimeleri A1/A2/B1 seviyelerine atar" if lang == "tr" else "Use AI to classify all words into A1/A2/B1 levels"
            if st.button(btn_label, help=btn_help, use_container_width=True, key="assign_levels_btn"):
                _run_level_classification(words, custom_words)
                st.rerun()
        _render_word_table(fw)

    with level_tab_a1:
        st.session_state["_active_level"] = "A1"
        if not has_levels:
            btn_label = "🏅 Seviyeleri Ata (AI)" if lang == "tr" else "🏅 Assign Levels (AI)"
            if st.button(btn_label, use_container_width=True, key="assign_levels_a1"):
                _run_level_classification(words, custom_words)
                st.rerun()
        else:
            a1_words = [w for w in fw if word_levels.get(w["word"]) == "A1"]
            _render_word_table(a1_words)

    with level_tab_a2:
        st.session_state["_active_level"] = "A2"
        if not has_levels:
            btn_label = "🏅 Seviyeleri Ata (AI)" if lang == "tr" else "🏅 Assign Levels (AI)"
            if st.button(btn_label, use_container_width=True, key="assign_levels_a2"):
                _run_level_classification(words, custom_words)
                st.rerun()
        else:
            a2_words = [w for w in fw if word_levels.get(w["word"]) == "A2"]
            _render_word_table(a2_words)

    with level_tab_b1:
        st.session_state["_active_level"] = "B1"
        if not has_levels:
            btn_label = "🏅 Seviyeleri Ata (AI)" if lang == "tr" else "🏅 Assign Levels (AI)"
            if st.button(btn_label, use_container_width=True, key="assign_levels_b1"):
                _run_level_classification(words, custom_words)
                st.rerun()
        else:
            b1_words = [w for w in fw if word_levels.get(w["word"]) == "B1"]
            _render_word_table(b1_words)



def _run_auto_grouping(words: list, custom_words: list) -> None:
    ai = get_ai_service()
    all_words = words + custom_words
    lang = st.session_state.get("ui_lang", "tr")
    groups: dict = {}
    batch_size = 80
    batches = [all_words[i:i + batch_size] for i in range(0, len(all_words), batch_size)]
    bar = st.progress(0, text="AI grupları oluşturuyor..." if lang == "tr" else "AI is creating groups...")
    for idx, batch in enumerate(batches):
        classified = ai.auto_classify_words(batch, _AUTO_TOPICS)
        for word_text, topic in classified.items():
            label = _TOPIC_TR.get(topic, topic) if lang == "tr" else topic
            groups.setdefault(label, [])
            if word_text not in groups[label]:
                groups[label].append(word_text)
        bar.progress((idx + 1) / len(batches))
    groups.pop(_TOPIC_TR.get("Other", "Other") if lang == "tr" else "Other", None)
    existing = dict(st.session_state.get("word_groups", {}))
    existing.update(groups)
    st.session_state.word_groups = existing
    persist_current_user()
    bar.empty()


def _load_topic_groups() -> None:
    import json
    from pathlib import Path
    lang = st.session_state.get("ui_lang", "tr")
    path = Path(__file__).parent.parent / "data" / "word_topics.json"
    if not path.exists():
        st.warning("word_topics.json bulunamadı." if lang == "tr" else "word_topics.json not found.")
        return
    with open(path, encoding="utf-8") as f:
        topic_data = json.load(f)
    existing = dict(st.session_state.get("word_groups", {}))
    added = 0
    for topic_en, data in topic_data.items():
        label = data["label_tr"] if lang == "tr" else data["label_en"]
        existing[label] = data["words"]
        added += 1
    st.session_state.word_groups = existing
    persist_current_user()
    st.toast(f"{added} grup oluşturuldu!" if lang == "tr" else f"{added} groups created!", icon="✅")


def _render_community_section() -> None:
    st.markdown(t("community_groups_title"))
    tab1, tab2 = st.tabs([t("my_groups_tab"), t("community_tab")])

    with tab1:
        lang = st.session_state.get("ui_lang", "tr")
        btn_label = "📚 Konu Gruplarını Yükle" if lang == "tr" else "📚 Load Topic Groups"
        btn_help = "İş, Sağlık, Seyahat gibi hazır konu gruplarını yükler (API kullanmaz)" if lang == "tr" else "Load preset topic groups like Work, Health, Travel (no API calls)"
        if st.button(btn_label, help=btn_help, use_container_width=True, key="load_topic_groups"):
            _load_topic_groups()
            st.rerun()
        st.markdown("")
        groups = st.session_state.get("word_groups", {})
        if not groups:
            st.info(t("community_no_groups"))
        else:
            current_user = st.session_state.get("current_user", "")
            for gname, gwords in groups.items():
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f"**{gname}**  `{t('community_words_count', n=len(gwords))}`")
                with c3:
                    if st.button(t("community_share_btn"), key=f"share_{gname}", use_container_width=True):
                        if publish_community_group(gname, gwords, current_user):
                            st.toast(t("community_share_ok"), icon="🌐")
                        st.rerun()

    with tab2:
        community = load_community_groups()
        current_user = st.session_state.get("current_user", "")
        if not community:
            st.info(t("community_empty"))
        else:
            for grp in community:
                gid = grp["id"]
                gname = grp["group_name"]
                author = grp["author"]
                wcount = grp.get("word_count", 0)
                icount = grp.get("import_count", 0)

                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{gname}**")
                        st.caption(
                            f"{t('community_by', author=author)} · "
                            f"{t('community_words_count', n=wcount)} · "
                            f"{t('community_imports_label', n=icount)}"
                        )
                    with c2:
                        already = gname in st.session_state.get("word_groups", {})
                        btn_label = t("community_shared_badge") if (author == current_user) else t("community_import_btn")
                        disabled = author == current_user
                        if st.button(btn_label, key=f"import_{gid}", use_container_width=True, disabled=disabled):
                            groups = dict(st.session_state.get("word_groups", {}))
                            import_name = gname if gname not in groups else f"{gname} ({author})"
                            groups[import_name] = grp.get("words", [])
                            st.session_state.word_groups = groups
                            persist_current_user()
                            increment_group_import(gid)
                            st.toast(t("community_imported_ok"), icon="✅")
                            st.rerun()


def _group_popover(word: str) -> None:
    groups = dict(st.session_state.get("word_groups", {}))
    in_groups = [g for g, ws in groups.items() if word in ws]

    if in_groups:
        st.caption("📌 " + ", ".join(in_groups))

    if groups:
        st.markdown(t("group_add_remove"))
        for gname in list(groups.keys()):
            already = word in groups.get(gname, [])
            btn_label = f"✅ {gname}" if already else f"➕ {gname}"
            if st.button(btn_label, key=f"grp_{word}_{gname}", use_container_width=True):
                if already:
                    groups[gname] = [w for w in groups[gname] if w != word]
                else:
                    groups[gname] = groups.get(gname, []) + [word]
                st.session_state.word_groups = groups
                persist_current_user()
                st.rerun()

    st.markdown(t("group_create_new"))
    new_name = st.text_input(
        "Grup adı", key=f"ng_{word}",
        label_visibility="collapsed",
        placeholder=t("group_name_placeholder"),
    )
    if st.button(t("btn_create_and_add"), key=f"cr_{word}", use_container_width=True):
        if new_name.strip():
            gname = new_name.strip()
            if gname not in groups:
                groups[gname] = []
            if word not in groups[gname]:
                groups[gname] = groups[gname] + [word]
            st.session_state.word_groups = groups
            persist_current_user()
            st.rerun()
