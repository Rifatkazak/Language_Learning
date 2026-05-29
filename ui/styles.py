import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main .block-container {
    max-width: 920px;
    padding-top: 1.5rem;
    padding-bottom: 4rem;
}

/* Sidebar */
[data-testid="stSidebarContent"] {
    padding: 1rem 0.75rem;
}

/* Cards */
.card {
    background: white;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
    margin-bottom: 1rem;
    border: 1px solid #f1f5f9;
}

.card-blue {
    background: #f0f7ff;
    border: 1.5px solid #bfdbfe;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}

/* Section label */
.section-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 0.75rem;
    display: block;
}

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
.word-big     { font-size: 2.8rem; font-weight: 700; margin: 0.5rem 0; }
.word-tr      { font-size: 1.8rem; color: #a8d8a8; margin: 0.5rem 0; }

.type-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-top: 0.5rem;
}
.type-Verb   { background: #1a3a6b; color: #64b3f4; }
.type-Nomen  { background: #3a1a2e; color: #f48fb1; }
.type-AdjAdv { background: #1a3a2a; color: #81c784; }

/* Progress bar */
.prog-bar-bg   { background: #e2e8f0; border-radius: 8px; height: 8px; margin: 0.3rem 0; }
.prog-bar-fill { border-radius: 8px; height: 8px; background: linear-gradient(90deg,#4a90d9,#27ae60); transition: width 0.5s; }

/* Quiz */
.quiz-option {
    width: 100%;
    padding: 14px 20px;
    margin: 6px 0;
    border-radius: 12px;
    border: 2px solid #e2e8f0;
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
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border-top: 4px solid;
}
.stat-label { font-size: 0.78rem; color: #94a3b8; margin-bottom: 4px; font-weight: 500; }
.stat-val   { font-size: 2.2rem; font-weight: 700; color: #1e293b; }

/* Word rows */
.word-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid #f1f5f9;
}

/* AI example box */
.ai-box {
    background: rgba(74, 144, 217, 0.08);
    border-left: 3px solid #4a90d9;
    border-radius: 0 10px 10px 0;
    padding: 1rem 1.2rem;
    margin-top: 1rem;
    font-size: 0.95rem;
    line-height: 1.7;
}

.swipe-hint {
    text-align: center;
    color: #cbd5e1;
    font-size: 0.75rem;
    padding: 4px;
    animation: pulse 2s infinite;
}
@keyframes pulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }

.action-btn-container {
    position: sticky;
    bottom: 0;
    background: white;
    padding: 12px;
    box-shadow: 0 -2px 12px rgba(0,0,0,0.08);
    z-index: 100;
}

/* Auth */
.auth-container {
    max-width: 420px;
    margin: 4rem auto;
    padding: 2.5rem;
    background: white;
    border-radius: 20px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.12);
}

/* Bottom nav bar separation */
.stColumns [data-testid="stVerticalBlock"] {
    gap: 0 !important;
}

/* Mobile */
@media (max-width: 768px) {
    .stButton > button { min-height: 52px !important; font-size: 1rem !important; padding: 12px 16px !important; }
    .main .block-container { padding: 0.5rem !important; max-width: 100% !important; }
    .flashcard { min-height: 200px !important; padding: 1.5rem 1rem !important; }
    .word-big  { font-size: 2rem !important; }
    [data-testid="stSidebarNav"] { display: none; }
}
</style>
"""


_DARK_CSS = """
<style>
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #1a1f2e !important;
    color: #e2e8f0 !important;
}
[data-testid="stSidebarContent"], [data-testid="stSidebar"] > div {
    background-color: #141924 !important;
}
[data-testid="stSidebarContent"] * { color: #e2e8f0 !important; }
.main .block-container { background-color: #1a1f2e !important; }
.card {
    background: #242b3d !important;
    border-color: #2d3748 !important;
    color: #e2e8f0 !important;
}
.card-blue {
    background: #1a2840 !important;
    border-color: #2d4a6b !important;
}
.stat-card { background: #242b3d !important; color: #e2e8f0 !important; }
.stat-val { color: #e2e8f0 !important; }
.quiz-option {
    background: #242b3d !important;
    border-color: #2d3748 !important;
    color: #e2e8f0 !important;
}
.quiz-option:hover { background: #1a2840 !important; border-color: #4a90d9 !important; }
.auth-container { background: #242b3d !important; }
.action-btn-container { background: #1a1f2e !important; }
.prog-bar-bg { background: #2d3748 !important; }
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] select {
    background-color: #242b3d !important;
    color: #e2e8f0 !important;
    border-color: #2d3748 !important;
}
p, span, label, div { color: #e2e8f0 !important; }
.section-label { color: #64748b !important; }
hr { border-color: #2d3748 !important; }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    if st.session_state.get("dark_mode"):
        st.markdown(_DARK_CSS, unsafe_allow_html=True)
