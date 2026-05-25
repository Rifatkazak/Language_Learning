import streamlit as st
import json
import random
import time
import html as _html
import datetime
import os
from pathlib import Path
from pathlib import Path as _Path

from ai_service import deepseek

# ── Sayfa Ayarları ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Goethe B1 Kelime Öğrenimi",
    page_icon="🇩🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from dotenv import load_dotenv
    load_dotenv()  # .env dosyasını oku
    print("✅ .env file loaded")
except ImportError:
    print("⚠️ python-dotenv not installed, using system env only")
except Exception as e:
    print(f"⚠️ Error loading .env: {e}")

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

/* Mobil touch hedefleri büyüt */
@media (max-width: 768px) {
    .stButton > button {
        min-height: 52px !important;
        font-size: 1rem !important;
        padding: 12px 16px !important;
    }
    
    /* Ana container genişlik */
    .main .block-container {
        padding: 0.5rem !important;
        max-width: 100% !important;
    }
    
    /* Flashcard mobil boyut */
    .flashcard {
        min-height: 200px !important;
        padding: 1.5rem 1rem !important;
    }
    
    .word-big {
        font-size: 2rem !important;
    }
    
    /* Sidebar toggle daha kolay */
    [data-testid="stSidebarNav"] {
        display: none;
    }
}

/* Swipe indicator */
.swipe-hint {
    text-align: center;
    color: #bbb;
    font-size: 0.75rem;
    padding: 4px;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
}

/* Büyük action buttons */
.action-btn-container {
    position: sticky;
    bottom: 0;
    background: white;
    padding: 12px;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    z-index: 100;
}
            
</style>
""", unsafe_allow_html=True)

if deepseek.is_available():
    st.sidebar.success("✅ AI Hizmeti Aktif")
    
    # Test butonu
    if st.sidebar.button("🧪 Test AI"):
        test_result = deepseek.generate_example_sentences("zuverlässig", "güvenilir", "B1")
        st.sidebar.code(test_result)
else:
    st.sidebar.error("❌ AI Hizmeti Pasif - API anahtarı bulunamadı")
    st.sidebar.info("Lütfen DEEPSEEK_API_KEY ayarlayın")

def render_bottom_nav():
    """Mobil için alt navigasyon"""
    pages = [
        ("🏠", "Ana Sayfa"),
        ('⚡', '⚡ Hızlı Aksiyonlar'),
        ("📇", "📇 Flashcard"),
        ("📝", "📝 Quiz"),
        ("🎮", "🎮 Kelime Oyunu"),
        ('🏆', '🏆 Haftalık Challange'),
        ("📖", "📖 Kelime Listesi"),
        ("➕", "➕ Kelime Ekle"),
        ("📊", "📊 İstatistikler"),
    ]
    cols = st.columns(len(pages))
    for col, (icon, page) in zip(cols, pages):
        with col:
            is_active = st.session_state.page == page
            btn_type = "primary" if is_active else "secondary"
            if st.button(icon, use_container_width=True, 
                        type=btn_type, key=f"nav_{page}"):
                st.session_state.page = page
                st.rerun()

# ── Veri Yükleme ────────────────────────────────────────────────────────────
@st.cache_data
def load_words():
    path = Path(__file__).parent / "words.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)

WORDS = load_words()


def calculate_priority_score(word: dict, progress: dict) -> float:
    """
    Düşük skor = daha önce göster
    """
    import datetime
    
    word_text = word.get("word", "")
    p = progress.get(word_text, {})
    
    if not p:
        return 0.0  # Hiç görülmemiş → en önce
    
    today = datetime.date.today()
    
    # Temel faktörler
    status = p.get("status", "unseen")
    count = p.get("count", 0)
    streak = p.get("streak", 0)
    
    # next_review tarihi geçmişse kritik
    next_review_str = p.get("next_review", str(today))
    next_review = datetime.date.fromisoformat(next_review_str)
    days_overdue = (today - next_review).days
    
    # Skor hesapla (düşük = önce göster)
    status_weights = {"hard": -10, "ok": 0, "easy": 5}
    base_score = status_weights.get(status, 0)
    
    # Vade geçmişse büyük öncelik
    overdue_bonus = -days_overdue * 2 if days_overdue > 0 else 0
    
    # Streak fazlaysa ertelenebilir  
    streak_delay = streak * 1.5
    
    return base_score + overdue_bonus + streak_delay

def build_adaptive_deck(pool: list, progress: dict, size: int = 30) -> list:
    """Öncelik skoruna göre sıralanmış deste"""
    scored = [(w, calculate_priority_score(w, progress)) for w in pool]
    scored.sort(key=lambda x: x[1])  # En düşük skor önce
    
    # İlk %70 kritik kelimeler, %30 rastgele yeni
    critical_count = int(size * 0.7)
    random_count = size - critical_count
    
    critical = [w for w, _ in scored[:critical_count]]
    remaining = [w for w, _ in scored[critical_count:]]
    
    import random
    random_sample = random.sample(remaining, min(random_count, len(remaining)))
    
    deck = critical + random_sample
    random.shuffle(deck)
    return deck[:size]

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
    """DeepSeek API ile örnek cümle üret"""
    return deepseek.generate_example_sentences(word, translation, "B1")
    
def save_progress(word: str, status: str):
    """Genişletilmiş - tüm sistemi günceller"""
    p = st.session_state.progress
    prev = p.get(word, {})
    
    intervals = {"easy": 7, "ok": 3, "hard": 1}
    import datetime
    next_review = datetime.date.today() + datetime.timedelta(
        days=intervals.get(status, 1)
    )
    
    p[word] = {
        "status": status,
        "count": prev.get("count", 0) + 1,
        "last_seen": str(datetime.date.today()),
        "next_review": str(next_review),
        "streak": prev.get("streak", 0) + (1 if status == "easy" else 0),
        "ai_example": prev.get("ai_example"),  # Koru
    }
    
    # Streak güncelle
    streak_result = check_and_update_streak()
    if streak_result.get("milestone_reached"):
        st.toast(f"🏆 {streak_result['milestone_reached']} günlük seri!", icon="🔥")
    
    # XP hesapla
    xp_map = {"easy": 10, "ok": 5, "hard": 3}
    xp = xp_map.get(status, 5)
    st.session_state.total_xp = st.session_state.get("total_xp", 0) + xp
    
    # Günlük görev güncelle
    update_task_progress("flashcard_daily")
    if status in ("easy", "hard"):  # hard review
        update_task_progress("hard_review")
    
    # Rozet kontrol
    new_badges = check_achievements()
    show_achievement_popup(new_badges)
    
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

def check_and_update_streak() -> dict:
    """
    Returns: {
        "current_streak": int,
        "milestone_reached": int | None,  # 7, 30, 100 gün milestones
        "streak_broken": bool,
        "grace_period_available": bool
    }
    """
    import datetime
    
    today = datetime.date.today()
    today_str = str(today)
    yesterday_str = str(today - datetime.timedelta(days=1))
    
    last_date = st.session_state.get("last_study_date")
    current_streak = st.session_state.get("daily_streak", 0)
    grace_used = st.session_state.get("grace_period_used", False)
    
    result = {
        "current_streak": current_streak,
        "milestone_reached": None,
        "streak_broken": False,
        "grace_period_available": False
    }
    
    if last_date == today_str:
        return result  # Bugün zaten çalışıldı
    
    if last_date == yesterday_str:
        # Seri devam ediyor
        new_streak = current_streak + 1
        st.session_state.daily_streak = new_streak
        st.session_state.last_study_date = today_str
        result["current_streak"] = new_streak
        
        # Milestone kontrolü
        milestones = [3, 7, 14, 30, 50, 100]
        if new_streak in milestones:
            result["milestone_reached"] = new_streak
            # Başarı rozeti ekle
            achievements = st.session_state.get("achievements", [])
            achievements.append({
                "type": "streak",
                "value": new_streak,
                "date": today_str
            })
            st.session_state.achievements = achievements
    
    elif last_date:
        # Seri kopmuş
        days_missed = (today - datetime.date.fromisoformat(last_date)).days
        
        # Grace period: 1 günlük af hakkı (30+ streak'te)
        if current_streak >= 30 and not grace_used and days_missed == 2:
            result["grace_period_available"] = True
        else:
            result["streak_broken"] = current_streak > 3  # 3+ günse bildir
            if not result["grace_period_available"]:
                st.session_state.daily_streak = 1
                st.session_state.last_study_date = today_str
    else:
        # İlk kez çalışıyor
        st.session_state.daily_streak = 1
        st.session_state.last_study_date = today_str
    
    persist_current_user()
    return result

def render_streak_widget():
    """Sidebar veya ana sayfada streak gösterimi"""
    streak = st.session_state.get("daily_streak", 0)
    
    if streak == 0:
        st.info("🌱 Bugün çalışmaya başla!")
        return
    
    # Ateş animasyonu (emoji tabanlı)
    fire_emojis = {
        range(1, 4): "🌱",
        range(4, 8): "🔥",
        range(8, 15): "🔥🔥",
        range(15, 31): "⚡🔥",
        range(31, 101): "🏆🔥",
    }
    
    fire = "🔥"
    for r, emoji in fire_emojis.items():
        if streak in r:
            fire = emoji
            break
    
    # Streak bar (7 günlük görünüm)
    import datetime
    today = datetime.date.today()
    
    st.markdown(f"### {fire} {streak} Günlük Seri!")
    
    # Son 7 günün durumu
    days_html = ""
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        day_str = str(day)
        day_name = ["Pt", "Sa", "Ça", "Pe", "Cu", "Ct", "Pz"][day.weekday()]
        
        # O gün çalışıldı mı?
        studied = any(
            v.get("last_seen") == day_str 
            for v in st.session_state.progress.values()
        )
        
        color = "#27ae60" if studied else ("#f39c12" if i == 0 else "#e0e0e0")
        emoji = "✅" if studied else ("👆" if i == 0 else "○")
        
        days_html += f"""
        <div style="text-align:center; padding:4px;">
            <div style="width:32px; height:32px; border-radius:50%; 
                        background:{color}; display:flex; align-items:center; 
                        justify-content:center; font-size:0.7rem; color:white;
                        margin:auto;">{emoji}</div>
            <div style="font-size:0.65rem; color:#888; margin-top:2px;">{day_name}</div>
        </div>
        """
    
    st.markdown(
        f'<div style="display:flex; justify-content:space-around; '
        f'background:#f8f9fa; border-radius:12px; padding:8px;">{days_html}</div>',
        unsafe_allow_html=True
    )

def generate_daily_tasks() -> list:
    """Her gün dinamik görevler oluştur"""
    import datetime
    
    today_str = str(datetime.date.today())
    
    # Bugünün görevleri zaten oluşturulduysa döndür
    cached_tasks = st.session_state.get("daily_tasks", {})
    if cached_tasks.get("date") == today_str:
        return cached_tasks.get("tasks", [])
    
    p = st.session_state.progress
    total_words = len(WORDS) + len(st.session_state.custom_words)
    hard_count = sum(1 for v in p.values() if v.get("status") == "hard")
    seen_count = len(p)
    
    tasks = []
    
    # Görev 1: Temel flashcard
    daily_target = min(20, max(10, hard_count + 5))
    tasks.append({
        "id": "flashcard_daily",
        "title": f"{daily_target} Flashcard Çalış",
        "description": f"Bugün {daily_target} kelime çalış",
        "icon": "📇",
        "xp": 50,
        "target": daily_target,
        "current": 0,
        "type": "flashcard",
        "completed": False
    })
    
    # Görev 2: Quiz
    tasks.append({
        "id": "quiz_daily",
        "title": "10 Quiz Sorusu Çöz",
        "description": "Bilgini test et",
        "icon": "📝",
        "xp": 40,
        "target": 10,
        "current": 0,
        "type": "quiz",
        "completed": False
    })
    
    # Görev 3: Zorlu kelimeler (varsa)
    if hard_count >= 3:
        tasks.append({
            "id": "hard_words",
            "title": f"{min(5, hard_count)} Zorlu Kelimeyi Tekrarla",
            "description": "❌ işaretli kelimeleri çalış",
            "icon": "💪",
            "xp": 60,
            "target": min(5, hard_count),
            "current": 0,
            "type": "hard_review",
            "completed": False
        })
    
    # Görev 4: Haftalık bonus (Pazar)
    import datetime
    if datetime.date.today().weekday() == 6:  # Pazar
        tasks.append({
            "id": "weekly_review",
            "title": "Haftalık Büyük Test (30 Soru)",
            "description": "Haftanın tüm kelimelerini test et",
            "icon": "🏆",
            "xp": 150,
            "target": 30,
            "current": 0,
            "type": "weekly",
            "completed": False
        })
    
    st.session_state.daily_tasks = {
        "date": today_str,
        "tasks": tasks,
        "total_xp_earned": 0
    }
    persist_current_user()
    return tasks

def update_task_progress(task_type: str, increment: int = 1):
    """Görev ilerlemesini güncelle"""
    tasks_data = st.session_state.get("daily_tasks", {})
    tasks = tasks_data.get("tasks", [])
    
    xp_earned = 0
    for task in tasks:
        if task["type"] == task_type and not task["completed"]:
            task["current"] = min(task["current"] + increment, task["target"])
            if task["current"] >= task["target"]:
                task["completed"] = True
                xp_earned += task["xp"]
                st.balloons()  # 🎈
    
    # XP ekle
    if xp_earned > 0:
        current_xp = st.session_state.get("total_xp", 0)
        st.session_state.total_xp = current_xp + xp_earned
        tasks_data["total_xp_earned"] = tasks_data.get("total_xp_earned", 0) + xp_earned
        st.session_state.daily_tasks = tasks_data
        persist_current_user()
    
    return xp_earned

def render_daily_tasks():
    """Ana sayfada görev paneli"""
    tasks = generate_daily_tasks()
    
    st.markdown("### 📋 Günlük Görevler")
    
    total_xp = sum(t["xp"] for t in tasks)
    earned_xp = sum(t["xp"] for t in tasks if t["completed"])
    
    st.progress(earned_xp / total_xp if total_xp else 0)
    st.caption(f"⚡ {earned_xp} / {total_xp} XP kazanıldı")
    
    for task in tasks:
        with st.container():
            col1, col2, col3 = st.columns([0.5, 3, 1])
            
            with col1:
                st.markdown(f"### {task['icon']}")
            
            with col2:
                if task["completed"]:
                    st.markdown(f"~~{task['title']}~~ ✅")
                else:
                    st.markdown(f"**{task['title']}**")
                    prog = task["current"] / task["target"] if task["target"] else 0
                    st.progress(prog)
                    st.caption(f"{task['current']}/{task['target']}")
            
            with col3:
                st.markdown(f"**+{task['xp']} XP**")
def start_flash():
    pool = filtered_words()
    if not st.session_state.get('flash_include_untranslated', False):
        pool = [w for w in pool if w.get('translation') not in ("Çeviri yok", "—", None, "")]
    
    comp = st.session_state.get('flash_comp')
    if comp and any(comp.values()):
        deck = build_deck_from_composition(pool, comp, 30)
    else:
        # Adaptive deck kullan
        deck = build_adaptive_deck(pool, st.session_state.progress, 30)
    
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

ACHIEVEMENTS = {
    # Streak rozetleri
    "streak_3": {"title": "🔥 İlk Alev", "desc": "3 günlük seri", "xp": 30},
    "streak_7": {"title": "⚡ Haftalık Kahraman", "desc": "7 günlük seri", "xp": 100},
    "streak_30": {"title": "🏆 Aylık Efsane", "desc": "30 günlük seri", "xp": 500},
    
    # Kelime rozetleri
    "words_50": {"title": "📚 Başlangıç", "desc": "50 kelime öğrenildi", "xp": 50},
    "words_100": {"title": "📖 Öğrenci", "desc": "100 kelime öğrenildi", "xp": 150},
    "words_250": {"title": "🎓 Kapsamlı", "desc": "250 kelime öğrenildi", "xp": 300},
    "words_500": {"title": "🌟 Uzman", "desc": "500 kelime öğrenildi", "xp": 750},
    
    # Quiz rozetleri
    "quiz_perfect": {"title": "💯 Mükemmel", "desc": "Quiz'den 100% aldın", "xp": 75},
    "quiz_100": {"title": "🧠 Quiz Ustası", "desc": "100 quiz sorusu", "xp": 200},
    
    # Özel rozetler
    "hard_conqueror": {"title": "💪 Zorluğu Yendi", "desc": "10 zorlu kelimeyi öğrendin", "xp": 100},
    "early_bird": {"title": "🌅 Sabah Kuşu", "desc": "Sabah 7'den önce çalıştın", "xp": 25},
    "night_owl": {"title": "🦉 Gece Baykuşu", "desc": "Gece yarısından sonra çalıştın", "xp": 25},
    "ai_user": {"title": "🤖 AI Destekli", "desc": "İlk AI örnek cümle aldın", "xp": 20},
}

def check_achievements() -> list:
    """Yeni kazanılan rozetleri döndür"""
    earned = set(st.session_state.get("earned_achievements", []))
    new_achievements = []
    
    p = st.session_state.progress
    easy_count = sum(1 for v in p.values() if v.get("status") == "easy")
    streak = st.session_state.get("daily_streak", 0)
    
    checks = [
        ("streak_3", streak >= 3),
        ("streak_7", streak >= 7),
        ("streak_30", streak >= 30),
        ("words_50", easy_count >= 50),
        ("words_100", easy_count >= 100),
        ("words_250", easy_count >= 250),
        ("words_500", easy_count >= 500),
    ]
    
    import datetime
    hour = datetime.datetime.now().hour
    if 5 <= hour < 7:
        checks.append(("early_bird", True))
    elif hour >= 23 or hour < 2:
        checks.append(("night_owl", True))
    
    for badge_id, condition in checks:
        if condition and badge_id not in earned:
            new_achievements.append(badge_id)
            earned.add(badge_id)
            xp_bonus = ACHIEVEMENTS[badge_id]["xp"]
            st.session_state.total_xp = st.session_state.get("total_xp", 0) + xp_bonus
    
    if new_achievements:
        st.session_state.earned_achievements = list(earned)
        persist_current_user()
    
    return new_achievements

def show_achievement_popup(badge_ids: list):
    """Yeni rozet kazanıldığında göster"""
    for bid in badge_ids:
        badge = ACHIEVEMENTS.get(bid, {})
        st.toast(
            f"{badge.get('title', '🏅')} — {badge.get('desc', '')} (+{badge.get('xp', 0)} XP)",
            icon="🎉"
        )

LEVELS = [
    (0, "🌱 Başlangıç", "#95a5a6"),
    (100, "📚 Öğrenci", "#3498db"),
    (300, "✏️ Çalışkan", "#2ecc71"),
    (600, "🎯 Odaklı", "#e67e22"),
    (1000, "⚡ Hızlı", "#e74c3c"),
    (1500, "🏅 Yetenekli", "#9b59b6"),
    (2500, "🎓 Bilgili", "#1abc9c"),
    (4000, "🌟 Uzman", "#f39c12"),
    (6000, "🏆 Usta", "#e74c3c"),
    (10000, "👑 Efsane", "#ffd700"),
]

def get_level_info(xp: int) -> dict:
    current_level = LEVELS[0]
    next_level = LEVELS[1] if len(LEVELS) > 1 else None
    
    for i, (req_xp, title, color) in enumerate(LEVELS):
        if xp >= req_xp:
            current_level = (req_xp, title, color)
            next_level = LEVELS[i + 1] if i + 1 < len(LEVELS) else None
    
    progress_to_next = 0
    if next_level:
        current_req, _, _ = current_level
        next_req, _, _ = next_level
        progress_to_next = (xp - current_req) / (next_req - current_req)
    
    return {
        "level_title": current_level[1],
        "level_color": current_level[2],
        "next_level": next_level[1] if next_level else "MAX",
        "progress": min(progress_to_next, 1.0),
        "xp_to_next": (next_level[0] - xp) if next_level else 0
    }

def render_xp_bar():
    """Sidebar'a eklenecek XP bar"""
    xp = st.session_state.get("total_xp", 0)
    info = get_level_info(xp)
    
    st.markdown(f"**{info['level_title']}** · {xp} XP")
    st.progress(info["progress"])
    if info["xp_to_next"] > 0:
        st.caption(f"Sonraki seviye: {info['xp_to_next']} XP")

def analyze_weak_patterns() -> dict:
    """
    Hangi kelime türlerinde, hangi harflerle başlayanlarda zayıf?
    """
    p = st.session_state.progress
    all_words = WORDS + st.session_state.custom_words
    
    analysis = {
        "by_type": {"Verb": {"hard": 0, "ok": 0, "easy": 0},
                    "Nomen": {"hard": 0, "ok": 0, "easy": 0},
                    "Adj/Adv": {"hard": 0, "ok": 0, "easy": 0}},
        "by_length": {"short": {"hard": 0, "total": 0},   # ≤5 harf
                      "medium": {"hard": 0, "total": 0},   # 6-9
                      "long": {"hard": 0, "total": 0}},    # ≥10
        "retry_rate": 0.0,  # Ortalama deneme sayısı
        "fastest_learned": [],
        "slowest_learned": [],
        "recommended_focus": ""
    }
    
    for w in all_words:
        word_text = w.get("word", "")
        prog = p.get(word_text, {})
        if not prog:
            continue
        
        status = prog.get("status", "ok")
        wtype = w.get("type", "")
        wlen = len(word_text)
        
        if wtype in analysis["by_type"]:
            analysis["by_type"][wtype][status] = \
                analysis["by_type"][wtype].get(status, 0) + 1
        
        bucket = "short" if wlen <= 5 else ("medium" if wlen <= 9 else "long")
        analysis["by_length"][bucket]["total"] += 1
        if status == "hard":
            analysis["by_length"][bucket]["hard"] += 1
    
    # En zayıf tür
    max_hard_ratio = 0
    for wtype, counts in analysis["by_type"].items():
        total = sum(counts.values())
        if total > 0:
            ratio = counts.get("hard", 0) / total
            if ratio > max_hard_ratio:
                max_hard_ratio = ratio
                analysis["recommended_focus"] = wtype
    
    return analysis

def render_weak_analysis():
    """İstatistikler sayfasına eklenecek analiz kartı"""
    analysis = analyze_weak_patterns()
    
    st.markdown("### 🔍 Zayıf Nokta Analizi")
    
    col1, col2, col3 = st.columns(3)
    
    for col, (wtype, counts) in zip(
        [col1, col2, col3], 
        analysis["by_type"].items()
    ):
        total = sum(counts.values())
        hard_pct = int(counts.get("hard", 0) / total * 100) if total else 0
        easy_pct = int(counts.get("easy", 0) / total * 100) if total else 0
        
        with col:
            color = "#e74c3c" if hard_pct > 30 else ("#f39c12" if hard_pct > 15 else "#27ae60")
            st.markdown(f"""
            <div style="background:{color}22; border-left:4px solid {color};
                        border-radius:8px; padding:12px;">
                <div style="font-weight:700">{wtype}</div>
                <div style="font-size:1.4rem; font-weight:700; color:{color}">
                    %{hard_pct} zor
                </div>
                <div style="font-size:0.8rem; color:#666">
                    %{easy_pct} öğrenildi
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    if analysis["recommended_focus"]:
        focus = analysis["recommended_focus"]
        st.info(f"💡 **Öneri:** {focus} kategorisinde zayıfsın. "
                f"Bu türden kelimeler için özel pratik yap!")
        
        if st.button(f"⚡ {focus} Kelimelerini Çalış", type="primary"):
            pool = [w for w in WORDS + st.session_state.custom_words 
                    if w.get("type") == focus]
            hard_first = sorted(
                pool,
                key=lambda w: st.session_state.progress.get(w["word"], {}).get("status", "") == "hard",
                reverse=True
            )
            st.session_state.flash_deck = hard_first[:25]
            st.session_state.flash_idx = 0
            st.session_state.flash_flipped = False
            st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
            st.session_state.page = "📇 Flashcard"
            st.rerun()
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
    
    st.markdown("---")
    st.markdown("### ⏰ Hatırlatıcı")

    # Son çalışma zamanını kontrol et
    last_study = st.session_state.get("last_study_date")
    if last_study:
        last_date = datetime.date.fromisoformat(last_study)
        days_since = (datetime.date.today() - last_date).days
        
        if days_since == 0:
            st.success("✅ Bugün çalıştın! Harika!")
        elif days_since == 1:
            st.warning("⚠️ Dün çalışmışsın. Seriyi bozma!")
        elif days_since > 1:
            st.error(f"📅 {days_since} gündür çalışmamışsın. Tekrar başlamak için harika bir gün!")
            
    if st.button("🔔 Günlük Hatırlatıcı Ayarla", use_container_width=True):
        st.info("Tarayıcı bildirimleri için izin ver.")

    pages = ["Ana Sayfa",'⚡ Hızlı Aksiyonlar', "📇 Flashcard", "📝 Quiz",'🎮 Kelime Oyunu','🏆 Haftalık Challange',  "📖 Kelime Listesi",
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
elif st.session_state.page == "⚡ Hızlı Aksiyonlar":
    # Ana sayfada, mevcut butonların altına ekle
    st.markdown("---")
    st.markdown("### ⚡ Hızlı Aksiyonlar")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔁 Bugünkü Tekrarlar", use_container_width=True):
            due_words = get_due_words()
            if due_words:
                random.shuffle(due_words)
                st.session_state.flash_deck = due_words[:20]
                st.session_state.flash_idx = 0
                st.session_state.flash_flipped = False
                st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
                st.session_state.page = "📇 Flashcard"
                st.rerun()
            else:
                st.toast("🎉 Bugün tekrar edilecek kelime yok!", icon="✅")

    with col2:
        if st.button("🎲 Rastgele 10 Kelime", use_container_width=True):
            all_words = WORDS + st.session_state.custom_words
            random.shuffle(all_words)
            st.session_state.flash_deck = all_words[:10]
            st.session_state.flash_idx = 0
            st.session_state.flash_flipped = False
            st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
            st.session_state.page = "📇 Flashcard"
            st.rerun()

    with col3:
        if st.button("💪 Sadece Zorlar", use_container_width=True):
            hard_words = [w for w in WORDS + st.session_state.custom_words 
                        if st.session_state.progress.get(w['word'], {}).get("status") == "hard"]
            if hard_words:
                st.session_state.flash_deck = hard_words[:15]
                st.session_state.flash_idx = 0
                st.session_state.flash_flipped = False
                st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
                st.session_state.page = "📇 Flashcard"
                st.rerun()
            else:
               st.toast("Hiç zor kelimen yok! Harika gidiyorsun! 🎉", icon="🏆")
# ── Sayfa: Haftalık Challenge ──────────────────────────────────────────────────
# ── Sayfa: Haftalık Challenge ──────────────────────────────────────────────────
elif st.session_state.page == "🏆 Haftalık Challange":
    st.markdown("# 🏆 Haftalık Challenge")
    st.markdown("Her hafta **30 yeni kelime** çalışarak büyük ödüller kazan!")
    
    # Challenge state'ini başlat
    week_num = datetime.date.today().isocalendar()[1]
    year = datetime.date.today().year
    challenge_key = f"week_{year}_{week_num}"
    
    # Bu hafta çalışılacak kelimeleri belirle
    all_words = WORDS + st.session_state.custom_words
    
    if challenge_key not in st.session_state:
        # Henüz görülmemiş kelimeleri bul
        unseen_words = [w for w in all_words if w["word"] not in st.session_state.progress]
        
        # Challenge için 30 kelime seç
        target_words = unseen_words[:30] if len(unseen_words) >= 30 else unseen_words
        
        st.session_state[challenge_key] = {
            "completed": 0,
            "target": len(target_words),
            "claimed": False,
            "start_date": str(datetime.date.today()),
            "target_words": [w["word"] for w in target_words],
            "target_words_data": target_words,  # Tüm veriyi sakla
            "completed_words": [],
            "flashcard_completed": False,
            "quiz_completed": False,
            "dialog_created": False,
            "dialog_content": None  # Oluşturulan diyalog burada saklanacak
        }
    
    challenge = st.session_state[challenge_key]
    
    # Bu hafta tamamlanan kelimeleri hesapla
    completed_count = 0
    for word in challenge["target_words"]:
        if word in st.session_state.progress:
            status = st.session_state.progress[word].get("status", "")
            if status == "easy":
                completed_count += 1
                if word not in challenge["completed_words"]:
                    challenge["completed_words"].append(word)
    
    challenge["completed"] = completed_count
    
    # Flashcard tamamlandı mı kontrol et
    if not challenge.get("flashcard_completed", False):
        all_words_seen = all(word in st.session_state.progress for word in challenge["target_words"])
        if all_words_seen:
            challenge["flashcard_completed"] = True
            st.balloons()
            st.success("🎉 Tüm haftalık kelimeleri flashcard'da gördün! Artık quiz yapabilirsin!")
    
    st.session_state[challenge_key] = challenge
    
    # Ana gösterim
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Haftalık Hedef", f"{challenge['target']} kelime")
    with col2:
        st.metric("✅ Öğrenilen", f"{challenge['completed']} kelime")
    with col3:
        remaining = challenge['target'] - challenge['completed']
        st.metric("📅 Kalan", f"{remaining} kelime")
    with col4:
        flashcard_status = "✅" if challenge.get("flashcard_completed", False) else "⏳"
        st.metric("📇 Flashcard", flashcard_status)
    
    # Progress bar
    if challenge['target'] > 0:
        st.progress(challenge['completed'] / challenge['target'])
    
    st.markdown("---")
    
    # Challenge durumu
    if challenge['completed'] >= challenge['target'] and challenge['target'] > 0:
        if not challenge.get("claimed", False):
            st.balloons()
            st.success(f"🎉 TEBRİKLER! {challenge['target']} kelimeyi öğrendin!")
            
            xp_reward = 300
            st.session_state.total_xp = st.session_state.get("total_xp", 0) + xp_reward
            
            if "weekly_champion" not in st.session_state.get("earned_achievements", []):
                achievements = st.session_state.get("earned_achievements", [])
                achievements.append("weekly_champion")
                st.session_state.earned_achievements = achievements
                st.markdown("🏅 **Yeni Rozet: Haftalık Şampiyon**")
            
            st.markdown(f"✨ **+{xp_reward} XP kazandın!**")
            
            if st.button("🎁 Ödülü Al", key="claim_reward", use_container_width=True, type="primary"):
                challenge["claimed"] = True
                st.session_state[challenge_key] = challenge
                persist_current_user()
                st.success("✅ Ödülünü aldın! Gelecek hafta yeni challenge seni bekliyor!")
                st.rerun()
        else:
            st.success("🏆 Bu haftaki challenge'ı tamamladın!")
    
    else:
        if challenge['target'] == 0:
            st.info("🎉 Tüm kelimeleri öğrendin! Yeni kelime eklemek için 'Kelime Ekle' sayfasını kullan.")
        else:
            st.info(f"📊 Bu hafta {challenge['completed']}/{challenge['target']} yeni kelime öğrendin.")
    
    st.markdown("---")
    
    # Hedef kelimeleri al
    target_words_list = [w for w in WORDS + st.session_state.custom_words 
                        if w["word"] in challenge["target_words"]]
    
    # === CHALLENGE AKSİYON BUTONLARI ===
    st.markdown("### 🎯 Challenge Aksiyonları")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📇 1. Flashcard Çalış", use_container_width=True, type="primary"):
            if target_words_list:
                unseen_in_challenge = [w for w in target_words_list 
                                      if w["word"] not in st.session_state.progress]
                seen_in_challenge = [w for w in target_words_list 
                                   if w["word"] in st.session_state.progress]
                deck = unseen_in_challenge + seen_in_challenge
                
                st.session_state.flash_deck = deck
                st.session_state.flash_idx = 0
                st.session_state.flash_flipped = False
                st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
                st.session_state.flash_challenge_mode = True
                st.session_state.current_challenge_key = challenge_key
                st.session_state.page = "📇 Flashcard"
                st.rerun()
            else:
                st.warning("Hedef kelime yok!")
    
    with col2:
        if challenge.get("flashcard_completed", False):
            if st.button("📝 2. Quiz Yap", use_container_width=True, type="secondary"):
                if target_words_list:
                    random.shuffle(target_words_list)
                    st.session_state.quiz_deck = target_words_list[:20]
                    st.session_state.quiz_idx = 0
                    st.session_state.quiz_session = {"correct": 0, "wrong": 0}
                    st.session_state.quiz_challenge_mode = True
                    make_quiz_question()
                    st.session_state.page = "📝 Quiz"
                    st.rerun()
                else:
                    st.warning("Hedef kelime yok!")
        else:
            st.button("📝 2. Quiz Yap", use_container_width=True, disabled=True, 
                     help="Önce tüm flashcard'ları tamamlamalısın!")
    
    with col3:
        if challenge.get("flashcard_completed", False):
            if not challenge.get("dialog_created", False):
                if st.button("💬 3. AI Diyalog Oluştur", use_container_width=True, type="secondary"):
                    with st.spinner("🤖 AI diyalog oluşturuyor..."):
                        # Diyalogu oluştur ve kaydet
                        dialog = deepseek.create_challenge_dialog(target_words_list, get_translation)
                        challenge["dialog_content"] = dialog
                        challenge["dialog_created"] = True
                        st.session_state[challenge_key] = challenge
                        st.success("✅ Diyalog oluşturuldu!")
                        st.rerun()
            else:
                if st.button("💬 3. AI Diyalog Göster", use_container_width=True, type="secondary"):
                    st.session_state.show_challenge_dialog = True
                    st.rerun()
        else:
            st.button("💬 3. AI Diyalog Oluştur", use_container_width=True, disabled=True,
                     help="Önce tüm flashcard'ları tamamlamalısın!")
    
    # AI Diyalog gösterimi (kaydedilmiş diyalogu kullan)
    if st.session_state.get("show_challenge_dialog", False) and challenge.get("dialog_content"):
        st.markdown("---")
        st.markdown("## 💬 Haftalık Kelimelerle AI Diyalog")
        
        # Diyalog içindeki kelimeleri vurgula
        dialog_html = challenge["dialog_content"]
        
        # Kelimeleri vurgula (opsiyonel)
        for word_obj in target_words_list[:10]:  # İlk 10 kelimeyi vurgula
            word = word_obj["word"]
            if word in dialog_html:
                dialog_html = dialog_html.replace(
                    word, 
                    f'<mark style="background:#ffd700; padding:2px 4px; border-radius:4px;">{word}</mark>'
                )
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 20px; padding: 2rem; margin: 1rem 0;">
            <div style="color: white; font-size: 1.1rem; line-height: 1.8;">
                {dialog_html.replace(chr(10), '<br>')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Diyalogda kullanılan kelimeleri göster
        st.markdown("**📝 Bu diyalogda kullanılan kelimeler:**")
        used_words = [w["word"] for w in target_words_list[:8]]
        st.markdown(", ".join([f"`{w}`" for w in used_words]))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 Kopyala", use_container_width=True):
                st.toast("✅ Diyalog kopyalandı!", icon="📋")
                st.session_state.dialog_to_copy = challenge["dialog_content"]
        
        with col2:
            if st.button("🔄 Diyalogu Yeniden Oluştur", use_container_width=True):
                if st.checkbox("Mevcut diyalog silinecek. Emin misin?"):
                    with st.spinner("Yeni diyalog oluşturuluyor..."):
                        new_dialog = deepseek.create_challenge_dialog(target_words_list, get_translation)
                        challenge["dialog_content"] = new_dialog
                        st.session_state[challenge_key] = challenge
                        st.rerun()
        
        with col3:
            if st.button("❌ Kapat", use_container_width=True):
                st.session_state.show_challenge_dialog = False
                st.rerun()
    
    st.markdown("---")
    
    # Bu haftanın kelime listesi
    st.markdown("### 📖 Bu Haftaki Hedef Kelimeler (30 Kelime)")
    
    if challenge["target_words"]:
        # Kelimeleri grid halinde göster
        learned_words = []
        unlearned_words = []
        
        for word_text in challenge["target_words"]:
            if word_text in challenge["completed_words"]:
                learned_words.append(word_text)
            else:
                unlearned_words.append(word_text)
        
        # Tüm kelimeleri göster (hepsi görünsün)
        st.markdown(f"**Toplam: {len(challenge['target_words'])} kelime** | ✅ Öğrenilen: {len(learned_words)} | 📝 Kalan: {len(unlearned_words)}")
        
        # 3 sütunlu grid
        cols = st.columns(3)
        for idx, word_text in enumerate(challenge["target_words"]):
            with cols[idx % 3]:
                word_obj = next((w for w in WORDS + st.session_state.custom_words if w["word"] == word_text), None)
                if word_obj:
                    if word_text in learned_words:
                        st.markdown(f"✅ {get_display(word_obj)}")
                    else:
                        st.markdown(f"📝 {get_display(word_obj)}")
        
        # Kalan kelimeleri çalış butonu
        if unlearned_words and not challenge.get("flashcard_completed", False):
            st.markdown("---")
            if st.button("⚡ Kalan Kelimeleri Çalış", use_container_width=True):
                remaining_words_list = [w for w in WORDS + st.session_state.custom_words 
                                       if w["word"] in unlearned_words]
                if remaining_words_list:
                    st.session_state.flash_deck = remaining_words_list
                    st.session_state.flash_idx = 0
                    st.session_state.flash_flipped = False
                    st.session_state.flash_challenge_mode = True
                    st.session_state.page = "📇 Flashcard"
                    st.rerun()
    
    else:
        st.info("Bu hafta için hedef kelime yok.")
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

                ai_col1, ai_col2 = st.columns([3, 1])
                with ai_col2:
                    if st.button("🤖 AI Örnek Cümle", use_container_width=True):
                        with st.spinner("AI cümle üretiyor..."):
                            try:
                                ai_text = generate_ai_example(word["word"], translation)
                                st.session_state.ai_sentence = ai_text
                                
                                # Kaydet
                                p = st.session_state.progress.get(word['word'], {})
                                p['ai_example'] = ai_text
                                st.session_state.progress[word['word']] = p
                                
                                # AI kullanım rozeti
                                if "ai_user" not in st.session_state.get("earned_achievements", []):
                                    achievements = st.session_state.get("earned_achievements", [])
                                    achievements.append("ai_user")
                                    st.session_state.earned_achievements = achievements
                                    st.session_state.total_xp = st.session_state.get("total_xp", 0) + 20
                                    st.toast("🎉 Yeni rozet kazandın: 🤖 AI Destekli! (+20 XP)", icon="🏆")
                                
                                persist_current_user()
                            except Exception as e:
                                st.session_state.ai_sentence = f"Hata: {e}"
                        st.rerun()

                ai_saved = st.session_state.ai_sentence or p_info.get('ai_example')
                if ai_saved:
                    st.markdown(f"""
                    <div class="ai-box">
                        {ai_saved.replace(chr(10), "<br>")}
                    </div>
                    """, unsafe_allow_html=True)

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

# Yeni bir sayfa ekleyin
# ── Sayfa: Kelime Oyunu (Match Game) ──────────────────────────────────────────
# ── Sayfa: Kelime Oyunu (Match Game) ──────────────────────────────────────────
elif st.session_state.page == "🎮 Kelime Oyunu":
    st.markdown("# 🎮 Eşleştirme Oyunu")
    st.markdown("Almanca kelimeleri doğru Türkçe anlamlarıyla eşleştir!")
    
    # Oyun state'ini başlat
    if "match_game" not in st.session_state:
        st.session_state.match_game = {
            "active": False,
            "words": [],
            "selected_german": None,
            "score": 0,
            "attempts": 0,
            "game_completed": False
        }
    
    # Oyunu başlatma fonksiyonu
    def start_new_game():
        all_words = WORDS + st.session_state.custom_words
        available_words = [w for w in all_words if get_translation(w["word"]) not in ("Çeviri yok", "—", None, "")]
        
        if len(available_words) < 4:
            st.session_state.match_game["active"] = False
            st.session_state.match_game["game_completed"] = False
            return False
        
        selected = random.sample(available_words, min(6, len(available_words)))
        
        game_words = []
        for w in selected:
            game_words.append({
                "german": w["word"],
                "article": w.get("article", ""),
                "turkish": get_translation(w["word"]),
                "matched": False,
                "id": random.randint(1000, 9999)  # Unique ID
            })
        
        random.shuffle(game_words)
        
        st.session_state.match_game = {
            "active": True,
            "words": game_words,
            "selected_german": None,
            "score": 0,
            "attempts": 0,
            "game_completed": False
        }
        return True
    
    # Ana buton - her zaman aynı key ile
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎮 Yeni Oyun Başlat", key="new_game_main", use_container_width=True, type="primary"):
            start_new_game()
            st.rerun()
    
    # Oyun aktif mi kontrol et
    if not st.session_state.match_game.get("active", False):
        st.info("🎯 Yeni oyun başlatmak için 'Yeni Oyun Başlat' butonuna tıklayın!")
        
        st.markdown("---")
        st.markdown("### 📖 Nasıl Oynanır?")
        st.markdown("""
        1. **Yeni Oyun Başlat** butonuna tıkla
        2. Soldaki **Almanca** kelimeye tıkla
        3. Sağdaki **Türkçe** anlama tıkla
        4. Doğru eşleştiyse puan kazanırsın!
        5. Tüm kelimeleri eşleştirmeye çalış!
        """)
    
    else:
        game = st.session_state.match_game
        words = game["words"]
        
        # Oyun tamamlandı mı kontrol et
        matched_count = sum(1 for w in words if w["matched"])
        total = len(words)
        
        if matched_count == total and total > 0 and not game.get("game_completed", False):
            game["game_completed"] = True
            game["active"] = False
            
            # XP kazandır
            xp_earned = game["score"] * 2
            st.session_state.total_xp = st.session_state.get("total_xp", 0) + xp_earned
            
            # Başarı mesajı göster
            st.balloons()
            st.success(f"🎉 TEBRİKLER! Oyunu {game['attempts']} denemede tamamladın!")
            st.markdown(f"🏆 **Skorun: {game['score']}**")
            st.markdown(f"✨ **+{xp_earned} XP kazandın!**")
            
            # Tekrar oyna butonu
            if st.button("🔄 Tekrar Oyna", key="play_again", use_container_width=True, type="primary"):
                start_new_game()
                st.rerun()
            
            # Oyun state'ini gösterme, sadece bitiş ekranını göster
            st.stop()
        
        # Skor gösterimi
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🎯 Skor", game["score"])
        with col2:
            st.metric("✅ Eşleşen", f"{matched_count}/{total}")
        with col3:
            st.metric("🔄 Deneme", game["attempts"])
        
        if total > 0:
            st.progress(matched_count / total)
        st.markdown("---")
        
        # Oyun alanı - 2 sütun
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("### 🇩🇪 Almanca")
            st.markdown("*Bir kelime seçin*")
            
            # Eşlenmemiş Almanca kelimeleri göster
            unmatched_german = [w for w in words if not w["matched"]]
            
            if not unmatched_german:
                st.success("🎉 Tüm kelimeler eşleşti! Yukarıdaki butona tıkla!")
            else:
                for word_data in unmatched_german:
                    german_word = word_data["german"]
                    article = word_data.get("article", "")
                    display = f"{article} {german_word}".strip() if article else german_word
                    
                    # Seçili mi?
                    is_selected = (game["selected_german"] == german_word)
                    button_type = "primary" if is_selected else "secondary"
                    
                    # Benzersiz key
                    btn_key = f"ger_{german_word}_{word_data['id']}"
                    
                    if st.button(f"{display}", key=btn_key, use_container_width=True, type=button_type):
                        if is_selected:
                            game["selected_german"] = None
                        else:
                            game["selected_german"] = german_word
                        st.rerun()
        
        with col_right:
            st.markdown("### 🇹🇷 Türkçe")
            st.markdown("*Anlamını seçin*")
            
            # Eşlenmemiş Türkçe anlamları göster (benzersiz)
            unmatched_turkish = list(set([w["turkish"] for w in words if not w["matched"]]))
            
            if not unmatched_turkish:
                st.success("🎉 Tüm anlamlar eşleşti!")
            else:
                for i, turkish in enumerate(unmatched_turkish):
                    btn_key = f"tr_{turkish}_{i}_{len(unmatched_turkish)}"
                    
                    if st.button(f"{turkish}", key=btn_key, use_container_width=True):
                        if game["selected_german"] is None:
                            st.warning("⚠️ Önce bir Almanca kelime seçin!")
                        else:
                            # Eşleştirme kontrolü
                            game["attempts"] += 1
                            
                            # Seçili Almanca kelimeyi bul
                            selected_word = next((w for w in words if w["german"] == game["selected_german"]), None)
                            
                            if selected_word and selected_word["turkish"] == turkish:
                                # DOĞRU EŞLEŞME
                                selected_word["matched"] = True
                                game["score"] += 10
                                game["selected_german"] = None
                                st.success(f"✅ Doğru! {selected_word['german']} = {turkish}")
                                st.balloons()
                            else:
                                # YANLIŞ EŞLEŞME
                                st.error(f"❌ Yanlış! '{game['selected_german']}' ≠ '{turkish}'")
                                game["selected_german"] = None
                                
                                # Doğru cevabı göster
                                if selected_word:
                                    st.info(f"💡 İpucu: {selected_word['german']} → {selected_word['turkish']}")
                            
                            st.rerun()
        
        # Seçili kelimeyi göster
        if game["selected_german"]:
            st.markdown("---")
            st.info(f"📌 **Seçili kelime:** {game['selected_german']}")
        
        # Oyunu sıfırlama butonu (ayrı key)
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🗑️ Oyunu Sıfırla", key="reset_game", use_container_width=True):
                st.session_state.match_game = {
                    "active": False,
                    "words": [],
                    "selected_german": None,
                    "score": 0,
                    "attempts": 0,
                    "game_completed": False
                }
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
    st.markdown("### 🤖 AI Destekli Analiz")

    # Zorlu kelimeleri al
    hard_words_list = [word for word, info in p.items() if info.get("status") == "hard"]

    if st.button("🔍 AI ile Zayıf Noktalarımı Analiz Et", use_container_width=True):
        with st.spinner("AI analiz yapıyor..."):
            user_stats = {
                "total_xp": st.session_state.get("total_xp", 0),
                "streak": st.session_state.get("daily_streak", 0),
                "total_words": len(p)
            }
            analysis = deepseek.analyze_weak_words(hard_words_list, user_stats)
            st.info(f"💡 {analysis}")
        
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

    # İstatistikler sayfasında, mevcut kodun altına ekle
    st.markdown("---")
    st.markdown("### 📈 Öğrenme Hızın")

    # Haftalık aktivite grafiği
    last_7_days = []
    for i in range(6, -1, -1):
        day = datetime.date.today() - datetime.timedelta(days=i)
        day_str = str(day)
        studied = sum(1 for v in p.values() if v.get("last_seen") == day_str)
        last_7_days.append(studied)

    st.bar_chart({"Çalışılan Kelime": last_7_days})
    st.caption("Son 7 gündeki günlük çalışma aktiviten")

    # Tahmini tamamlanma süresi
    if seen > 0 and easy > 0:
        words_per_day = easy / max(1, (datetime.date.today() - st.session_state.get("start_date", datetime.date.today())).days)
        remaining = total - easy
        days_left = int(remaining / max(words_per_day, 1))
        st.info(f"🎯 Mevcut hızınla **{days_left} gün** içinde tüm kelimeleri öğrenebilirsin!")