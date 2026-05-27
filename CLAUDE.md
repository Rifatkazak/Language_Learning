# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app runs at `http://localhost:8501`. No build step required.

Requires a `.env` file with `DEEPSEEK_API_KEY=sk-...`.

## Architecture

This is a **Streamlit** multi-page app for learning German (Goethe B1 vocabulary). Navigation is state-driven: `st.session_state.page` holds the current page name, and `views/router.py` dispatches to the appropriate view handler.

### Layer overview

```
app.py                          # Entry: init session, auth gate, render nav + current page
  └── core/session.py           # All st.session_state keys & defaults; page name constants
  └── core/auth.py              # PBKDF2 login/register/logout

ui/navigation.py                # Sidebar, bottom nav bar, leaderboard
ui/components.py                # Reusable widgets (streak, XP bar, daily tasks)
ui/styles.py                    # CSS injection

views/router.py                 # Maps page name → view handler
views/{home,flashcard,quiz,games,challenge,word_list,add_word,stats,quick_actions}.py

services/game_engine.py         # Deck initialization, game state, answer handling
services/progress.py            # Word mastery (easy/ok/hard), spaced-repetition scheduling
services/gamification.py        # XP, achievements, levels, streaks, daily tasks
services/ai_service.py          # DeepSeek API: example sentences, dialogues, TTS (gTTS)

storage/user_store.py           # Load/save data/users.json; data migrations
storage/word_repo.py            # Load data/words.json (cached with st.cache_data)
models/word.py                  # Word & WordProgress dataclasses
```

### Data storage

All persistence is flat JSON — no database:
- `data/users.json` — user profiles, hashed passwords, per-word progress, XP, achievements, AI cache
- `data/words.json` — master vocabulary list (word, article, type, translation)
- Duplicate copies `users.json` / `words.json` at the repo root are leftovers and not used by the app.

### Key patterns

- **Session state** is the single source of truth during a session. `core/session.py` defines all keys and defaults.
- **Page navigation** works by setting `st.session_state.page` then calling `st.rerun()` — never use `st.switch_page`.
- **AI calls** go through `services/ai_service.py`, which uses the OpenAI SDK pointed at `https://api.deepseek.com/v1`. Results are cached in `users.json` under `ai_cache` to avoid repeat API calls.
- **Spaced repetition** schedules next review at +1/+3/+7 days based on easy/ok/hard rating.

### Adding a new page

1. Create `views/my_page.py` with a `render()` function.
2. Add a page constant in `core/session.py`.
3. Register it in `views/router.py`.
4. Add a navigation button in `ui/navigation.py`.
