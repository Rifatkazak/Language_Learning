import streamlit as st
from models.word import get_translation, get_display
from services.progress import filtered_words
from storage.user_store import persist_current_user
from core.i18n import t


def render(words: list, custom_words: list) -> None:
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

    fw = filtered_words(words, custom_words)
    st.caption(t("wordlist_showing", n=len(fw)))

    status_icon = {"easy": "✅", "ok": "🤔", "hard": "❌"}
    article_color = {"der": "🔵", "die": "🔴", "das": "🟢", "": "⚪"}

    PAGE_SIZE = 50
    if "list_page" not in st.session_state:
        st.session_state.list_page = 0
    total_pages = (len(fw) - 1) // PAGE_SIZE + 1 if fw else 1
    start = st.session_state.list_page * PAGE_SIZE
    page_words = fw[start:start + PAGE_SIZE]

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
            if st.session_state.list_page > 0 and st.button(t("btn_prev"), key="list_prev"):
                st.session_state.list_page -= 1
                st.rerun()
        with pc2:
            st.markdown(
                f"<p style='text-align:center'>{t('page_indicator', cur=st.session_state.list_page + 1, total=total_pages)}</p>",
                unsafe_allow_html=True,
            )
        with pc3:
            if st.session_state.list_page < total_pages - 1 and st.button(t("btn_next_page"), key="list_next"):
                st.session_state.list_page += 1
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
