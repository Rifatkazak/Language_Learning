import random
import streamlit as st

from services.ai_service import get_ai_service
from services.gamification import add_xp
from storage.user_store import persist_current_user
from core.i18n import t

# fmt: off
IMAGES = [
    {
        "id": "family_breakfast",
        "url": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&auto=format&fit=crop&q=80",
        "context_tr": "Mutlu bir aile mutfakta birlikte kahvaltı yapıyor. Masada çeşitli yiyecekler var.",
        "context_en": "A happy family having breakfast together in a bright kitchen. Various foods are on the table.",
        "vocab_tr": "die Küche, der Tisch, das Frühstück, die Familie, gemeinsam, frühstücken, sitzen, essen",
        "vocab_en": "kitchen, table, breakfast, family, together, to have breakfast, to sit, to eat",
        "hint_structure": "Auf dem Bild sieht man ... Im Vordergrund ... Im Hintergrund sieht man ... Die Personen ... Es scheint, dass ... Insgesamt wirkt das Bild ...",
        "hint_example": "Auf dem Bild sieht man eine Familie, die gemeinsam in der hellen Küche frühstückt.",
    },
    {
        "id": "vegetable_market",
        "url": "https://images.unsplash.com/photo-1488459716781-31db52582fe9?w=800&auto=format&fit=crop&q=80",
        "context_tr": "Bir açık hava sebze ve meyve pazarı. Renkli ürünler tezgahlarda sergileniyor.",
        "context_en": "An outdoor vegetable and fruit market. Colorful produce is displayed on stalls.",
        "vocab_tr": "der Markt, das Gemüse, das Obst, der Verkäufer, die Kundin, kaufen, frisch, bunt",
        "vocab_en": "market, vegetable, fruit, seller, customer, to buy, fresh, colorful",
        "hint_structure": "Das Bild zeigt ... Man sieht viele ... Im Vordergrund steht/liegt ... Eine Person ... Die Atmosphäre wirkt ...",
        "hint_example": "Das Bild zeigt einen belebten Wochenmarkt mit frischem Gemüse und Obst.",
    },
    {
        "id": "cafe_interior",
        "url": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=800&auto=format&fit=crop&q=80",
        "context_tr": "Şık bir kafenin içi. Masalarda insanlar oturuyor, kahve içiyor ve sohbet ediyor.",
        "context_en": "The interior of a cozy café. People sit at tables, drinking coffee and chatting.",
        "vocab_tr": "das Café, der Kaffee, die Tasse, sitzen, trinken, sich unterhalten, gemütlich, die Atmosphäre",
        "vocab_en": "café, coffee, cup, to sit, to drink, to chat, cozy, atmosphere",
        "hint_structure": "Auf dem Bild sieht man ein ... Im Vordergrund ... An den Tischen ... Die Menschen wirken ... Das Café hat eine ... Atmosphäre.",
        "hint_example": "Auf dem Bild sieht man ein gemütliches Café, in dem mehrere Personen Kaffee trinken und sich unterhalten.",
    },
    {
        "id": "city_street",
        "url": "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=800&auto=format&fit=crop&q=80",
        "context_tr": "Bir şehir caddesinin gece görünümü. Işıklar parlıyor, insanlar yürüyor.",
        "context_en": "A city street at night. Lights are glowing and people are walking.",
        "vocab_tr": "die Straße, die Stadt, die Nacht, das Licht, die Menschen, gehen, beleuchtet, lebendig",
        "vocab_en": "street, city, night, light, people, to walk, illuminated, lively",
        "hint_structure": "Das Bild zeigt ... Es ist ... Uhr / Es ist Nacht. Im Hintergrund sieht man ... Viele Menschen ... Die Straße wirkt ...",
        "hint_example": "Das Bild zeigt eine belebte Stadtstraße bei Nacht, die von vielen Lichtern erleuchtet wird.",
    },
    {
        "id": "park_nature",
        "url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&auto=format&fit=crop&q=80",
        "context_tr": "Yeşil ağaçlarla dolu güzel bir park. Işık ağaçların arasından süzülüyor.",
        "context_en": "A beautiful park full of green trees. Light filters through the trees.",
        "vocab_tr": "der Park, der Baum, das Licht, die Natur, grün, ruhig, spazieren gehen, die Umgebung",
        "vocab_en": "park, tree, light, nature, green, peaceful, to take a walk, surroundings",
        "hint_structure": "Auf dem Bild sieht man einen ... Im Vordergrund ... Die Bäume sind ... Es scheint, dass ... Das Bild vermittelt eine ... Stimmung.",
        "hint_example": "Auf dem Bild sieht man einen ruhigen Park mit hohen grünen Bäumen, durch die das Sonnenlicht scheint.",
    },
    {
        "id": "office_work",
        "url": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&auto=format&fit=crop&q=80",
        "context_tr": "Modern bir ofis ortamı. Çalışanlar masalarında bilgisayarla çalışıyor.",
        "context_en": "A modern office environment. Employees work at their desks with computers.",
        "vocab_tr": "das Büro, der Schreibtisch, der Computer, arbeiten, die Kollegen, modern, hell, konzentriert",
        "vocab_en": "office, desk, computer, to work, colleagues, modern, bright, focused",
        "hint_structure": "Das Bild zeigt ein ... Im Vordergrund/Hintergrund sieht man ... Die Personen ... Die Büroumgebung wirkt ... Es scheint, dass ...",
        "hint_example": "Das Bild zeigt ein modernes, helles Büro, in dem Mitarbeiter konzentriert an ihren Computern arbeiten.",
    },
    {
        "id": "train_journey",
        "url": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800&auto=format&fit=crop&q=80",
        "context_tr": "Bir tren içi. Yolcular oturuyor, bazıları pencereden dışarı bakıyor.",
        "context_en": "Inside a train. Passengers are seated, some looking out the window.",
        "vocab_tr": "der Zug, der Bahnhof, der Fahrgast, das Fenster, reisen, sitzen, schauen, die Fahrt",
        "vocab_en": "train, station, passenger, window, to travel, to sit, to look, journey",
        "hint_structure": "Auf dem Bild sieht man das Innere eines ... Im Vordergrund sitzen ... Die Fahrgäste ... Durch das Fenster ... Die Atmosphäre wirkt ...",
        "hint_example": "Auf dem Bild sieht man das Innere eines modernen Zuges, in dem Fahrgäste sitzen und die vorbeiziehende Landschaft beobachten.",
    },
    {
        "id": "sport_outdoor",
        "url": "https://images.unsplash.com/photo-1461897104016-0b3b00cc81ee?w=800&auto=format&fit=crop&q=80",
        "context_tr": "İnsanlar açık havada spor yapıyor. Koşuyorlar ve egzersiz yapıyorlar.",
        "context_en": "People doing sport outdoors. They are running and exercising.",
        "vocab_tr": "der Sport, laufen, trainieren, die Bewegung, gesund, das Wetter, draußen, die Energie",
        "vocab_en": "sport, to run, to train, movement, healthy, weather, outside, energy",
        "hint_structure": "Das Bild zeigt Menschen beim ... Im Vordergrund ... Die Personen wirken ... Das Wetter ist ... Sport macht ...",
        "hint_example": "Das Bild zeigt Menschen, die im Freien Sport treiben und joggen.",
    },
    {
        "id": "supermarket",
        "url": "https://images.unsplash.com/photo-1604719312566-8912e9c8a213?w=800&auto=format&fit=crop&q=80",
        "context_tr": "Bir süpermarket içinde alışveriş yapan insanlar. Raflar ürünlerle dolu.",
        "context_en": "People shopping inside a supermarket. Shelves are full of products.",
        "vocab_tr": "der Supermarkt, einkaufen, das Regal, die Produkte, der Einkaufswagen, wählen, günstig, die Kasse",
        "vocab_en": "supermarket, to shop, shelf, products, shopping cart, to choose, affordable, checkout",
        "hint_structure": "Auf dem Bild sieht man einen ... Die Regale sind ... Im Vordergrund ... Eine Person ... Man kann erkennen, dass ...",
        "hint_example": "Auf dem Bild sieht man einen großen Supermarkt, in dem Kunden zwischen vollen Regalen einkaufen.",
    },
    {
        "id": "library",
        "url": "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=800&auto=format&fit=crop&q=80",
        "context_tr": "Büyük ve sessiz bir kütüphane. Kitap rafları yüksek tavana kadar uzanıyor.",
        "context_en": "A large, quiet library. Bookshelves reach up to the high ceiling.",
        "vocab_tr": "die Bibliothek, das Buch, das Regal, lesen, still, hoch, lernen, studieren",
        "vocab_en": "library, book, shelf, to read, quiet, high, to learn, to study",
        "hint_structure": "Das Bild zeigt eine ... Die Regale sind ... Im Raum ... Die Atmosphäre ist ... Man fühlt, dass dieser Ort ...",
        "hint_example": "Das Bild zeigt eine imposante Bibliothek mit hohen Bücherregalen, die eine ruhige Lernumgebung schaffen.",
    },
    {
        "id": "restaurant",
        "url": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&auto=format&fit=crop&q=80",
        "context_tr": "Şık bir restoranın içi. Misafirler masalarda oturup yemek yiyor.",
        "context_en": "The interior of an elegant restaurant. Guests sit at tables and eat.",
        "vocab_tr": "das Restaurant, das Essen, der Kellner, die Speisekarte, bestellen, elegant, die Kerze, genießen",
        "vocab_en": "restaurant, food, waiter, menu, to order, elegant, candle, to enjoy",
        "hint_structure": "Auf dem Bild sieht man ein ... Die Einrichtung wirkt ... An den Tischen ... Die Gäste ... Das Restaurant hat eine ...",
        "hint_example": "Auf dem Bild sieht man ein elegantes Restaurant, in dem Gäste an gedeckten Tischen ein schönes Abendessen genießen.",
    },
    {
        "id": "doctor_office",
        "url": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800&auto=format&fit=crop&q=80",
        "context_tr": "Bir doktor muayenehanesi. Doktor hastasıyla konuşuyor.",
        "context_en": "A doctor's office. A doctor is talking with their patient.",
        "vocab_tr": "der Arzt, die Ärztin, der Patient, die Praxis, untersuchen, gesund, die Gesundheit, erklären",
        "vocab_en": "doctor, physician, patient, practice, to examine, healthy, health, to explain",
        "hint_structure": "Das Bild zeigt eine Arztpraxis. Im Vordergrund ... Der Arzt / Die Ärztin ... Der Patient ... Es scheint, dass ... Die Atmosphäre ...",
        "hint_example": "Das Bild zeigt eine Arztpraxis, in der ein Arzt mit seinem Patienten spricht und ihm die Diagnose erklärt.",
    },
]
# fmt: on


def _lang() -> str:
    return st.session_state.get("ui_lang", "tr")


def _init() -> None:
    defaults = {
        "bild_idx": 0,
        "bild_hint_level": 0,
        "bild_feedback": None,
        "bild_checked": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render(words: list, custom_words: list) -> None:
    _init()

    img = IMAGES[st.session_state.bild_idx % len(IMAGES)]
    ctx = img["context_tr"] if _lang() == "tr" else img["context_en"]

    # Image row
    col_img, col_ctrl = st.columns([5, 1])
    with col_img:
        try:
            st.image(img["url"], use_container_width=True)
        except Exception:
            st.info(f"📷 {ctx}")
        st.caption(f"📷 {ctx}")
    with col_ctrl:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄", use_container_width=True, help=t("bild_btn_new"), key="bild_new_img"):
            new_idx = (st.session_state.bild_idx + random.randint(1, len(IMAGES) - 1)) % len(IMAGES)
            st.session_state.bild_idx = new_idx
            st.session_state.bild_hint_level = 0
            st.session_state.bild_feedback = None
            st.session_state.bild_checked = False
            st.rerun()

    st.markdown("---")

    # Text input
    user_text = st.text_area(
        t("bild_text_label"),
        placeholder=t("bild_text_placeholder"),
        height=180,
        key=f"bild_text_{st.session_state.bild_idx}",
    )

    # Hint + Check row
    col_hint, col_check = st.columns(2)

    with col_hint:
        level = st.session_state.bild_hint_level
        if level == 0:
            if st.button(f"💡 {t('bild_hint_btn_structure')}", use_container_width=True):
                st.session_state.bild_hint_level = 1
                st.rerun()
        elif level == 1:
            if st.button(f"📚 {t('bild_hint_btn_vocab')}", use_container_width=True):
                st.session_state.bild_hint_level = 2
                st.rerun()
        elif level == 2:
            if st.button(f"✍️ {t('bild_hint_btn_example')}", use_container_width=True):
                st.session_state.bild_hint_level = 3
                st.rerun()
        else:
            st.button(f"✅ {t('bild_hint_all_shown')}", use_container_width=True, disabled=True)

    with col_check:
        ai = get_ai_service()
        already_done = st.session_state.bild_checked
        if st.button(
            f"✅ {t('bild_btn_check')}",
            use_container_width=True,
            type="primary",
            disabled=already_done or not user_text.strip(),
        ):
            if not ai.can_generate():
                st.error(t("bild_ai_required"))
            else:
                with st.spinner(t("bild_spinner")):
                    feedback = ai.check_bildbeschreibung(ctx, user_text.strip())
                if feedback:
                    st.session_state.bild_feedback = feedback
                    st.session_state.bild_checked = True
                    add_xp(20)
                    persist_current_user()
                    st.rerun()
                else:
                    st.error(t("bild_check_error"))

    # Progressive hints
    _render_hints(img)

    # Feedback
    if st.session_state.bild_feedback:
        _render_feedback(st.session_state.bild_feedback)
        if st.button(f"🔄 {t('bild_btn_next_img')}", use_container_width=True, type="primary"):
            new_idx = (st.session_state.bild_idx + 1) % len(IMAGES)
            st.session_state.bild_idx = new_idx
            st.session_state.bild_hint_level = 0
            st.session_state.bild_feedback = None
            st.session_state.bild_checked = False
            st.rerun()


def _render_hints(img: dict) -> None:
    level = st.session_state.bild_hint_level
    if level < 1:
        return

    if level >= 1:
        with st.expander(f"💡 {t('bild_hint_structure')}", expanded=True):
            st.markdown(
                f"<div style='font-family:monospace;background:#f1f5f9;padding:0.8rem;"
                f"border-radius:8px;font-size:0.9rem;color:#334155'>{img['hint_structure']}</div>",
                unsafe_allow_html=True,
            )

    if level >= 2:
        with st.expander(f"📚 {t('bild_hint_vocab')}", expanded=True):
            vocab = img["vocab_tr"] if _lang() == "tr" else img["vocab_en"]
            tags = [v.strip() for v in vocab.split(",")]
            tag_html = " ".join(
                f"<span style='display:inline-block;background:#dbeafe;color:#1d4ed8;"
                f"padding:3px 10px;border-radius:16px;font-size:0.85rem;margin:2px'>{v}</span>"
                for v in tags
            )
            st.markdown(tag_html, unsafe_allow_html=True)

    if level >= 3:
        with st.expander(f"✍️ {t('bild_hint_example')}", expanded=True):
            st.markdown(
                f"<div style='padding:0.7rem 1rem;background:#f0fdf4;border-left:3px solid #22c55e;"
                f"border-radius:8px;font-style:italic;color:#166534'>{img['hint_example']}</div>",
                unsafe_allow_html=True,
            )


def _render_feedback(fb: dict) -> None:
    grade = fb.get("grade", 3)
    grade_colors = {1: "#22c55e", 2: "#84cc16", 3: "#eab308", 4: "#f97316", 5: "#ef4444", 6: "#dc2626"}
    grade_labels = {1: "Sehr gut", 2: "Gut", 3: "Befriedigend", 4: "Ausreichend", 5: "Mangelhaft", 6: "Ungenügend"}
    color = grade_colors.get(grade, "#64748b")
    label = grade_labels.get(grade, "")

    st.markdown("---")
    st.markdown(f"### 🎓 {t('bild_feedback_title')}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"<div style='text-align:center;padding:1.2rem 0.5rem;background:{color}18;"
            f"border:2px solid {color};border-radius:12px'>"
            f"<div style='font-size:2.8rem;font-weight:800;color:{color}'>{grade}</div>"
            f"<div style='font-size:0.85rem;font-weight:600;color:{color};margin-top:4px'>{label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col2:
        errors = fb.get("grammar_errors", "")
        st.markdown(f"**{t('bild_fb_grammar')}**")
        if errors and errors.lower() not in ("keine fehler", "no errors", "-"):
            st.warning(errors)
        else:
            st.success("✅ " + ("Keine Fehler!" if _lang() == "de" else t("bild_fb_no_errors")))
    with col3:
        vocab = fb.get("vocab_feedback", "")
        st.markdown(f"**{t('bild_fb_vocab')}**")
        if vocab:
            st.info(vocab)

    if fb.get("structure_feedback"):
        st.markdown(
            f"<div style='padding:0.7rem 1rem;background:#eff6ff;border-left:3px solid #3b82f6;"
            f"border-radius:8px;margin-top:0.5rem'>"
            f"<strong>🏗️ {t('bild_fb_structure')}</strong> {fb['structure_feedback']}</div>",
            unsafe_allow_html=True,
        )

    if fb.get("example"):
        st.markdown(
            f"<div style='padding:0.7rem 1rem;background:#f0fdf4;border-left:3px solid #22c55e;"
            f"border-radius:8px;margin-top:0.5rem;font-style:italic'>"
            f"<strong>✍️ {t('bild_fb_example')}</strong> {fb['example']}</div>",
            unsafe_allow_html=True,
        )

    if fb.get("summary"):
        st.markdown(f"> 💬 {fb['summary']}")

    st.success(f"⚡ +20 XP {t('bild_xp_earned')}")
