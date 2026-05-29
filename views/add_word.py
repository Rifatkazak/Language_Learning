import io
import streamlit as st
from models.word import get_translation, get_display
from storage.user_store import persist_current_user
from services.ai_service import get_ai_service
from core.i18n import t


def render(words: list, custom_words: list) -> None:
    st.markdown(t("addword_title"))
    st.info(t("addword_info"))

    with st.form("add_word_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_word = st.text_input(t("addword_german_label"), placeholder="z.B. lernen")
            new_article = st.selectbox(t("addword_article_label"), ["", "der", "die", "das"])
            new_type = st.selectbox(t("addword_type_label"), ["Verb", "Nomen", "Adj/Adv"])
        with col2:
            new_tr = st.text_input(t("addword_translation_label"), placeholder="öğrenmek")
            new_notes = st.text_area(t("addword_notes_label"), placeholder=t("addword_notes_placeholder"))

        submitted = st.form_submit_button(t("btn_add_word"), type="primary")
        if submitted:
            if not new_word.strip() or not new_tr.strip():
                st.error(t("addword_required"))
            else:
                entry = {
                    "word": new_word.strip(),
                    "article": new_article,
                    "type": new_type,
                    "translation": new_tr.strip(),
                    "custom": True,
                    "notes": new_notes.strip() if new_notes else "",
                }
                ai = get_ai_service()
                with st.spinner(t("spinner_en_translation")):
                    en_tr = ai.translate_to_english(new_word.strip(), new_tr.strip())
                if en_tr:
                    entry["translation_en"] = en_tr
                st.session_state.custom_words.append(entry)
                st.success(t("addword_success", article=new_article, word=new_word))
                persist_current_user()
                st.rerun()

    if st.session_state.custom_words:
        st.markdown("---")
        st.markdown(t("addword_your_words"))
        for i, w in enumerate(st.session_state.custom_words):
            c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
            c1.write(f"**{get_display(w)}**")
            c2.write(get_translation(w["word"], words, custom_words))
            c3.write(w["type"])
            if c4.button("🗑️", key=f"del_{i}"):
                st.session_state.custom_words.pop(i)
                persist_current_user()
                st.rerun()

    st.markdown("---")
    st.markdown(t("addword_csv_section"))
    st.markdown(t("addword_csv_format"))
    uploaded = st.file_uploader(t("addword_csv_upload"), type=["csv", "txt"])
    if uploaded:
        content = uploaded.read().decode("utf-8")
        lines = content.strip().split("\n")
        ai = get_ai_service()
        added, errors = 0, []
        for line in lines:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2:
                entry = {
                    "word": parts[0], "article": parts[3] if len(parts) > 3 else "",
                    "type": parts[2] if len(parts) > 2 else "Verb",
                    "translation": parts[1], "custom": True,
                }
                en_tr = ai.translate_to_english(parts[0], parts[1])
                if en_tr:
                    entry["translation_en"] = en_tr
                st.session_state.custom_words.append(entry)
                added += 1
            else:
                errors.append(line)
        st.success(t("addword_csv_success", n=added))
        if errors:
            st.warning(t("addword_csv_skipped", errors=errors[:5]))
        persist_current_user()
        st.rerun()
