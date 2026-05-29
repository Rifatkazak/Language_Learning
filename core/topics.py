import streamlit as st

TOPIC_TR = {
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
}

_TR_TO_EN = {v: k for k, v in TOPIC_TR.items()}


def display_group_name(name: str) -> str:
    """Return the localized display name for a group."""
    lang = st.session_state.get("ui_lang", "tr")
    if lang == "en":
        return _TR_TO_EN.get(name, name)
    return TOPIC_TR.get(name, name)
