import streamlit as st
import json
import random
import time
import html as _html
import datetime
import os
from pathlib import Path
from pathlib import Path as _Path

# import google.generativeai as genai
from dotenv import load_dotenv

# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# ── Sayfa Ayarları ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Goethe B1 Kelime Öğrenimi",
    page_icon="🇩🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_dotenv()
# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main .block-container { max-width: 900px; padding-top: 2rem; }

/* Flashcard */
.flashcard {
    background: linear-gradient(135deg, #1e3a5f 0%, #16213e 100%);
    border-radius: 20px;
    padding: 3rem 2rem;
    text-align: center;
    min-height: 280px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    cursor: pointer;
    transition: transform 0.2s;
    margin: 1rem 0;
    color: white;
}

.flashcard-front { border-left: 6px solid #4a90d9; }
.flashcard-back  { border-left: 6px solid #27ae60; }

.article-der  { color: #64b3f4; font-weight: 700; font-size: 1.1rem; }
.article-die  { color: #f48fb1; font-weight: 700; font-size: 1.1rem; }
.article-das  { color: #81c784; font-weight: 700; font-size: 1.1rem; }

.word-big { font-size: 2.8rem; font-weight: 700; margin: 0.5rem 0; }
.word-tr  { font-size: 1.8rem; color: #a8d8a8; margin: 0.5rem 0; }
.type-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-top: 0.5rem;
}
.type-Verb  { background: #1a3a6b; color: #64b3f4; }
.type-Nomen { background: #3a1a2e; color: #f48fb1; }
.type-AdjAdv{ background: #1a3a2a; color: #81c784; }

/* Progress bar custom */
.prog-bar-bg {
    background: #e0e0e0;
    border-radius: 8px;
    height: 10px;
    margin: 0.3rem 0;
}
.prog-bar-fill {
    border-radius: 8px;
    height: 10px;
    background: linear-gradient(90deg,#4a90d9,#27ae60);
    transition: width 0.5s;
}

/* Quiz option buttons */
.quiz-option {
    width: 100%;
    padding: 14px 20px;
    margin: 6px 0;
    border-radius: 12px;
    border: 2px solid #ddd;
    background: white;
    font-size: 1rem;
    cursor: pointer;
    text-align: left;
    transition: all 0.2s;
}
.quiz-option:hover { border-color: #4a90d9; background: #f0f7ff; }
.quiz-correct { border-color: #27ae60 !important; background: #f0fff4 !important; color: #1a5c30; }
.quiz-wrong   { border-color: #e53935 !important; background: #fff0f0 !important; color: #7b1a1a; }

/* Stat cards */
.stat-card {
    background: white;
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    border-top: 4px solid;
}
.stat-label { font-size: 0.8rem; color: #888; margin-bottom: 4px; }
.stat-val   { font-size: 2.2rem; font-weight: 700; }

/* Word list item */
.word-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid #f0f0f0;
}
.ai-box {
    background: #f8f9fa;
    border-left: 4px solid #4a90d9;
    border-radius: 0 12px 12px 0;
    padding: 1rem 1.2rem;
    margin-top: 1rem;
    font-size: 0.95rem;
    line-height: 1.7;
}
.streak-fire { font-size: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Veri Yükleme ────────────────────────────────────────────────────────────
@st.cache_data
def load_words():
    path = Path(__file__).parent / "words.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)

WORDS = load_words()


# ── get_translation fonksiyonu (words.json'daki translation alanını okur) ─────
def get_translation(word_obj_or_str):
    """
    Kelimenin çevirisini döndürür.
    Parametre: string (kelime metni) veya dict (kelime objesi)
    """
    # Eğer dict ise içindeki translation alanını kullan
    if isinstance(word_obj_or_str, dict):
        return word_obj_or_str.get('translation', 'Çeviri yok')
    
    # String ise önce WORDS içinde ara
    word_text = word_obj_or_str
    for w in WORDS:
        if w.get('word') == word_text:
            return w.get('translation', 'Çeviri yok')
    
    # Özel kelimelerde de ara
    for w in st.session_state.get('custom_words', []):
        if w.get('word') == word_text:
            return w.get('translation', 'Çeviri yok')
    
    return 'Çeviri yok'

# ── Kullanıcı verileri (kullanıcı bazlı ilerleme kaydı) ─────────────────────
USERS_FILE = Path(__file__).parent / "users.json"

def load_users_file():
    if not USERS_FILE.exists():
        return {}
    try:
        with open(USERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users_file(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def build_deck_from_composition(pool, comp, deck_size):
    # pool: list of word dicts. comp: dict like {'Verb':2,'Nomen':3,'Adj/Adv':1}
    available = {
        'Verb': [w for w in pool if w.get('type','') == 'Verb' and w.get('translation') not in ("Çeviri yok", "—", None, "")],
        'Nomen': [w for w in pool if w.get('type','') == 'Nomen' and w.get('translation') not in ("Çeviri yok", "—", None, "")],
        'Adj/Adv': [w for w in pool if w.get('type','') == 'Adj/Adv' and w.get('translation') not in ("Çeviri yok", "—", None, "")],
    }
    deck = []
    # Fill requested per type
    for t in ('Verb','Nomen','Adj/Adv'):
        req = int(comp.get(t, 0)) if comp else 0
        if req <= 0:
            continue
        take = min(req, len(available[t]))
        if take:
            deck.extend(random.sample(available[t], take))
    # If deck too small, fill from remaining translated pool
    translated_pool = [w for w in pool if w.get('translation') not in ("Çeviri yok", "—", None, "") and w not in deck]
    need = deck_size - len(deck)
    if need > 0:
        if len(translated_pool) <= need:
            deck.extend(translated_pool)
        else:
            deck.extend(random.sample(translated_pool, need))
    random.shuffle(deck)
    return deck[:deck_size]

def load_user_data(username):
    users = st.session_state.get('users', {})
    user_data = users.get(username, {})
    st.session_state.progress = user_data.get('progress', {})
    st.session_state.last_study_date = user_data.get('last_study_date', st.session_state.get('last_study_date'))
    st.session_state.daily_streak = user_data.get('daily_streak', st.session_state.get('daily_streak', 0))
    st.session_state.total_study_minutes = user_data.get('total_study_minutes', st.session_state.get('total_study_minutes', 0))
    st.session_state.custom_words = user_data.get('custom_words', [])
    st.session_state.current_user = username

def persist_current_user():
    username = st.session_state.get('current_user')
    if not username:
        return
    users = st.session_state.get('users', {})
    users[username] = {
        'progress': st.session_state.get('progress', {}),
        'last_study_date': st.session_state.get('last_study_date'),
        'daily_streak': st.session_state.get('daily_streak', 0),
        'total_study_minutes': st.session_state.get('total_study_minutes', 0),
        'custom_words': st.session_state.get('custom_words', []),
    }
    save_users_file(users)
    st.session_state['users'] = users

def get_display(w):
    art = w.get('article', '')
    word = w.get('word', '')
    # Escape any HTML so raw tags aren't rendered inside the card
    art_safe = _html.escape(art) if art else ""
    word_safe = _html.escape(word)
    return f"{art_safe} {word_safe}".strip() if art_safe else word_safe

# ── Session State Başlat ─────────────────────────────────────────────────────
def init_state():
    defaults = {
        "progress": {},          # word -> {status, count, last_seen, streak}
        "page": "Ana Sayfa",
        "flash_deck": [],
        "flash_idx": 0,
        "flash_flipped": False,
        "flash_session": {"correct": 0, "wrong": 0, "skipped": 0},
        "quiz_deck": [],
        "quiz_idx": 0,
        "quiz_state": None,      # {word, options, answered, correct}
        "quiz_session": {"correct": 0, "wrong": 0},
        "filter_type": "Tümü",
        "search": "",
        "daily_streak": 0,
        "last_study_date": None,
        "total_study_minutes": 0,
        "session_start": time.time(),
        "ai_sentence": "",
        "ai_loading": False,
        "custom_words": [],      # kullanıcı eklemeleri
        "flash_filter_type": "Karışık",
        "quiz_filter_type": "Karışık",
        "flash_comp": None,
        "quiz_comp": None,
        "flash_include_untranslated": False,
        "quiz_include_untranslated": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
# Load users from disk into session
if 'users' not in st.session_state:
    st.session_state['users'] = load_users_file()
# If a current user is already set (session restore), load their data
if st.session_state.get('current_user'):
    if st.session_state['current_user'] in st.session_state['users']:
        load_user_data(st.session_state['current_user'])

# ── Yardımcı Fonksiyonlar ────────────────────────────────────────────────────

def generate_ai_example(word, translation=""):

    prompt = f"""
        You are a German teacher.

        Word: {word}
        Meaning: {translation}

        Task:
        - Write 2 short German sentences (A2-B1 level)
        - Add Turkish translation under each sentence
        - Everyday life context
        - Keep it simple

        Format:

        1. German sentence
        → Turkish translation

        2. German sentence
        → Turkish translation
    """

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        return f"AI Error (Gemini): {str(e)}"
    
def save_progress(word, status):
    p = st.session_state.progress
    prev = p.get(word, {})
    # Spaced repetition: interval hesapla
    intervals = {"easy": 7, "ok": 3, "hard": 1}
    next_review = datetime.date.today() + datetime.timedelta(days=intervals.get(status, 1))
    p[word] = {
        "status": status,
        "count": prev.get("count", 0) + 1,
        "last_seen": str(datetime.date.today()),
        "next_review": str(next_review),
        "streak": prev.get("streak", 0) + (1 if status == "easy" else 0),
    }
    # Streak güncelle
    today = str(datetime.date.today())
    if st.session_state.last_study_date != today:
        if st.session_state.last_study_date == str(datetime.date.today() - datetime.timedelta(days=1)):
            st.session_state.daily_streak += 1
        else:
            st.session_state.daily_streak = 1
        st.session_state.last_study_date = today
    # Eğer kullanıcı girişliyse, kalıcı olarak kaydet
    persist_current_user()

def get_due_words():
    """Spaced repetition: bugün tekrar edilmesi gerekenler"""
    today = str(datetime.date.today())
    all_w = WORDS + st.session_state.custom_words
    due = []
    for w in all_w:
        p = st.session_state.progress.get(w["word"], {})
        if not p:
            due.append(w)
        elif p.get("next_review", "0") <= today:
            due.append(w)
    return due

def filtered_words():
    ft = st.session_state.filter_type
    sq = st.session_state.search.lower().strip()
    all_w = WORDS + st.session_state.custom_words
    result = []
    for w in all_w:
        if ft != "Tümü" and w.get("type") != ft:
            continue
        if sq and sq not in w.get("word", "").lower() and sq not in w.get("translation", "").lower():
            continue
        # Tüm alanları koruyarak ekle
        result.append({
            "word": w.get("word", ""),
            "article": w.get("article", ""),
            "type": w.get("type", ""),
            "translation": w.get("translation", ""),
            "custom": w.get("custom", False)
        })
    return result

def start_flash():
    global_filter = st.session_state.get('filter_type', 'Tümü')
    
    all_filtered = filtered_words()
    
    # SADECE translation alanı olan kelimeleri al
    include_untr = st.session_state.get('flash_include_untranslated', False)
    if include_untr:
        deck_source = all_filtered
    else:
        deck_source = [w for w in all_filtered if w.get('translation') and w.get('translation') not in ("Çeviri yok", "—")]
    
    if not deck_source:
        st.warning(f"Seçili filtrelerde çalışılacak kelime bulunamadı. Filtreleri değiştirin.")
        st.session_state.flash_deck = []
        return
    
    comp = st.session_state.get('flash_comp')
    if comp and any(comp.values()):
        deck = build_deck_from_composition(deck_source, comp, 30)
    else:
        random.shuffle(deck_source)
        deck = deck_source[:30]
    
    # DEBUG: Kontrol et
    for w in deck[:3]:
        st.write(f"DEBUG Deck: {w.get('word')} -> translation={w.get('translation', 'YOK')}")
    
    st.session_state.flash_deck = deck
    st.session_state.flash_idx = 0
    st.session_state.flash_flipped = False
    st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
    st.session_state.ai_sentence = ""

def start_quiz():
    # Öncelikle çevirisi olan kelimelerden bir havuz oluştur
    # Use page-specific quiz filter; 'Karışık' means no filtering (mixed)
    qft = st.session_state.get('quiz_filter_type', 'Karışık')
    all_pool = filtered_words()
    # Respect global filter when page-specific is neutral
    effective_qft = qft
    if qft in ("Karışık", "Tümü"):
        effective_qft = st.session_state.get('filter_type', 'Tümü')
    if effective_qft not in ("Karışık", "Tümü"):
        all_pool = [w for w in all_pool if w.get('type') == effective_qft]
    include_untr_q = st.session_state.get('quiz_include_untranslated', False)
    if include_untr_q:
        pool = all_pool
    else:
        translated_pool = [w for w in all_pool if get_translation(w['word']) not in ("Çeviri yok", "—")]
        pool = translated_pool if len(translated_pool) >= 10 else all_pool
    comp = st.session_state.get('quiz_comp')
    if comp:
        deck = build_deck_from_composition(pool, comp, 20)
    else:
        random.shuffle(pool)
        deck = pool[:20]
    st.session_state.quiz_deck = deck
    st.session_state.quiz_idx = 0
    st.session_state.quiz_session = {"correct": 0, "wrong": 0}
    make_quiz_question()

def make_quiz_question():
    idx = st.session_state.quiz_idx
    deck = st.session_state.quiz_deck
    if idx >= len(deck):
        st.session_state.quiz_state = None
        return
    word = deck[idx]
    all_w = WORDS + st.session_state.custom_words
    # Yanlış seçenekleri de mümkünse çevirisi olanlardan seç
    candidates = [w for w in all_w if w["word"] != word["word"] and get_translation(w['word']) not in ("Çeviri yok", "—")]
    if len(candidates) < 3:
        candidates = [w for w in all_w if w["word"] != word["word"]]
    wrongs = random.sample(candidates, 3)
    options = random.sample([word] + wrongs, 4)
    st.session_state.quiz_state = {
        "word": word,
        "options": options,
        "answered": None,
        "correct": None,
    }

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🇩🇪 Goethe B1")
    st.markdown("---")
    # Kullanıcı girişi
    st.markdown("**Kullanıcı**")
    uname = st.text_input("Kullanıcı adı", value=st.session_state.get('current_user',''))
    if st.button("Giriş", use_container_width=True):
        users = load_users_file()
        st.session_state['users'] = users
        if uname and uname not in users:
            users[uname] = {'progress': {}, 'last_study_date': None, 'daily_streak': 0, 'total_study_minutes': 0, 'custom_words': []}
            save_users_file(users)
        if uname:
            load_user_data(uname)
        # After login, stay on Ana Sayfa and do not auto-start any deck
        st.session_state['page'] = 'Ana Sayfa'
        st.session_state['flash_deck'] = []
        st.session_state['quiz_deck'] = []
        st.rerun()

    pages = ["Ana Sayfa", "📇 Flashcard", "📝 Quiz", "📖 Kelime Listesi",
             "➕ Kelime Ekle", "📊 İstatistikler"]
    for pg in pages:
        if st.button(pg, use_container_width=True,
                     type="primary" if st.session_state.page == pg else "secondary"):
            st.session_state.page = pg
            st.rerun()

    st.markdown("---")
    # Filtre (sayılara sahip etiketler)
    st.markdown("**Filtre**")
    all_w = WORDS + st.session_state.custom_words
    counts_total = {
        'Verb': sum(1 for w in all_w if w.get('type') == 'Verb'),
        'Nomen': sum(1 for w in all_w if w.get('type') == 'Nomen'),
        'Adj/Adv': sum(1 for w in all_w if w.get('type') == 'Adj/Adv'),
    }
    total = len(all_w)
    # Görünür etiket metinleri (format_func ile gösterilecek)
    display_map = {
        'Tümü': f'Tümü ({total})',
        'Verb': f'Verb ({counts_total.get("Verb",0)})',
        'Nomen': f'Nomen ({counts_total.get("Nomen",0)})',
        'Adj/Adv': f'Adjective ({counts_total.get("Adj/Adv",0)})',
    }
    ft_keys = ['Tümü', 'Verb', 'Nomen', 'Adj/Adv']
    ft = st.selectbox("Kelime türü", ft_keys,
                      label_visibility="collapsed",
                      index=ft_keys.index(st.session_state.filter_type),
                      format_func=lambda x: display_map.get(x, x))
    if ft != st.session_state.filter_type:
        st.session_state.filter_type = ft
        st.rerun()

    st.markdown("---")
    p = st.session_state.progress
    seen = len(p)
    total = len(WORDS) + len(st.session_state.custom_words)
    pct = int(seen / total * 100) if total else 0
    st.markdown(f"**İlerleme: %{pct}**")
    st.progress(pct / 100)
    st.caption(f"{seen} / {total} kelime")
    streak = st.session_state.daily_streak
    if streak > 0:
        st.markdown(f"🔥 **{streak} günlük seri!**")

    st.markdown("---")
    # Çeviri kontrolü - diagnostic
    if st.button("Çeviri Kontrolü (Eksikler)", use_container_width=True):
        all_w = WORDS + st.session_state.custom_words
        missing = []
        per_type_missing = {"Verb":0, "Nomen":0, "Adj/Adv":0}
        for w in all_w:
            tr = get_translation(w.get('word',''))
            if tr in ("Çeviri yok", "—"):
                missing.append(w)
                t = w.get('type','')
                if t in per_type_missing:
                    per_type_missing[t] += 1
        st.markdown(f"**Toplam kelime:** {len(all_w)}")
        st.markdown(f"**Çevirisi eksik:** {len(missing)}")
        st.markdown(f"- Verb: {per_type_missing['Verb']} • Nomen: {per_type_missing['Nomen']} • Adj/Adv: {per_type_missing['Adj/Adv']}")
        if missing:
            sample = ', '.join([m['word'] for m in missing[:30]])
            st.markdown(f"**Örnek eksikler (ilk 30):** {sample}")
        else:
            st.markdown("Tüm kelimelerin çevirisi mevcut görünüyor.")

# ── Sayfa: Ana Sayfa ─────────────────────────────────────────────────────────
if st.session_state.page == "Ana Sayfa":
    st.markdown("# 🇩🇪 Goethe B1 Kelime Öğrenimi")
    st.markdown("Almanca öğrenme yolculuğuna hoş geldiniz!")

    p = st.session_state.progress
    total = len(WORDS) + len(st.session_state.custom_words)
    seen = len(p)
    hard = sum(1 for v in p.values() if v.get("status") == "hard")
    ok   = sum(1 for v in p.values() if v.get("status") == "ok")
    easy = sum(1 for v in p.values() if v.get("status") == "easy")
    due_today = len(get_due_words())

    # İstatistik kartları
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("📚 Toplam", total)
    with c2:
        st.metric("👀 Görülen", seen)
    with c3:
        st.metric("⏰ Bugün tekrar", due_today)
    with c4:
        st.metric("❌ Zor", hard)
    with c5:
        st.metric("✅ Öğrenildi", easy)

    st.markdown("---")

    # Progress bar
    pct = int(seen / total * 100) if total else 0
    st.markdown(f"#### Genel ilerleme: **%{pct}**")
    st.progress(pct / 100)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🃏 Flashcard Çalışması")
        st.markdown(f"Bugün **{due_today}** kelime tekrarı var.")
        if st.button("Flashcard Başlat 🚀", use_container_width=True, type="primary"):
            start_flash()
            st.session_state.page = "📇 Flashcard"
            st.rerun()

    with col2:
        st.markdown("### 📝 Quiz Modu")
        st.markdown("Çoktan seçmeli sorularla kendinizi test edin.")
        if st.button("Quiz Başlat 🎯", use_container_width=True, type="primary"):
            start_quiz()
            st.session_state.page = "📝 Quiz"
            st.rerun()

    st.markdown("---")
    # Günün kelimesi
    day_idx = datetime.date.today().toordinal() % total if total > 0 else 0
    all_w = WORDS + st.session_state.custom_words
    if all_w:
        day_word = all_w[day_idx]
        st.markdown("### 🌟 Günün Kelimesi")
        col1, col2 = st.columns([1, 2])
        with col1:
            article_color = {"der": "🔵", "die": "🔴", "das": "🟢", "": "⚪"}
            ic = article_color.get(day_word.get("article", ""), "⚪")
            st.markdown(f"## {ic} {get_display(day_word)}")
            st.markdown(f"*{day_word['type']}*")
        with col2:
            st.markdown(f"### {get_translation(day_word['word'])}")
            p_info = st.session_state.progress.get(day_word["word"], {})
            if p_info:
                status_icons = {"easy":"✅ Öğrenildi","ok":"🤔 Tekrar gerekiyor","hard":"❌ Zorlandınız"}
                st.caption(status_icons.get(p_info.get("status",""), ""))

# ── Sayfa: Flashcard ─────────────────────────────────────────────────────────
elif st.session_state.page == "📇 Flashcard":
    st.markdown("# 📇 Flashcard Çalışması")

    # Global sidebar filtresini göster
    global_filter = st.session_state.get('filter_type', 'Tümü')
    if global_filter != 'Tümü':
        st.info(f"🔍 **Global filtre: {global_filter}** seçili - Yalnızca {global_filter} türündeki kelimeler gösteriliyor.")
    
    if not st.session_state.flash_deck:
        st.info("Başlamak için aşağıdaki butona tıklayın.")
        
        # Mevcut kelime havuzunu göster
        pool = filtered_words()
        
        if global_filter != 'Tümü':
            pool = [w for w in pool if w.get('type') == global_filter]
        
        counts_total = {
            'Verb': sum(1 for w in pool if w.get('type') == 'Verb'),
            'Nomen': sum(1 for w in pool if w.get('type') == 'Nomen'),
            'Adj/Adv': sum(1 for w in pool if w.get('type') == 'Adj/Adv'),
        }
        
        st.markdown(f"**Mevcut havuz:** Verb: {counts_total['Verb']} • Nomen: {counts_total['Nomen']} • Adj/Adv: {counts_total['Adj/Adv']}")
        
        include_untr = st.checkbox('Çevirisi olmayanları da dahil et', value=st.session_state.get('flash_include_untranslated', False))
        st.session_state['flash_include_untranslated'] = include_untr
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Flashcard Başlat", type="primary", use_container_width=True):
                st.session_state['flash_comp'] = None
                start_flash()
                st.rerun()
        
        with col2:
            # Zorlu kelimeleri çalış butonu
            hard_words_count = sum(1 for v in st.session_state.progress.values() if v.get("status") == "hard")
            if hard_words_count > 0:
                if st.button(f"❌ Zorlu Kelimeler ({hard_words_count})", use_container_width=True):
                    hard_list = [w for w in WORDS + st.session_state.custom_words 
                                if w.get('word') in st.session_state.progress 
                                and st.session_state.progress[w.get('word')].get("status") == "hard"]
                    if hard_list:
                        # Global filtreyi de uygula
                        if global_filter != 'Tümü':
                            hard_list = [w for w in hard_list if w.get('type') == global_filter]
                        random.shuffle(hard_list)
                        st.session_state.flash_deck = hard_list[:30]
                        st.session_state.flash_idx = 0
                        st.session_state.flash_flipped = False
                        st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
                        st.session_state.page = "📇 Flashcard"
                        st.rerun()
                    else:
                        st.warning("Zorlu kelime yok.")
    else:
        # ... flashcard çalışma kısmı aynı kalıyor ...
        idx = st.session_state.flash_idx
        deck = st.session_state.flash_deck
        sess = st.session_state.flash_session
        
        if idx >= len(deck):
            # Tur bitti
            total_answered = sess["correct"] + sess["wrong"] + sess["skipped"]
            st.markdown("## 🎉 Tur Tamamlandı!")
            c1, c2, c3 = st.columns(3)
            c1.metric("✅ Bildim", sess["correct"])
            c2.metric("🔄 Tekrar", sess["wrong"])
            c3.metric("⏭️ Atladım", sess["skipped"])
            if total_answered:
                st.progress(sess["correct"] / total_answered)
            if st.button("🔄 Yeni Tur Başlat", type="primary"):
                start_flash()
                st.rerun()
            if st.button("🏠 Ana Sayfaya Dön"):
                st.session_state.page = "Ana Sayfa"
                st.rerun()
        else:
            # ... flashcard gösterim kısmı aynı kalıyor ...
            word = deck[idx]
            display = get_display(word)
            translation = get_translation(word["word"])
            flipped = st.session_state.flash_flipped

            # İlerleme
            prog = idx / len(deck)
            st.progress(prog)
            st.caption(f"Kart {idx+1} / {len(deck)}  |  ✅ {sess['correct']}  ❌ {sess['wrong']}  ⏭️ {sess['skipped']}")

            # Kart
            article = word.get("article", "")
            if article not in ("der", "die", "das"):
                article = ""
            art_class = f"article-{article}" if article else ""
            type_map = {"Verb": "Fiil", "Nomen": "İsim", "Adj/Adv": "Sıfat/Zarf"}
            raw_type = word.get("type", "")
            type_label = type_map.get(raw_type, raw_type)
            type_class = f"type-{raw_type}" if raw_type else "type-Unknown"

            if not flipped:
                art_html = f'<div class="{art_class}">{article}</div>' if article else ""
                front_html = f"""
                <div class="flashcard flashcard-front">
                    {art_html}
                    <div class="word-big">{word['word']}</div>
                    <span class="type-badge {type_class}">{type_label}</span>
                    <div style="margin-top:1rem; opacity:0.6; font-size:0.82rem">Anlamını görmek için tıkla 👆</div>
                </div>
                """
                st.html(front_html)  # ← st.markdown yerine st.html kullan
                if st.button("🔄 Çevir", use_container_width=True, type="primary"):
                    st.session_state.flash_flipped = True
                    st.rerun()
            else:
                # Arka yüz
                p_info = st.session_state.progress.get(word["word"], {})
                count = p_info.get("count", 0)
                
                # DEBUG: Çeviriyi kontrol et

 
                translation = get_translation(word["word"])
                
                back_html = f"""
                <div class="flashcard flashcard-back">
                    <div style="opacity:0.7; font-size:1rem; margin-bottom:0.3rem">{display}</div>
                    <div class="word-tr">{translation}</div>
                    {f'<div style="font-size:0.85rem; opacity:0.6; margin-top:0.5rem">Daha önce {count}× görüldü</div>' if count else ""}
                </div>
                """
                st.markdown(back_html, unsafe_allow_html=True)

                # AI Örnek Cümle
                # ai_col1, ai_col2 = st.columns([3, 1])
                # with ai_col2:
                #     ai_text = None
                #     if st.button("🤖 AI Örnek Cümle", use_container_width=True):

                #         with st.spinner("AI cümle üretiyor..."):

                #             try:

                #                 ai_text = generate_ai_example(
                #                     word["word"],
                #                     translation
                #                 )

                #                 st.session_state.ai_sentence = ai_text

                #                 p = st.session_state.progress.get(word['word'], {})
                #                 p['ai_example'] = ai_text
                #                 st.session_state.progress[word['word']] = p

                #                 persist_current_user()

                #             except Exception as e:

                #                 st.session_state.ai_sentence = f"Hata: {e}"

                #         st.rerun()

                # ai_saved = st.session_state.ai_sentence

                # if ai_text:
                #     st.markdown(f"""
                #     <div class="ai-box">
                #         {ai_text.replace(chr(10), "<br>")}
                #     </div>
                #     """, unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("**Bu kelimeyi nasıl buldunuz?**")
                c1, c2, c3, c4 = st.columns(4)
                
                def rate(status, sess_key):
                     save_progress(word["word"], status)
                     st.session_state.flash_session[sess_key] += 1
                     st.session_state.flash_idx += 1
                     st.session_state.flash_flipped = False
                     st.session_state.ai_sentence = ""
                     st.rerun()

                with c1:
                    if st.button("✅ Bildim", use_container_width=True, type="primary"):
                        rate("easy", "correct")
                with c2:
                    if st.button("🤔 Zorlandım", use_container_width=True):
                        rate("ok", "wrong")
                with c3:
                    if st.button("❌ Bilmedim", use_container_width=True):
                        rate("hard", "wrong")
                with c4:
                    if st.button("⏭️ Atla", use_container_width=True):
                        st.session_state.flash_session["skipped"] += 1
                        st.session_state.flash_idx += 1
                        st.session_state.flash_flipped = False
                        st.session_state.ai_sentence = ""
                        st.rerun()
# ── Sayfa: Quiz ───────────────────────────────────────────────────────────────
elif st.session_state.page == "📝 Quiz":
    st.markdown("# 📝 Quiz Modu")

    if not st.session_state.quiz_deck:
        st.info("Quiz başlatmak için butona tıklayın.")
        # Sayfa-bazlı tür seçici (karışık dahil)
        global_qft = st.session_state.get('filter_type', 'Tümü')
        if global_qft != 'Tümü':
            st.info(f"Global filtre: {global_qft} seçili — yalnızca bu türe ait sorular gösterilecek.")
            qopt = global_qft
            st.session_state['quiz_filter_type'] = qopt
        else:
            qopt = st.selectbox("Tür seçimi", ["Karışık", "Tümü", "Verb", "Nomen", "Adj/Adv"], index=["Karışık","Tümü","Verb","Nomen","Adj/Adv"].index(st.session_state.get('quiz_filter_type','Karışık')))
            if qopt != st.session_state.get('quiz_filter_type'):
                st.session_state['quiz_filter_type'] = qopt

        # Havuz ve mevcut sayılar (toplam ve çeviri olan)
        pool = filtered_words()
        if qopt not in ("Karışık", "Tümü"):
            pool = [w for w in pool if w.get('type') == qopt]
        counts_total = {
            'Verb': sum(1 for w in pool if w.get('type') == 'Verb'),
            'Nomen': sum(1 for w in pool if w.get('type') == 'Nomen'),
            'Adj/Adv': sum(1 for w in pool if w.get('type') == 'Adj/Adv'),
        }
        counts_trans = {
            'Verb': sum(1 for w in pool if w.get('type') == 'Verb' and get_translation(w.get('word','')) not in ("Çeviri yok","—")),
            'Nomen': sum(1 for w in pool if w.get('type') == 'Nomen' and get_translation(w.get('word','')) not in ("Çeviri yok","—")),
            'Adj/Adv': sum(1 for w in pool if w.get('type') == 'Adj/Adv' and get_translation(w.get('word','')) not in ("Çeviri yok","—")),
        }
        st.markdown(f"**Mevcut havuz:** Verb: {counts_total['Verb']} ({counts_trans['Verb']} çeviri) • Nomen: {counts_total['Nomen']} ({counts_trans['Nomen']} çeviri) • Adj/Adv: {counts_total['Adj/Adv']} ({counts_trans['Adj/Adv']} çeviri)")
        include_untr_q = st.checkbox('Çevirisi olmayanları da dahil et', value=st.session_state.get('quiz_include_untranslated', False))
        st.session_state['quiz_include_untranslated'] = include_untr_q

        comp_def = st.session_state.get('quiz_comp') or {'Verb':0,'Nomen':0,'Adj/Adv':0}
        max_v = counts_total['Verb'] if include_untr_q else counts_trans['Verb']
        max_n = counts_total['Nomen'] if include_untr_q else counts_trans['Nomen']
        max_a = counts_total['Adj/Adv'] if include_untr_q else counts_trans['Adj/Adv']

        # Eğer global sidebar filtresi belirli bir türe sabitlenmişse, doğrudan o türe ait tüm soruları başlat
        global_qft = st.session_state.get('filter_type', 'Tümü')
        if global_qft != 'Tümü':
            sel = global_qft
            counts_map = {'Verb': max_v, 'Nomen': max_n, 'Adj/Adv': max_a}
            sel_count = counts_map.get(sel, 0)
            st.markdown(f"**Global filtre: {sel} seçili — {sel_count} soru havuzuyla çalışacaksınız.**")
            if st.button(f"{sel} türündeki tüm soruları başlat ({sel_count})", type="primary"):
                comp = {'Verb':0,'Nomen':0,'Adj/Adv':0}
                if sel in comp:
                    comp[sel] = sel_count
                st.session_state['quiz_comp'] = comp
                st.session_state['quiz_include_untranslated'] = include_untr_q
                start_quiz()
                st.session_state.page = "📝 Quiz"
                st.rerun()
        else:
            qv1 = st.number_input('Verb sayısı', min_value=0, max_value=max_v, value=int(comp_def.get('Verb',0)))
            qv2 = st.number_input('Nomen sayısı', min_value=0, max_value=max_n, value=int(comp_def.get('Nomen',0)))
            qv3 = st.number_input('Adj/Adv sayısı', min_value=0, max_value=max_a, value=int(comp_def.get('Adj/Adv',0)))
            q_total = qv1 + qv2 + qv3
            st.markdown(f"Toplam seçili: **{q_total}** / 20")

            if st.button("Ayarla ve Başlat (Özel)"):
                if q_total > 0:
                    st.session_state['quiz_comp'] = {'Verb':qv1,'Nomen':qv2,'Adj/Adv':qv3}
                else:
                    st.session_state['quiz_comp'] = None
                st.session_state['quiz_include_untranslated'] = include_untr_q
                start_quiz()
                st.session_state.page = "📝 Quiz"
                st.rerun()

            if st.button("Karışık Başlat 🎯", type="primary"):
                st.session_state['quiz_comp'] = None
                st.session_state['quiz_include_untranslated'] = include_untr_q
                start_quiz()
                st.rerun()
    else:
        idx  = st.session_state.quiz_idx
        deck = st.session_state.quiz_deck
        sess = st.session_state.quiz_session
        qs   = st.session_state.quiz_state

        if qs is None or idx >= len(deck):
            # Sonuç
            total_q = len(deck)
            score = sess["correct"]
            pct = int(score / total_q * 100) if total_q else 0
            emoji = "🏆" if pct >= 80 else "💪" if pct >= 50 else "📚"
            st.markdown(f"## {emoji} Quiz Tamamlandı!")
            c1, c2, c3 = st.columns(3)
            c1.metric("✅ Doğru", sess["correct"])
            c2.metric("❌ Yanlış", sess["wrong"])
            c3.metric("🎯 Başarı", f"%{pct}")
            st.progress(pct / 100)
            if st.button("🔄 Tekrar Dene", type="primary"):
                start_quiz()
                st.rerun()
            if st.button("🏠 Ana Sayfaya Dön"):
                st.session_state.page = "Ana Sayfa"
                st.rerun()
        else:
            word = qs["word"]
            display = get_display(word)
            translation = get_translation(word["word"])

            st.progress(idx / len(deck))
            st.caption(f"Soru {idx+1} / {len(deck)}  |  ✅ {sess['correct']}  ❌ {sess['wrong']}")

            st.markdown(f"### Bu kelimenin Türkçe anlamı nedir?")
            article = word.get("article", "")
            art_color = {"der": "🔵", "die": "🔴", "das": "🟢", "": ""}
            art_ic = art_color.get(article, "")
            st.markdown(f"## {art_ic} {display}  `{word['type']}`")
            st.markdown("---")

            answered = qs.get("answered")
            for opt in qs["options"]:
                opt_tr = get_translation(opt["word"])
                if opt_tr in ("—", "Çeviri yok"):
                    opt_tr = opt["word"]
                is_correct_opt = opt["word"] == word["word"]
                is_chosen = answered == opt["word"]

                if answered is None:
                    if st.button(opt_tr, use_container_width=True, key=f"opt_{opt['word']}"):
                        correct = opt["word"] == word["word"]
                        qs["answered"] = opt["word"]
                        qs["correct"] = correct
                        if correct:
                            sess["correct"] += 1
                        else:
                            sess["wrong"] += 1
                        save_progress(word["word"], "easy" if correct else "hard")
                        st.rerun()
                else:
                    if is_correct_opt:
                        st.success(f"✅ {opt_tr}")
                    elif is_chosen:
                        st.error(f"❌ {opt_tr}  ← seçtiğiniz")
                    else:
                        st.button(opt_tr, use_container_width=True, disabled=True, key=f"opt_d_{opt['word']}")

            if answered:
                if qs["correct"]:
                    st.success("🎉 Doğru!")
                else:
                    st.error(f"Doğru cevap: **{translation}**")
                if st.button("Sonraki Soru ➡️", type="primary"):
                    st.session_state.quiz_idx += 1
                    make_quiz_question()
                    st.rerun()

# ── Sayfa: Kelime Listesi ─────────────────────────────────────────────────────
elif st.session_state.page == "📖 Kelime Listesi":
    st.markdown("# 📖 Kelime Listesi")

    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Ara (Almanca veya Türkçe)", value=st.session_state.search,
                               placeholder="Kelime ara...", label_visibility="collapsed")
        if search != st.session_state.search:
            st.session_state.search = search
            st.rerun()
    with col2:
        ft_map = {"Tümü":"Tümü","Verb":"Fiiller","Nomen":"İsimler","Adj/Adv":"Sıfat/Zarf"}
        ft = st.selectbox("Tür", list(ft_map.keys()), format_func=lambda x: ft_map[x],
                          label_visibility="collapsed",
                          index=list(ft_map.keys()).index(st.session_state.filter_type))
        if ft != st.session_state.filter_type:
            st.session_state.filter_type = ft
            st.rerun()

    fw = filtered_words()
    st.caption(f"**{len(fw)}** kelime gösteriliyor")

    status_icon = {"easy":"✅","ok":"🤔","hard":"❌"}
    article_color = {"der":"🔵","die":"🔴","das":"🟢","":"⚪"}

    # Sayfalama
    PAGE_SIZE = 50
    if "list_page" not in st.session_state:
        st.session_state.list_page = 0
    total_pages = (len(fw) - 1) // PAGE_SIZE + 1 if fw else 1
    start = st.session_state.list_page * PAGE_SIZE
    page_words = fw[start:start + PAGE_SIZE]

    # Tablo başlığı
    h1, h2, h3, h4, h5 = st.columns([0.5, 2, 2, 1.5, 1])
    h1.markdown("**#**")
    h2.markdown("**Almanca**")
    h3.markdown("**Türkçe**")
    h4.markdown("**Tür**")
    h5.markdown("**Durum**")
    st.markdown("<hr style='margin:4px 0'>", unsafe_allow_html=True)

    for i, w in enumerate(page_words, start=start + 1):
        c1, c2, c3, c4, c5 = st.columns([0.5, 2, 2, 1.5, 1])
        p_info = st.session_state.progress.get(w["word"], {})
        status = p_info.get("status", "")
        art = w.get("article","")
        c1.write(i)
        c2.write(f"{article_color.get(art,'⚪')} **{art} {w['word']}**" if art else f"**{w['word']}**")
        c3.write(get_translation(w["word"]))
        c4.write(w["type"])
        c5.write(status_icon.get(status, "—"))

    # Sayfalama butonları
    if total_pages > 1:
        st.markdown("---")
        pc1, pc2, pc3 = st.columns([1, 2, 1])
        with pc1:
            if st.session_state.list_page > 0:
                if st.button("◀ Önceki"):
                    st.session_state.list_page -= 1
                    st.rerun()
        with pc2:
            st.markdown(f"<p style='text-align:center'>Sayfa {st.session_state.list_page+1} / {total_pages}</p>",
                        unsafe_allow_html=True)
        with pc3:
            if st.session_state.list_page < total_pages - 1:
                if st.button("Sonraki ▶"):
                    st.session_state.list_page += 1
                    st.rerun()

# ── Sayfa: Kelime Ekle ────────────────────────────────────────────────────────
elif st.session_state.page == "➕ Kelime Ekle":
    st.markdown("# ➕ Yeni Kelime Ekle")
    st.info("Kendi kelimelerinizi listeye ekleyebilirsiniz.")

    with st.form("add_word_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_word = st.text_input("Almanca Kelime *", placeholder="z.B. lernen")
            new_article = st.selectbox("Artikel", ["", "der", "die", "das"])
            new_type = st.selectbox("Tür", ["Verb", "Nomen", "Adj/Adv"])
        with col2:
            new_tr = st.text_input("Türkçe Anlamı *", placeholder="öğrenmek")
            new_notes = st.text_area("Notlar (isteğe bağlı)", placeholder="Ek bilgiler...")

        submitted = st.form_submit_button("➕ Kelime Ekle", type="primary")
        if submitted:
            if not new_word.strip() or not new_tr.strip():
                st.error("Kelime ve Türkçe anlam zorunludur.")
            else:
                entry = {
                    "word": new_word.strip(), 
                    "article": new_article,
                    "type": new_type, 
                    "translation": new_tr.strip(),
                    "custom": True,
                    "notes": new_notes.strip() if new_notes else ""
                }
                st.session_state.custom_words.append(entry)
                st.success(f"✅ '{new_article} {new_word}' başarıyla eklendi!")
                persist_current_user()
                st.rerun()

    if st.session_state.custom_words:
        st.markdown("---")
        st.markdown("### 📋 Eklediğiniz Kelimeler")
        for i, w in enumerate(st.session_state.custom_words):
            c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
            c1.write(f"**{get_display(w)}**")
            c2.write(get_translation(w["word"]))
            c3.write(w["type"])
            if c4.button("🗑️", key=f"del_{i}"):
                st.session_state.custom_words.pop(i)
                persist_current_user()
                st.rerun()

    st.markdown("---")
    st.markdown("### 📤 CSV ile Toplu İçe Aktarma")
    st.markdown("**Format:** `kelime,anlam,tür,artikel`  (örnek: `machen,yapmak,Verb,`)")
    uploaded = st.file_uploader("CSV Dosyası Yükle", type=["csv", "txt"])
    if uploaded:
        import io
        content = uploaded.read().decode("utf-8")
        lines = content.strip().split("\n")
        added = 0
        errors = []
        for line in lines:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2:
                w_word = parts[0]
                w_tr = parts[1]
                w_type = parts[2] if len(parts) > 2 else "Verb"
                w_art = parts[3] if len(parts) > 3 else ""
                entry = {
                    "word": w_word, 
                    "article": w_art, 
                    "type": w_type, 
                    "translation": w_tr,
                    "custom": True
                }
                st.session_state.custom_words.append(entry)
                added += 1
            else:
                errors.append(line)
        st.success(f"✅ {added} kelime eklendi!")
        if errors:
            st.warning(f"Atlandı: {errors[:5]}")
        persist_current_user()
        st.rerun()

# ── Sayfa: İstatistikler ──────────────────────────────────────────────────────
elif st.session_state.page == "📊 İstatistikler":
    st.markdown("# 📊 İstatistikler ve İlerleme")

    p = st.session_state.progress
    total = len(WORDS) + len(st.session_state.custom_words)
    seen  = len(p)
    hard  = sum(1 for v in p.values() if v.get("status") == "hard")
    ok    = sum(1 for v in p.values() if v.get("status") == "ok")
    easy  = sum(1 for v in p.values() if v.get("status") == "easy")
    unseen = total - seen
    due   = len(get_due_words())

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

    chart_data = [
        {"Durum": "Öğrenildi ✅", "Adet": easy,  "Renk": "#27ae60"},
        {"Durum": "Çalışılıyor 🤔","Adet": ok,   "Renk": "#f39c12"},
        {"Durum": "Zorlu ❌",       "Adet": hard, "Renk": "#e74c3c"},
        {"Durum": "Görülmedi",      "Adet": unseen,"Renk":"#95a5a6"},
    ]
    if any(d["Adet"] > 0 for d in chart_data):
        st.bar_chart({d["Durum"]: d["Adet"] for d in chart_data})

    st.markdown("---")
    st.markdown("### Türe Göre Dağılım")
    type_stats = {}
    for w in WORDS + st.session_state.custom_words:
        t = w["type"]
        pi = p.get(w["word"], {})
        st_val = pi.get("status", "unseen")
        if t not in type_stats:
            type_stats[t] = {"total":0,"easy":0,"ok":0,"hard":0,"unseen":0}
        type_stats[t]["total"] += 1
        type_stats[t][st_val] += 1

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
            wobj = next((w for w in WORDS + st.session_state.custom_words if w["word"] == word), None)
            if wobj:
                disp = get_display(wobj)
                tr   = get_translation(word)
                cnt  = info.get("count", 0)
                col1, col2, col3 = st.columns([2, 2, 1])
                col1.write(f"**{disp}**")
                col2.write(tr)
                col3.write(f"❌ {cnt}×")
    else:
        st.info("Henüz zorlu kelime yok. Harika gidiyorsunuz! 🎉")

    st.markdown("---")
    st.markdown("### ⚡ Hızlı Eylemler")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Zorlu kelimeleri çalış", use_container_width=True, type="primary"):
            hard_list = [next((w for w in WORDS + st.session_state.custom_words if w["word"] == word), None)
                         for word, info in p.items() if info.get("status") == "hard"]
            hard_list = [w for w in hard_list if w]
            if hard_list:
                random.shuffle(hard_list)
                st.session_state.flash_deck = hard_list[:25]
                st.session_state.flash_idx = 0
                st.session_state.flash_flipped = False
                st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
                st.session_state.page = "📇 Flashcard"
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