import streamlit as st
from models.word import get_translation, get_display
from services.progress import filtered_words


def render(words: list, custom_words: list) -> None:
    st.markdown("# 📖 Kelime Listesi")

    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input(
            "🔍 Ara", value=st.session_state.search,
            placeholder="Kelime ara...", label_visibility="collapsed",
        )
        if search != st.session_state.search:
            st.session_state.search = search
            st.rerun()
    with col2:
        ft_map = {"Tümü": "Tümü", "Verb": "Fiiller", "Nomen": "İsimler", "Adj/Adv": "Sıfat/Zarf"}
        ft = st.selectbox(
            "Tür", list(ft_map.keys()), format_func=lambda x: ft_map[x],
            label_visibility="collapsed",
            index=list(ft_map.keys()).index(st.session_state.filter_type),
        )
        if ft != st.session_state.filter_type:
            st.session_state.filter_type = ft
            st.rerun()

    fw = filtered_words(words, custom_words)
    st.caption(f"**{len(fw)}** kelime gösteriliyor")

    status_icon = {"easy": "✅", "ok": "🤔", "hard": "❌"}
    article_color = {"der": "🔵", "die": "🔴", "das": "🟢", "": "⚪"}

    PAGE_SIZE = 50
    if "list_page" not in st.session_state:
        st.session_state.list_page = 0
    total_pages = (len(fw) - 1) // PAGE_SIZE + 1 if fw else 1
    start = st.session_state.list_page * PAGE_SIZE
    page_words = fw[start:start + PAGE_SIZE]

    h1, h2, h3, h4, h5 = st.columns([0.5, 2, 2, 1.5, 1])
    h1.markdown("**#**"); h2.markdown("**Almanca**"); h3.markdown("**Türkçe**")
    h4.markdown("**Tür**"); h5.markdown("**Durum**")
    st.markdown("<hr style='margin:4px 0'>", unsafe_allow_html=True)

    for i, w in enumerate(page_words, start=start + 1):
        c1, c2, c3, c4, c5 = st.columns([0.5, 2, 2, 1.5, 1])
        p_info = st.session_state.progress.get(w["word"], {})
        status = p_info.get("status", "")
        art = w.get("article", "")
        c1.write(i)
        c2.write(f"{article_color.get(art,'⚪')} **{art} {w['word']}**" if art else f"**{w['word']}**")
        c3.write(get_translation(w["word"], words, custom_words))
        c4.write(w["type"])
        c5.write(status_icon.get(status, "—"))

    if total_pages > 1:
        st.markdown("---")
        pc1, pc2, pc3 = st.columns([1, 2, 1])
        with pc1:
            if st.session_state.list_page > 0 and st.button("◀ Önceki", key="list_prev"):
                st.session_state.list_page -= 1
                st.rerun()
        with pc2:
            st.markdown(
                f"<p style='text-align:center'>Sayfa {st.session_state.list_page+1} / {total_pages}</p>",
                unsafe_allow_html=True,
            )
        with pc3:
            if st.session_state.list_page < total_pages - 1 and st.button("Sonraki ▶", key="list_next"):
                st.session_state.list_page += 1
                st.rerun()
