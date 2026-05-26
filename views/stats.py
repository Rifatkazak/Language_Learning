import datetime
import streamlit as st
from models.word import get_translation, get_display
from services.progress import get_due_words
from services.ai_service import get_ai_service
from services.game_engine import start_flash
from storage.user_store import persist_current_user
from ui.components import render_weak_analysis
from core.session import PAGE_FLASH


def render(words: list, custom_words: list) -> None:
    st.markdown("# 📊 İstatistikler ve İlerleme")

    p = st.session_state.progress
    total = len(words) + len(custom_words)
    seen = len(p)
    hard = sum(1 for v in p.values() if v.get("status") == "hard")
    ok = sum(1 for v in p.values() if v.get("status") == "ok")
    easy = sum(1 for v in p.values() if v.get("status") == "easy")
    unseen = total - seen
    due = len(get_due_words(words, custom_words))

    st.markdown("### Genel Özet")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📚 Toplam", total)
    c2.metric("✅ Öğrenildi", easy)
    c3.metric("🤔 Çalışılıyor", ok)
    c4.metric("❌ Zorlu", hard)
    c5.metric("⏰ Bugün tekrar", due)

    streak = st.session_state.daily_streak
    if streak > 0:
        st.markdown(f"### 🔥 Günlük Seri: **{streak} gün**")

    st.markdown("---")
    st.markdown("### Dağılım Grafiği")
    chart_data = {
        "Öğrenildi ✅": easy, "Çalışılıyor 🤔": ok,
        "Zorlu ❌": hard, "Görülmedi": unseen,
    }
    if any(v > 0 for v in chart_data.values()):
        st.bar_chart(chart_data)

    st.markdown("---")
    st.markdown("### Türe Göre Dağılım")
    type_stats: dict = {}
    for w in words + custom_words:
        t = w["type"]
        pi = p.get(w["word"], {})
        sv = pi.get("status", "unseen")
        if t not in type_stats:
            type_stats[t] = {"total": 0, "easy": 0, "ok": 0, "hard": 0, "unseen": 0}
        type_stats[t]["total"] += 1
        type_stats[t][sv] += 1
    for t, stats in type_stats.items():
        pct2 = int(stats["easy"] / stats["total"] * 100) if stats["total"] else 0
        st.markdown(f"**{t}** — {stats['total']} kelime, %{pct2} öğrenildi")
        st.progress(pct2 / 100)

    st.markdown("---")
    st.markdown("### 📋 En Zorlu Kelimeler")
    hard_words = [(word, info) for word, info in p.items() if info.get("status") == "hard"]
    hard_words.sort(key=lambda x: x[1].get("count", 0), reverse=True)
    if hard_words:
        for word, info in hard_words[:15]:
            wobj = next((w for w in words + custom_words if w["word"] == word), None)
            if wobj:
                col1, col2, col3 = st.columns([2, 2, 1])
                col1.write(f"**{get_display(wobj)}**")
                col2.write(get_translation(word, words, custom_words))
                col3.write(f"❌ {info.get('count', 0)}×")
    else:
        st.info("Henüz zorlu kelime yok. Harika gidiyorsunuz! 🎉")

    st.markdown("---")
    render_weak_analysis(words, custom_words)

    st.markdown("---")
    st.markdown("### 🤖 AI Destekli Analiz")
    hard_words_list = [word for word, info in p.items() if info.get("status") == "hard"]
    if st.button("🔍 AI ile Zayıf Noktalarımı Analiz Et", use_container_width=True):
        with st.spinner("AI analiz yapıyor..."):
            ai = get_ai_service()
            user_stats = {
                "total_xp": st.session_state.get("total_xp", 0),
                "streak": st.session_state.get("daily_streak", 0),
                "total_words": len(p),
            }
            analysis = ai.analyze_weak_words(hard_words_list, user_stats)
            st.info(f"💡 {analysis}")

    st.markdown("---")
    st.markdown("### ⚡ Hızlı Eylemler")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Zorlu kelimeleri çalış", use_container_width=True, type="primary"):
            hard_list = [
                next((w for w in words + custom_words if w["word"] == word), None)
                for word, info in p.items() if info.get("status") == "hard"
            ]
            hard_list = [w for w in hard_list if w]
            if hard_list:
                import random; random.shuffle(hard_list)
                st.session_state.flash_deck = hard_list[:25]
                st.session_state.flash_idx = 0
                st.session_state.flash_flipped = False
                st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
                st.session_state.page = PAGE_FLASH
                st.rerun()
            else:
                st.warning("Zorlu kelime yok.")
    with col2:
        if st.button("🗑️ İlerlemeyi Sıfırla", use_container_width=True):
            if st.checkbox("Emin misiniz? Bu işlem geri alınamaz."):
                st.session_state.progress = {}
                st.session_state.daily_streak = 0
                persist_current_user()
                st.rerun()

    st.markdown("---")
    st.markdown("### 📈 Öğrenme Hızın")
    last_7 = []
    for i in range(6, -1, -1):
        day_str = str(datetime.date.today() - datetime.timedelta(days=i))
        last_7.append(sum(1 for v in p.values() if v.get("last_seen") == day_str))
    st.bar_chart({"Çalışılan Kelime": last_7})
    st.caption("Son 7 gündeki günlük çalışma aktiviten")

    if seen > 0 and easy > 0:
        start_date = st.session_state.get("start_date", datetime.date.today())
        if isinstance(start_date, str):
            try:
                start_date = datetime.date.fromisoformat(start_date)
            except Exception:
                start_date = datetime.date.today()
        days_elapsed = max(1, (datetime.date.today() - start_date).days)
        wpd = easy / days_elapsed
        remaining = total - easy
        days_left = int(remaining / max(wpd, 1))
        st.info(f"🎯 Mevcut hızınla **{days_left} gün** içinde tüm kelimeleri öğrenebilirsin!")
