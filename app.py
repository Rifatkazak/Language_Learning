import streamlit as st
import json
import random
import time
import datetime
import os
from pathlib import Path
from anthropic import Anthropic

# ── Sayfa Ayarları ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Goethe B1 Kelime Öğrenimi",
    page_icon="🇩🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

# Türkçe çeviriler (temel liste)
TRANSLATIONS = {
    "abbiegen":"dönmek","Abbildung":"resim, şekil","Abenteuer":"macera","aber":"ama, fakat",
    "abfahren":"hareket etmek, kalkmak","Abfahrt":"kalkış","Abfall":"çöp, atık",
    "Abfalleimer":"çöp kovası","abgeben":"teslim etmek","abhängen":"bağlı olmak",
    "abheben":"para çekmek","abholen":"almak, karşılamak","abhängig":"bağımlı",
    "ablehnen":"reddetmek","abmachen":"anlaşmak","abnehmen":"kilo vermek, azalmak",
    "abonnieren":"abone olmak","Abonnement":"abonelik","absagen":"iptal etmek",
    "Abschluss":"bitiş, diploma","Abschnitt":"bölüm, paragraf","Absender":"gönderici",
    "Absicht":"niyet, kasıt","absolut":"kesinlikle, mutlak","abstimmen":"oy kullanmak",
    "Abteilung":"departman, bölüm","abwärts":"aşağı doğru","abwesend":"yok, burada değil",
    "achten":"dikkat etmek, saygı göstermek","Adresse":"adres","ähnlich":"benzer",
    "Ahnung":"fikir, sezgi","Aktion":"eylem, kampanya","aktiv":"aktif, etkin",
    "Aktivität":"aktivite","Alphabet":"alfabe","als":"olarak, -den daha",
    "also":"yani, demek ki","aktuell":"güncel","akzeptieren":"kabul etmek",
    "alt":"yaşlı, eski","Alarm":"alarm","Alltag":"günlük hayat","allgemein":"genel",
    "allein":"yalnız, tek başına","allerdings":"ancak, gerçi","alles":"her şey",
    "Alter":"yaş","Ampel":"trafik lambası","Amt":"daire, makam","amtlich":"resmi",
    "anbieten":"teklif etmek","Angebot":"teklif, fırsat","angemessen":"uygun, makul",
    "Angst":"korku, endişe","ankommen":"varmak, gelmek","anmelden":"kaydettirmek",
    "Anmeldung":"kayıt, başvuru","annehmen":"kabul etmek","anrufen":"aramak (telefon)",
    "Anruf":"telefon araması","anschauen":"bakmak, izlemek","ansehen":"seyretmek",
    "Ansicht":"görüş, manzara","antworten":"cevap vermek","Antwort":"cevap, yanıt",
    "anwenden":"uygulamak","Anwendung":"uygulama","Anzahl":"sayı, miktar",
    "anzünden":"tutuşturmak","Apotheke":"eczane","Apparat":"cihaz, hat",
    "arbeiten":"çalışmak","Arbeit":"iş, çalışma","Arbeiter":"işçi",
    "Arbeitsamt":"iş ve işçi bulma kurumu","arm":"fakir, yoksul","Arm":"kol",
    "Arzt":"doktor (erkek)","Ärztin":"doktor (kadın)","aufhören":"bırakmak, durdurmak",
    "aufmachen":"açmak","aufnehmen":"kaydetmek","aufpassen":"dikkat etmek",
    "aufräumen":"toplamak, düzenlemek","aufschreiben":"not almak","aufstehen":"kalkmak",
    "aufwachen":"uyanmak","Ausbildung":"mesleki eğitim","ausgeben":"harcamak",
    "ausgehen":"dışarı çıkmak","Ausland":"yurt dışı","ausländisch":"yabancı",
    "ausmachen":"kapatmak, anlaşmak","Ausnahme":"istisna","ausruhen":"dinlenmek",
    "ausschalten":"kapatmak (cihaz)","aussuchen":"seçmek","Ausweg":"çıkış yolu",
    "ausziehen":"taşınmak (ev), çıkarmak","Auto":"araba","Autobahn":"otoyol",
    "backen":"fırında pişirmek","Bäckerei":"fırın","Bad":"banyo",
    "Bahnhof":"tren istasyonu","bald":"yakında","Balkon":"balkon","Bank":"banka",
    "bauen":"inşa etmek","Bauer":"çiftçi","Baum":"ağaç",
    "bedeuten":"anlamına gelmek","Bedeutung":"anlam, önem","bedienen":"hizmet etmek",
    "Bedingung":"şart, koşul","befragen":"sorgulamak","beginnen":"başlamak",
    "Beginn":"başlangıç","begleiten":"eşlik etmek","behalten":"akılda tutmak",
    "behandeln":"tedavi etmek","Behandlung":"tedavi","beherrschen":"hakim olmak",
    "beitragen":"katkıda bulunmak","bekannt":"tanınmış, bilinen",
    "bekommen":"almak, elde etmek","bemerken":"fark etmek","benutzen":"kullanmak",
    "Benutzer":"kullanıcı","beraten":"tavsiye vermek","Beratung":"danışmanlık",
    "Bereich":"alan, bölge","bereit":"hazır","Beruf":"meslek","berühmt":"ünlü",
    "beschreiben":"tanımlamak","Beschreibung":"tanımlama","besitzen":"sahip olmak",
    "besonders":"özellikle","besprechen":"görüşmek","bestehen":"geçmek (sınav)",
    "bestellen":"sipariş vermek","Bestellung":"sipariş","besuchen":"ziyaret etmek",
    "Besucher":"ziyaretçi","betonen":"vurgulamak","Betrieb":"işletme",
    "bewegen":"hareket ettirmek","Bewegung":"hareket","beweisen":"kanıtlamak",
    "bezahlen":"ödemek","Bibliothek":"kütüphane","bieten":"sunmak",
    "Bild":"resim, fotoğraf","bilden":"oluşturmak, eğitmek","Bildung":"eğitim",
    "billig":"ucuz","bitten":"rica etmek","bleiben":"kalmak","Blick":"bakış",
    "blicken":"bakmak","Blume":"çiçek","Boden":"zemin, toprak",
    "brauchen":"ihtiyaç duymak","brechen":"kırmak","Brief":"mektup",
    "bringen":"getirmek","Brot":"ekmek","Brücke":"köprü","Buch":"kitap",
    "buchen":"rezervasyon yapmak","Buchung":"rezervasyon","Bundesland":"eyalet",
    "Bürger":"vatandaş","Büro":"ofis","Bus":"otobüs","Chance":"şans, fırsat",
    "Charakter":"karakter","Chef":"patron (erkek)","Chefin":"patron (kadın)",
    "Datum":"tarih","dauern":"sürmek","Dauer":"süre","denken":"düşünmek",
    "Direktor":"müdür","Diskussion":"tartışma","diskutieren":"tartışmak",
    "doch":"yine de, ama","Dokument":"belge","Dorf":"köy","drücken":"basmak",
    "dürfen":"izni olmak","eben":"tam, düz, biraz önce","ehrenamtlich":"gönüllü",
    "eigentlich":"aslında","einladen":"davet etmek","Einladung":"davet",
    "einschalten":"açmak (cihaz)","einstellen":"ayarlamak","einteilen":"bölmek",
    "einziehen":"taşınmak","Empfang":"resepsiyon","empfangen":"karşılamak",
    "empfehlen":"tavsiye etmek","Empfehlung":"tavsiye","Ende":"son, bitiş",
    "enden":"bitmek","endlich":"sonunda","entscheiden":"karar vermek",
    "Entscheidung":"karar","entschuldigen":"özür dilemek","Entschuldigung":"özür",
    "entspannen":"rahatlamak","Entspannung":"rahatlama","entwickeln":"geliştirmek",
    "Entwicklung":"gelişme","Erfahrung":"deneyim","erfahren":"öğrenmek",
    "Erfolg":"başarı","erfolgreich":"başarılı","erinnern":"hatırlamak",
    "Erinnerung":"anı, hatıra","erklären":"açıklamak","Erklärung":"açıklama",
    "erlauben":"izin vermek","Erlaubnis":"izin","ernst":"ciddi",
    "erreichen":"ulaşmak","erscheinen":"görünmek, yayımlanmak",
    "erwarten":"beklemek","Erwartung":"beklenti","erzählen":"anlatmak",
    "Essen":"yemek (isim)","essen":"yemek yemek","etwas":"bir şey, biraz",
    "fahren":"sürmek, gitmek","Fahrt":"yolculuk","fallen":"düşmek",
    "falsch":"yanlış","Familie":"aile","fangen":"yakalamak","Farbe":"renk",
    "fast":"neredeyse","fehlen":"eksik olmak","Fehler":"hata","Fenster":"pencere",
    "Ferien":"tatil (okul)","fertig":"hazır, bitmiş","Fest":"bayram, festival",
    "Film":"film","finden":"bulmak","Firma":"şirket","folgen":"takip etmek",
    "Frage":"soru","fragen":"sormak","Freiheit":"özgürlük","fremd":"yabancı",
    "freuen":"sevinmek","Freude":"sevinç","Freund":"erkek arkadaş",
    "Freundin":"kız arkadaş","früher":"daha önce, eskiden",
    "führen":"yönetmek, götürmek","Führerschein":"sürücü belgesi",
    "fühlen":"hissetmek","Gefühl":"duygu, his","geben":"vermek",
    "Gebäude":"bina","Geburtstag":"doğum günü","gefallen":"hoşuna gitmek",
    "gegen":"karşı","gehen":"gitmek, yürümek","gehören":"ait olmak",
    "Geld":"para","Gelegenheit":"fırsat","genug":"yeterli","Gepäck":"bagaj",
    "gerade":"tam, doğruca, şu an","Gerät":"cihaz, alet",
    "Geschäft":"dükkan, iş","Geschenk":"hediye","Geschichte":"tarih, hikaye",
    "Gesetz":"yasa, kanun","Gesicht":"yüz","Gespräch":"sohbet, konuşma",
    "gesund":"sağlıklı","Gesundheit":"sağlık","Gewicht":"ağırlık",
    "gewinnen":"kazanmak","glauben":"inanmak","Glück":"şans, mutluluk",
    "glücklich":"mutlu","groß":"büyük","Gruppe":"grup","gut":"iyi",
    "haben":"sahip olmak","Hafen":"liman","halten":"tutmak, durmak",
    "Handy":"cep telefonu","Hauptbahnhof":"ana tren istasyonu",
    "Hauptstadt":"başkent","Haus":"ev","Haushalt":"hane, ev işleri",
    "heiraten":"evlenmek","helfen":"yardım etmek","Hilfe":"yardım",
    "hoch":"yüksek","hoffen":"ummak","Hoffnung":"umut",
    "hören":"duymak, dinlemek","Hunger":"açlık","Idee":"fikir",
    "immer":"her zaman","Information":"bilgi","informieren":"bilgilendirmek",
    "Inhalt":"içerik","interessant":"ilginç","Interesse":"ilgi",
    "interessieren":"ilgilendirmek","Jahr":"yıl","jedoch":"ancak",
    "jemand":"birisi","Job":"iş","kaufen":"satın almak",
    "Kaufhaus":"büyük mağaza","kennen":"tanımak","Kind":"çocuk",
    "Klasse":"sınıf","klar":"açık, net","klein":"küçük",
    "klingen":"çınlamak, kulağa gelmek","kochen":"pişirmek","kommen":"gelmek",
    "können":"yapabilmek","Kontakt":"iletişim","kontrollieren":"kontrol etmek",
    "Konzert":"konser","Kosten":"masraf","kosten":"mal olmak",
    "Krankenhaus":"hastane","krank":"hasta","Kreuzung":"kavşak",
    "Küche":"mutfak","Kurs":"kurs","kurz":"kısa","lachen":"gülmek",
    "Laden":"dükkan","lang":"uzun","langsam":"yavaş","lassen":"bırakmak",
    "laufen":"koşmak, yürümek","laut":"yüksek sesli","leben":"yaşamak",
    "Leben":"yaşam, hayat","legen":"koymak","lehren":"öğretmek",
    "Lehrer":"öğretmen (erkek)","Lehrerin":"öğretmen (kadın)","lernen":"öğrenmek",
    "lesen":"okumak","Leute":"insanlar","lieben":"sevmek","Liebe":"aşk, sevgi",
    "liefern":"teslim etmek","links":"sol","lösen":"çözmek","Lösung":"çözüm",
    "machen":"yapmak","Meinung":"görüş, fikir","meinen":"düşünmek, kastetmek",
    "meistens":"çoğunlukla","Mensch":"insan","merken":"fark etmek",
    "Messe":"fuar","mieten":"kiralamak","Miete":"kira","Mitte":"orta",
    "möglich":"mümkün","Möglichkeit":"olasılık, imkan","Monat":"ay",
    "müde":"yorgun","müssen":"zorunda olmak","Nachbar":"komşu",
    "Nachricht":"haber, mesaj","natürlich":"tabii ki, doğal",
    "nehmen":"almak","neu":"yeni","nichts":"hiçbir şey","normal":"normal",
    "Notiz":"not","nötig":"gerekli","nutzen":"kullanmak, yararlanmak",
    "oben":"yukarıda","öffnen":"açmak","öffentlich":"kamusal",
    "Ort":"yer, şehir","passen":"uymak","Pause":"mola","Person":"kişi",
    "planen":"planlamak","Plan":"plan","Platz":"yer, meydan",
    "Politik":"politika","politisch":"siyasi","Post":"posta",
    "Problem":"sorun","Produkt":"ürün","Programm":"program",
    "Projekt":"proje","prüfen":"sınamak","Prüfung":"sınav",
    "pünktlich":"dakik, zamanında","putzen":"temizlemek","Qualität":"kalite",
    "Rat":"tavsiye","raten":"tavsiye etmek","Raum":"oda, alan",
    "reagieren":"tepki vermek","Reaktion":"tepki","rechts":"sağ",
    "reden":"konuşmak","Regel":"kural","regeln":"düzenlemek",
    "Region":"bölge","reisen":"seyahat etmek","Reise":"seyahat",
    "rennen":"koşmak","retten":"kurtarmak","richtig":"doğru",
    "Richtung":"yön","Rolle":"rol","rufen":"çağırmak",
    "ruhig":"sakin","Ruhe":"sessizlik, huzur","sagen":"söylemek",
    "sammeln":"toplamak","Schule":"okul","Schüler":"öğrenci (erkek)",
    "Schülerin":"öğrenci (kadın)","schreiben":"yazmak",
    "schließen":"kapatmak","schlecht":"kötü","schnell":"hızlı",
    "schön":"güzel","schon":"zaten, artık","schwer":"ağır, zor",
    "sehen":"görmek","sein":"olmak","Seite":"sayfa, taraf",
    "selbst":"kendisi, bizzat","sicher":"güvenli, kesin",
    "Sicherheit":"güvenlik","sitzen":"oturmak","sollen":"yapması gerekiyor",
    "Spaß":"eğlence","spät":"geç","spielen":"oynamak",
    "Sprache":"dil","sprechen":"konuşmak","Staat":"devlet",
    "Stadt":"şehir","stehen":"durmak, ayakta olmak",
    "stellen":"koymak, sormak","Stelle":"yer, pozisyon",
    "stimmen":"doğru olmak, oy vermek","Straße":"sokak, cadde",
    "studieren":"üniversitede okumak","Studium":"üniversite eğitimi",
    "suchen":"aramak","System":"sistem","täglich":"günlük",
    "Teil":"parça, bölüm","teilnehmen":"katılmak","Telefon":"telefon",
    "telefonieren":"telefon etmek","Termin":"randevu","Test":"test",
    "testen":"test etmek","Tisch":"masa","Tochter":"kız çocuğu",
    "tragen":"taşımak, giymek","treffen":"buluşmak","Treffen":"buluşma",
    "trinken":"içmek","tun":"yapmak","Tür":"kapı",
    "Überzeugung":"inanç, kanaat","übrig":"kalan, geri kalan",
    "umsteigen":"aktarma yapmak","ungefähr":"yaklaşık",
    "Universität":"üniversite","Unterricht":"ders","Urlaub":"tatil, izin",
    "verantwortlich":"sorumlu","verbessern":"geliştirmek",
    "Verbesserung":"gelişme, iyileşme","verbinden":"bağlamak",
    "Verbindung":"bağlantı","vereinbaren":"anlaşmak",
    "Vereinbarung":"anlaşma","vergessen":"unutmak",
    "vergleichen":"karşılaştırmak","Vergleich":"karşılaştırma",
    "verkaufen":"satmak","Verkäufer":"satıcı","Verkehr":"trafik",
    "verlassen":"terk etmek","verlieren":"kaybetmek",
    "versprechen":"söz vermek","Versprechen":"söz, vaat",
    "verstehen":"anlamak","Verständnis":"anlayış",
    "versuchen":"denemek","Versuch":"deneme","viel":"çok",
    "vielleicht":"belki","Vorbild":"örnek, idol",
    "vorbereiten":"hazırlamak","Vorbereitung":"hazırlık",
    "vorstellen":"tanıtmak, hayal etmek","Vorstellung":"tanıtım",
    "wählen":"seçmek","Wahl":"seçim","warten":"beklemek",
    "warum":"neden","Wasser":"su","Weg":"yol","wegen":"yüzünden",
    "weiter":"devam etmek, ileri","Welt":"dünya","wenig":"az",
    "werden":"olmak","wichtig":"önemli","Wichtigkeit":"önem",
    "Wissen":"bilgi (isim)","wissen":"bilmek","Wohnung":"daire, ev",
    "wohnen":"yaşamak, oturmak","Wort":"kelime","wünschen":"dilemek",
    "Wunsch":"dilek, istek","zahlen":"ödemek","Zeichen":"işaret",
    "zeigen":"göstermek","Zeit":"zaman","Zeitung":"gazete",
    "Ziel":"hedef, amaç","Zimmer":"oda","zuhören":"dinlemek",
    "Zukunft":"gelecek","zumachen":"kapatmak","zurückgeben":"geri vermek",
    "zusammen":"birlikte","Zusammenarbeit":"işbirliği","zwingen":"zorlamak",
}

def get_translation(word):
    return TRANSLATIONS.get(word, "—")

def get_display(w):
    return f"{w['article']} {w['word']}" if w.get('article') else w['word']

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
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Yardımcı Fonksiyonlar ────────────────────────────────────────────────────
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
        if ft != "Tümü" and w["type"] != ft:
            continue
        if sq and sq not in w["word"].lower() and sq not in get_translation(w["word"]).lower():
            continue
        result.append(w)
    return result

def start_flash():
    due = get_due_words()
    ft = st.session_state.filter_type
    if ft != "Tümü":
        due = [w for w in due if w["type"] == ft]
    if not due:
        due = filtered_words()
    random.shuffle(due)
    st.session_state.flash_deck = due[:30]
    st.session_state.flash_idx = 0
    st.session_state.flash_flipped = False
    st.session_state.flash_session = {"correct": 0, "wrong": 0, "skipped": 0}
    st.session_state.ai_sentence = ""

def start_quiz():
    pool = filtered_words()
    random.shuffle(pool)
    st.session_state.quiz_deck = pool[:20]
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
    wrongs = random.sample([w for w in all_w if w["word"] != word["word"]], 3)
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

    pages = ["Ana Sayfa", "📇 Flashcard", "📝 Quiz", "📖 Kelime Listesi",
             "➕ Kelime Ekle", "📊 İstatistikler"]
    for pg in pages:
        if st.button(pg, use_container_width=True,
                     type="primary" if st.session_state.page == pg else "secondary"):
            st.session_state.page = pg
            st.rerun()

    st.markdown("---")
    # Filtre
    st.markdown("**Filtre**")
    ft = st.selectbox("Kelime türü", ["Tümü", "Verb", "Nomen", "Adj/Adv"],
                      label_visibility="collapsed",
                      index=["Tümü","Verb","Nomen","Adj/Adv"].index(st.session_state.filter_type))
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
    day_idx = datetime.date.today().toordinal() % total
    all_w = WORDS + st.session_state.custom_words
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

    if not st.session_state.flash_deck:
        st.info("Başlamak için aşağıdaki butona tıklayın.")
        if st.button("Flashcard Başlat 🚀", type="primary"):
            start_flash()
            st.rerun()
    else:
        idx   = st.session_state.flash_idx
        deck  = st.session_state.flash_deck
        sess  = st.session_state.flash_session

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
            art_class = f"article-{article}" if article else ""
            wtype = word["type"].replace("/", "")

            if not flipped:
                # Ön yüz
                art_html = f'<div class="{art_class}">{article}</div>' if article else ""
                st.markdown(f"""
                <div class="flashcard flashcard-front">
                    {art_html}
                    <div class="word-big">{word['word']}</div>
                    <span class="type-badge type-{wtype}">{word['type']}</span>
                    <div style="margin-top:1.5rem; opacity:0.5; font-size:0.85rem">👆 Çeviriyi görmek için çevir</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🔄 Çevir", use_container_width=True, type="primary"):
                    st.session_state.flash_flipped = True
                    st.rerun()
            else:
                # Arka yüz
                p_info = st.session_state.progress.get(word["word"], {})
                count = p_info.get("count", 0)
                st.markdown(f"""
                <div class="flashcard flashcard-back">
                    <div style="opacity:0.7; font-size:1rem; margin-bottom:0.3rem">{display}</div>
                    <div class="word-tr">{translation}</div>
                    {f'<div style="font-size:0.85rem; opacity:0.6; margin-top:0.5rem">Daha önce {count}× görüldü</div>' if count else ""}
                </div>
                """, unsafe_allow_html=True)

                # AI Örnek Cümle
                ai_col1, ai_col2 = st.columns([3, 1])
                with ai_col2:
                    if st.button("🤖 AI Örnek Cümle", use_container_width=True):
                        with st.spinner("AI cümle üretiyor..."):
                            try:
                                client = Anthropic()
                                msg = client.messages.create(
                                    model="claude-sonnet-4-5",
                                    max_tokens=300,
                                    messages=[{"role":"user","content":
                                        f'"{display}" Almanca kelimesi için 2 kısa örnek cümle yaz ve her birinin Türkçe çevirisini ver.\nFormat:\n1. [Almanca cümle]\n   → [Türkçe çeviri]\n2. [Almanca cümle]\n   → [Türkçe çeviri]'}]
                                )
                                st.session_state.ai_sentence = msg.content[0].text
                            except Exception as e:
                                st.session_state.ai_sentence = f"Hata: {e}"
                        st.rerun()

                if st.session_state.ai_sentence:
                    st.markdown(f'<div class="ai-box">{st.session_state.ai_sentence.replace(chr(10),"<br>")}</div>',
                                unsafe_allow_html=True)

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
        if st.button("Quiz Başlat 🎯", type="primary"):
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
    total_pages = (len(fw) - 1) // PAGE_SIZE + 1
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
                entry = {"word": new_word.strip(), "article": new_article,
                         "type": new_type, "custom": True}
                TRANSLATIONS[new_word.strip()] = new_tr.strip()
                st.session_state.custom_words.append(entry)
                st.success(f"✅ '{new_article} {new_word}' başarıyla eklendi!")
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
                entry = {"word": w_word, "article": w_art, "type": w_type, "custom": True}
                TRANSLATIONS[w_word] = w_tr
                st.session_state.custom_words.append(entry)
                added += 1
            else:
                errors.append(line)
        st.success(f"✅ {added} kelime eklendi!")
        if errors:
            st.warning(f"Atlandı: {errors[:5]}")
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
                st.rerun()