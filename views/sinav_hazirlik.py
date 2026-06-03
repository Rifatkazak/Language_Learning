import streamlit as st
from core.i18n import t
import views.bildbeschreibung as bildbeschreibung


def render(words: list, custom_words: list) -> None:
    st.markdown(f"# 📋 {t('exam_title')}")
    st.caption(t("exam_subtitle"))

    tab_bild, = st.tabs([f"🖼️ {t('exam_tab_bild')}"])

    with tab_bild:
        bildbeschreibung.render(words, custom_words)
