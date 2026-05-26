import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main .block-container { max-width: 900px; padding-top: 2rem; }

.flashcard {
    background: linear-gradient(135deg, #1e3a5f 0%, #16213e 100%);
    border-radius: 20px; padding: 3rem 2rem; text-align: center;
    min-height: 280px; display: flex; flex-direction: column;
    justify-content: center; align-items: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3); cursor: pointer;
    transition: transform 0.2s; margin: 1rem 0; color: white;
}
.flashcard-front { border-left: 6px solid #4a90d9; }
.flashcard-back  { border-left: 6px solid #27ae60; }
.article-der  { color: #64b3f4; font-weight: 700; font-size: 1.1rem; }
.article-die  { color: #f48fb1; font-weight: 700; font-size: 1.1rem; }
.article-das  { color: #81c784; font-weight: 700; font-size: 1.1rem; }
.word-big { font-size: 2.8rem; font-weight: 700; margin: 0.5rem 0; }
.word-tr  { font-size: 1.8rem; color: #a8d8a8; margin: 0.5rem 0; }
.type-badge {
    display: inline-block; padding: 4px 14px; border-radius: 20px;
    font-size: 0.78rem; font-weight: 600; margin-top: 0.5rem;
}
.type-Verb   { background: #1a3a6b; color: #64b3f4; }
.type-Nomen  { background: #3a1a2e; color: #f48fb1; }
.type-AdjAdv { background: #1a3a2a; color: #81c784; }

.prog-bar-bg   { background: #e0e0e0; border-radius: 8px; height: 10px; margin: 0.3rem 0; }
.prog-bar-fill { border-radius: 8px; height: 10px;
                 background: linear-gradient(90deg,#4a90d9,#27ae60); transition: width 0.5s; }

.quiz-option {
    width: 100%; padding: 14px 20px; margin: 6px 0; border-radius: 12px;
    border: 2px solid #ddd; background: white; font-size: 1rem;
    cursor: pointer; text-align: left; transition: all 0.2s;
}
.quiz-option:hover { border-color: #4a90d9; background: #f0f7ff; }
.quiz-correct { border-color: #27ae60 !important; background: #f0fff4 !important; color: #1a5c30; }
.quiz-wrong   { border-color: #e53935 !important; background: #fff0f0 !important; color: #7b1a1a; }

.stat-card {
    background: white; border-radius: 16px; padding: 1.2rem 1.5rem;
    text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.07); border-top: 4px solid;
}
.stat-label { font-size: 0.8rem; color: #888; margin-bottom: 4px; }
.stat-val   { font-size: 2.2rem; font-weight: 700; }

.word-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 0; border-bottom: 1px solid #f0f0f0;
}
.ai-box {
    background: rgba(74, 144, 217, 0.12); border-left: 4px solid #4a90d9;
    border-radius: 0 12px 12px 0; padding: 1rem 1.2rem;
    margin-top: 1rem; font-size: 0.95rem; line-height: 1.7;
    color: inherit;
}
.swipe-hint {
    text-align: center; color: #bbb; font-size: 0.75rem; padding: 4px;
    animation: pulse 2s infinite;
}
@keyframes pulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }
.action-btn-container {
    position: sticky; bottom: 0; background: white;
    padding: 12px; box-shadow: 0 -2px 10px rgba(0,0,0,0.1); z-index: 100;
}

/* Auth form */
.auth-container {
    max-width: 420px; margin: 4rem auto; padding: 2.5rem;
    background: white; border-radius: 20px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.12);
}

@media (max-width: 768px) {
    .stButton > button { min-height: 52px !important; font-size: 1rem !important; padding: 12px 16px !important; }
    .main .block-container { padding: 0.5rem !important; max-width: 100% !important; }
    .flashcard { min-height: 200px !important; padding: 1.5rem 1rem !important; }
    .word-big  { font-size: 2rem !important; }
    [data-testid="stSidebarNav"] { display: none; }
}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
