import streamlit as st

_T = {
    "tr": {
        "app_title":         "Vocardio",
        "login_subtitle":    "B1 kelime haznenizi geliştirin",
        "username":          "Kullanıcı adı",
        "password":          "Şifre",
        "login_btn":         "Giriş Yap",
        "logout_btn":        "Çıkış Yap",
        "username_empty":    "Kullanıcı adı boş olamaz.",
        "password_empty":    "Şifre boş olamaz.",
        "wrong_password":    "Yanlış şifre.",
        "ai_active":         "AI Hizmeti Aktif",
        "ai_inactive":       "AI Pasif — API anahtarı eksik",
        "reminder":          "Hatırlatıcı",
        "studied_today":     "Bugün çalıştın! Harika!",
        "studied_yesterday": "Dün çalışmışsın. Seriyi bozma!",
        "not_studied":       "{n} gündür çalışmamışsın!",
        "progress":          "İlerleme",
        "words_progress":    "{seen} / {total} kelime",
        "streak":            "{n} günlük seri!",
        "leaderboard":       "Liderlik Tablosu",
        "your_rank":         "Senin sıran: #{rank}",
        "word_type":         "Kelime türü",
        "all":               "Tümü",
        # page labels
        "page_home":         "🏠 Ana Sayfa",
        "page_flash":        "📇 Flashcards",
        "page_quiz":         "📝 Quiz",
        "page_games":        "🎮 Kelime Oyunları",
        "page_challenge":    "🏆 Haftalık Görev",
        "page_wordlist":     "📖 Kelime Listesi",
        "page_add":          "➕ Kelime Ekle",
        "page_stats":        "📊 İstatistikler",
        "page_quick":        "⚡ Hızlı Aksiyonlar",
        "page_conv":         "🗣️ AI Konuşma",
        "page_article":      "🎯 Artikel Trainer",
    },
    "en": {
        "app_title":         "Vocardio",
        "login_subtitle":    "Build your B1 vocabulary",
        "username":          "Username",
        "password":          "Password",
        "login_btn":         "Sign In",
        "logout_btn":        "Log Out",
        "username_empty":    "Username cannot be empty.",
        "password_empty":    "Password cannot be empty.",
        "wrong_password":    "Wrong password.",
        "ai_active":         "AI Service Active",
        "ai_inactive":       "AI Inactive — API key missing",
        "reminder":          "Reminder",
        "studied_today":     "You studied today! Great!",
        "studied_yesterday": "You studied yesterday. Keep the streak!",
        "not_studied":       "You haven't studied in {n} days!",
        "progress":          "Progress",
        "words_progress":    "{seen} / {total} words",
        "streak":            "{n} day streak!",
        "leaderboard":       "Leaderboard",
        "your_rank":         "Your rank: #{rank}",
        "word_type":         "Word type",
        "all":               "All",
        # page labels
        "page_home":         "🏠 Home",
        "page_flash":        "📇 Flashcards",
        "page_quiz":         "📝 Quiz",
        "page_games":        "🎮 Word Games",
        "page_challenge":    "🏆 Weekly Challenge",
        "page_wordlist":     "📖 Word List",
        "page_add":          "➕ Add Word",
        "page_stats":        "📊 Statistics",
        "page_quick":        "⚡ Quick Actions",
        "page_conv":         "🗣️ AI Conversation",
        "page_article":      "🎯 Artikel Trainer",
    },
}

# Maps internal page constant → i18n key
PAGE_LABEL_KEYS = {
    "🏠 Ana Sayfa":        "page_home",
    "📇 Flashcards":       "page_flash",
    "📝 Quiz":             "page_quiz",
    "🎮 Kelime Oyunları":  "page_games",
    "🏆 Haftalık Görev":   "page_challenge",
    "📖 Kelime Listesi":   "page_wordlist",
    "➕ Kelime Ekle":      "page_add",
    "📊 İstatistikler":    "page_stats",
    "⚡ Hızlı Aksiyonlar": "page_quick",
    "🗣️ AI Konuşma":       "page_conv",
    "🎯 Artikel Trainer":  "page_article",
}


def t(key: str, **kwargs) -> str:
    lang = st.session_state.get("ui_lang", "tr")
    text = _T.get(lang, _T["tr"]).get(key, key)
    return text.format(**kwargs) if kwargs else text


def page_label(page_const: str) -> str:
    key = PAGE_LABEL_KEYS.get(page_const, page_const)
    return t(key)
