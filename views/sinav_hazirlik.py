import streamlit as st
from core.i18n import t
import views.bildbeschreibung as bildbeschreibung
import views.brief_schreiben as brief_schreiben
import views.kendinden_bahset as kendinden_bahset


def render(words: list, custom_words: list) -> None:
    st.markdown(f"# 📋 {t('exam_title')}")
    st.caption(t("exam_subtitle"))

    tab_vorst, tab_bild, tab_brief = st.tabs([
        f"👤 {t('exam_tab_vorstellung')}",
        f"🖼️ {t('exam_tab_bild')}",
        f"✉️ {t('exam_tab_brief')}",
    ])

    with tab_vorst:
        kendinden_bahset.render(words, custom_words)

    with tab_bild:
        bildbeschreibung.render(words, custom_words)

    with tab_brief:
        brief_schreiben.render(words, custom_words)
