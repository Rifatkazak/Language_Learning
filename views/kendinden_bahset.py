import random
import streamlit as st

from services.ai_service import get_ai_service
from services.gamification import add_xp
from storage.user_store import persist_current_user
from core.i18n import t

# fmt: off
PROMPTS = [
    {
        "id": "basis_vorstellung",
        "subject_tr": "Temel öz tanıtım",
        "subject_en": "Basic self-introduction",
        "task_tr": "Bir dil kursunun ilk günündesiniz. Kendinizi sınıfa tanıtın.",
        "task_en": "It's the first day of a language course. Introduce yourself to the class.",
        "points_tr": ["Adınızı ve nereden geldiğinizi söyleyin", "Kaç yaşında olduğunuzu belirtin", "Ne iş yaptığınızı anlatın", "Neden Almanca öğrendiğinizi açıklayın"],
        "points_en": ["Say your name and where you are from", "State your age", "Describe what you do for work", "Explain why you are learning German"],
        "hint_phrases_tr": "Ich heiße ... · Ich komme aus ... · Ich bin ... Jahre alt · Von Beruf bin ich ... · Ich lerne Deutsch, weil ...",
        "hint_phrases_en": "Ich heiße ... · Ich komme aus ... · Ich bin ... Jahre alt · Von Beruf bin ich ... · Ich lerne Deutsch, weil ...",
        "hint_example": "Ich heiße Ali und komme aus der Türkei. Ich bin 28 Jahre alt und wohne seit zwei Jahren in Deutschland. Von Beruf bin ich Ingenieur. Ich lerne Deutsch, weil ich hier arbeiten möchte.",
    },
    {
        "id": "freizeit_hobbys",
        "subject_tr": "Hobiler ve boş zaman",
        "subject_en": "Hobbies and free time",
        "task_tr": "Almanca arkadaş bulma sitesinde kendinizi tanıtıyorsunuz. Hobilerinizcden ve boş zamanınızdan bahsedin.",
        "task_en": "You are writing a profile for a German pen-pal website. Tell them about your hobbies and free time.",
        "points_tr": ["En sevdiğiniz hobiyi anlatın", "Haftada ne sıklıkla yaptığınızı belirtin", "Bu hobiyi neden sevdiğinizi açıklayın", "Ortak ilgi alanı olan biriyle ne yapmak istediğinizi söyleyin"],
        "points_en": ["Describe your favourite hobby", "Say how often you do it per week", "Explain why you enjoy it", "Say what you would like to do with someone who shares the same interest"],
        "hint_phrases_tr": "In meiner Freizeit ... · Ich interessiere mich für ... · Ich treibe gerne Sport · Einmal pro Woche ... · Das macht mir Spaß, weil ...",
        "hint_phrases_en": "In meiner Freizeit ... · Ich interessiere mich für ... · Ich treibe gerne Sport · Einmal pro Woche ... · Das macht mir Spaß, weil ...",
        "hint_example": "In meiner Freizeit lese ich sehr gerne Bücher und höre Musik. Ich interessiere mich besonders für Kriminalromane. Außerdem treibe ich zweimal pro Woche Sport – meistens gehe ich joggen. Das hilft mir, Stress abzubauen.",
    },
    {
        "id": "familie_heimat",
        "subject_tr": "Aile ve memleket",
        "subject_en": "Family and hometown",
        "task_tr": "Yeni Alman komşunuz sizi tanımak istiyor. Ailenizden ve memleket/şehrinizden bahsedin.",
        "task_en": "Your new German neighbour wants to get to know you. Tell them about your family and your hometown.",
        "points_tr": ["Aile yapınızı anlatın (evli mi? çocuk? kardeş?)", "Ailenizin nerede yaşadığını belirtin", "Memleket veya şehrinizi kısaca tanıtın", "Ailenizi ne sıklıkla ziyaret ettiğinizi söyleyin"],
        "points_en": ["Describe your family (married? children? siblings?)", "Say where your family lives", "Briefly describe your hometown or city", "Say how often you visit your family"],
        "hint_phrases_tr": "Ich bin verheiratet / ledig · Ich habe ... Geschwister · Meine Eltern leben in ... · Meine Heimatstadt heißt ... · Ich besuche meine Familie ...",
        "hint_phrases_en": "Ich bin verheiratet / ledig · Ich habe ... Geschwister · Meine Eltern leben in ... · Meine Heimatstadt heißt ... · Ich besuche meine Familie ...",
        "hint_example": "Ich bin ledig und habe zwei Geschwister – einen Bruder und eine Schwester. Meine ganze Familie lebt noch in Istanbul. Ich besuche sie zweimal im Jahr. Istanbul ist eine sehr lebendige Stadt mit vielen Sehenswürdigkeiten.",
    },
    {
        "id": "beruf_ausbildung",
        "subject_tr": "Meslek ve eğitim",
        "subject_en": "Job and education",
        "task_tr": "Bir iş görüşmesine hazırlanıyorsunuz. Eğitiminizden ve iş deneyiminizden bahsedin.",
        "task_en": "You are preparing for a job interview. Talk about your education and work experience.",
        "points_tr": ["Hangi okulu/üniversiteyi bitirdiğinizi söyleyin", "Mesleğinizi ve şu anki işinizi anlatın", "İş deneyiminizden bahsedin", "Güçlü yönlerinizden birini belirtin"],
        "points_en": ["State which school/university you finished", "Describe your profession and current job", "Talk about your work experience", "Mention one of your strengths"],
        "hint_phrases_tr": "Ich habe ... studiert / eine Ausbildung als ... gemacht · Seit ... Jahren arbeite ich als ... · Ich habe Erfahrung in ... · Meine Stärke ist ...",
        "hint_phrases_en": "Ich habe ... studiert / eine Ausbildung als ... gemacht · Seit ... Jahren arbeite ich als ... · Ich habe Erfahrung in ... · Meine Stärke ist ...",
        "hint_example": "Ich habe Informatik an der Universität in Ankara studiert. Seit drei Jahren arbeite ich als Softwareentwickler in einem internationalen Unternehmen. Ich habe vor allem Erfahrung in der Webentwicklung. Meine Stärke ist, dass ich schnell lerne.",
    },
    {
        "id": "wohnort_alltag",
        "subject_tr": "Yaşam yeri ve günlük hayat",
        "subject_en": "Where you live and daily life",
        "task_tr": "Almanya'daki yaşamınızı tanıtın. Nerede yaşadığınızı ve günlük hayatınızın nasıl geçtiğini anlatın.",
        "task_en": "Introduce your life in Germany. Describe where you live and what a typical day looks like for you.",
        "points_tr": ["Hangi şehirde ve nasıl bir yerde yaşadığınızı anlatın", "Günlük rutininizi kısaca açıklayın", "Almanya'da sevdiğiniz bir şey söyleyin", "Zor bulduğunuz bir şeyi belirtin"],
        "points_en": ["Describe the city and type of home you live in", "Briefly describe your daily routine", "Mention one thing you like about Germany", "State one thing you find difficult"],
        "hint_phrases_tr": "Ich wohne in ... in einer ... (Wohnung/WG) · Mein Alltag beginnt um ... · Was mir an Deutschland gefällt, ist ... · Das finde ich schwierig: ...",
        "hint_phrases_en": "Ich wohne in ... in einer ... (Wohnung/WG) · Mein Alltag beginnt um ... · Was mir an Deutschland gefällt, ist ... · Das finde ich schwierig: ...",
        "hint_example": "Ich wohne seit einem Jahr in München in einer kleinen Zweizimmerwohnung. Mein Alltag beginnt um 7 Uhr morgens – ich frühstücke, dann fahre ich mit der U-Bahn zur Arbeit. Was mir an Deutschland besonders gefällt, ist die gute Infrastruktur. Manchmal finde ich die Sprache noch schwierig.",
    },
    {
        "id": "zukunftsplaene",
        "subject_tr": "Gelecek planları",
        "subject_en": "Future plans",
        "task_tr": "Bir integrasyon kursunda tanıştığınız biriyle konuşuyorsunuz. Gelecek planlarınızdan bahsedin.",
        "task_en": "You are talking to someone you met at an integration course. Tell them about your future plans.",
        "points_tr": ["Kısa vadeli bir hedefinizi anlatın (önümüzdeki 1 yıl)", "Uzun vadeli bir hedefinizi belirtin", "Bu hedeflere ulaşmak için ne yaptığınızı açıklayın", "Almanca öğrenmenin planlarınız için önemini söyleyin"],
        "points_en": ["Describe a short-term goal (next 1 year)", "State a long-term goal", "Explain what you are doing to achieve these goals", "Say why learning German is important for your plans"],
        "hint_phrases_tr": "In einem Jahr möchte ich ... · Mein großes Ziel ist es, ... · Ich lerne jeden Tag Deutsch, weil ... · Ich hoffe, dass ich bald ...",
        "hint_phrases_en": "In einem Jahr möchte ich ... · Mein großes Ziel ist es, ... · Ich lerne jeden Tag Deutsch, weil ... · Ich hoffe, dass ich bald ...",
        "hint_example": "In einem Jahr möchte ich die B2-Prüfung ablegen. Mein großes Ziel ist es, in meinem Beruf als Ärztin auch in Deutschland arbeiten zu können. Deshalb lerne ich jeden Tag Deutsch und besuche einen Sprachkurs. Ohne gutes Deutsch wäre das unmöglich.",
    },
]
# fmt: on


def _lang() -> str:
    return st.session_state.get("ui_lang", "tr")


def _init() -> None:
    defaults = {
        "vorst_idx": 0,
        "vorst_hint_level": 0,
        "vorst_feedback": None,
        "vorst_checked": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render(words: list, custom_words: list) -> None:
    _init()

    prompt = PROMPTS[st.session_state.vorst_idx % len(PROMPTS)]
    lang = _lang()

    subject = prompt["subject_tr"] if lang == "tr" else prompt["subject_en"]
    task = prompt["task_tr"] if lang == "tr" else prompt["task_en"]
    points = prompt["points_tr"] if lang == "tr" else prompt["points_en"]

    # Task card
    col_card, col_ctrl = st.columns([5, 1])
    with col_card:
        points_html = "".join(f"<li>{p}</li>" for p in points)
        st.markdown(
            f"<div style='padding:1.2rem 1.4rem;background:#f8fafc;"
            f"border:1px solid #e2e8f0;border-radius:12px;'>"
            f"<div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.6rem'>"
            f"<span style='background:#0ea5e918;color:#0ea5e9;font-size:0.75rem;"
            f"font-weight:600;padding:2px 10px;border-radius:20px;border:1px solid #0ea5e940'>"
            f"👤 {t('vorst_task_label')}</span>"
            f"<span style='font-weight:600;color:#1e293b'>{subject}</span></div>"
            f"<p style='color:#475569;margin:0 0 0.7rem'>{task}</p>"
            f"<ul style='margin:0;padding-left:1.3rem;color:#334155'>{points_html}</ul>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_ctrl:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄", use_container_width=True, help=t("vorst_btn_new"), key="vorst_new"):
            new_idx = (st.session_state.vorst_idx + random.randint(1, len(PROMPTS) - 1)) % len(PROMPTS)
            st.session_state.vorst_idx = new_idx
            st.session_state.vorst_hint_level = 0
            st.session_state.vorst_feedback = None
            st.session_state.vorst_checked = False
            st.rerun()

    st.markdown("---")

    user_text = st.text_area(
        t("vorst_text_label"),
        placeholder=t("vorst_text_placeholder"),
        height=220,
        key=f"vorst_text_{st.session_state.vorst_idx}",
    )

    col_hint, col_check = st.columns(2)
    with col_hint:
        level = st.session_state.vorst_hint_level
        if level == 0:
            if st.button(f"💡 {t('vorst_hint_btn_phrases')}", use_container_width=True, key="vorst_h1"):
                st.session_state.vorst_hint_level = 1
                st.rerun()
        elif level == 1:
            if st.button(f"✍️ {t('vorst_hint_btn_example')}", use_container_width=True, key="vorst_h2"):
                st.session_state.vorst_hint_level = 2
                st.rerun()
        else:
            st.button(f"✅ {t('bild_hint_all_shown')}", use_container_width=True, disabled=True, key="vorst_hall")

    with col_check:
        ai = get_ai_service()
        if st.button(
            f"✅ {t('vorst_btn_check')}",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.vorst_checked or not user_text.strip(),
            key="vorst_check",
        ):
            if not ai.can_generate():
                st.error(t("bild_ai_required"))
            else:
                task_context = f"{task} ({', '.join(points)})"
                with st.spinner(t("bild_spinner")):
                    feedback = ai.check_vorstellung(
                        task_context=task_context,
                        user_text=user_text.strip(),
                    )
                if feedback:
                    st.session_state.vorst_feedback = feedback
                    st.session_state.vorst_checked = True
                    add_xp(25)
                    persist_current_user()
                    st.rerun()
                else:
                    st.error(t("bild_check_error"))

    _render_hints(prompt)

    if st.session_state.vorst_feedback:
        _render_feedback(st.session_state.vorst_feedback)
        if st.button(f"🔄 {t('vorst_btn_next')}", use_container_width=True, type="primary", key="vorst_next"):
            new_idx = (st.session_state.vorst_idx + 1) % len(PROMPTS)
            st.session_state.vorst_idx = new_idx
            st.session_state.vorst_hint_level = 0
            st.session_state.vorst_feedback = None
            st.session_state.vorst_checked = False
            st.rerun()


def _render_hints(prompt: dict) -> None:
    level = st.session_state.vorst_hint_level
    if level < 1:
        return
    lang = _lang()

    if level >= 1:
        with st.expander(f"💡 {t('vorst_hint_phrases')}", expanded=True):
            phrases_raw = prompt["hint_phrases_tr"] if lang == "tr" else prompt["hint_phrases_en"]
            phrases = [p.strip() for p in phrases_raw.split("·")]
            tag_html = " ".join(
                f"<span style='display:inline-block;background:#e0f2fe;color:#0369a1;"
                f"padding:3px 10px;border-radius:16px;font-size:0.85rem;margin:2px'>{p}</span>"
                for p in phrases if p
            )
            st.markdown(tag_html, unsafe_allow_html=True)

    if level >= 2:
        with st.expander(f"✍️ {t('vorst_hint_example')}", expanded=True):
            st.markdown(
                f"<div style='padding:0.7rem 1rem;background:#f0fdf4;border-left:3px solid #22c55e;"
                f"border-radius:8px;font-style:italic;color:#166534'>{prompt['hint_example']}</div>",
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
            st.success(f"✅ {t('bild_fb_no_errors')}")
    with col3:
        fluency = fb.get("fluency_feedback", "")
        st.markdown(f"**{t('vorst_fb_fluency')}**")
        if fluency:
            st.info(fluency)

    if fb.get("content_feedback"):
        st.markdown(
            f"<div style='padding:0.7rem 1rem;background:#fefce8;border-left:3px solid #eab308;"
            f"border-radius:8px;margin-top:0.5rem'>"
            f"<strong>📋 {t('vorst_fb_content')}</strong> {fb['content_feedback']}</div>",
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

    st.success(f"⚡ +25 XP {t('bild_xp_earned')}")
