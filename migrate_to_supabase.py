"""
One-time migration: users.json + challenges.json -> Supabase.
Run once from the project root:

    pip install supabase python-dotenv
    python migrate_to_supabase.py

Requires .env with SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

DATA_DIR = Path(__file__).parent / "data"
USERS_FILE = DATA_DIR / "users.json"
CHALLENGES_FILE = DATA_DIR / "challenges.json"

_ERROR_MARKERS = (
    "AI Hatas", "AI Error", "Error code:", "insufficient_quota",
    "Quota exceeded", "invalid_request_error", "servis hatas",
)


def _clean_ai_cache(cache: dict) -> dict:
    return {
        k: v for k, v in cache.items()
        if isinstance(v, str) and not any(m in v for m in _ERROR_MARKERS)
    }


def migrate_users():
    if not USERS_FILE.exists():
        print("users.json not found, skipping.")
        return

    with open(USERS_FILE, encoding="utf-8") as f:
        users = json.load(f)

    print(f"Found {len(users)} users.")
    ok = 0
    for username, data in users.items():
        progress = data.get("progress", {})
        ai_cache = data.get("ai_cache", {})

        # Migrate ai_example from progress entries into ai_cache
        for word, p in progress.items():
            if "ai_example" in p:
                val = p.pop("ai_example")
                if isinstance(val, str) and not any(m in val for m in _ERROR_MARKERS):
                    ai_cache.setdefault(word, val)

        ai_cache = _clean_ai_cache(ai_cache)

        row = {
            "username": username,
            "password_hash": data.get("password_hash", ""),
            "password_salt": data.get("password_salt", ""),
            "created_at": data.get("created_at", ""),
            "progress": progress,
            "last_study_date": data.get("last_study_date"),
            "daily_streak": data.get("daily_streak", 0),
            "total_study_minutes": int(data.get("total_study_minutes", 0)),
            "custom_words": data.get("custom_words", []),
            "total_xp": int(data.get("total_xp", 0)),
            "earned_achievements": [
                x if isinstance(x, str) else x.get("id", "")
                for x in data.get("earned_achievements", []) if x
            ],
            "ai_cache": ai_cache,
            "daily_tasks": data.get("daily_tasks", {}),
            "grace_period_used": bool(data.get("grace_period_used", False)),
            "challenges": data.get("challenges", {}),
        }

        try:
            sb.table("users").upsert(row).execute()
            print(f"  OK {username}")
            ok += 1
        except Exception as e:
            print(f"  FAIL {username}: {e}")

    print(f"\nUsers: {ok}/{len(users)} migrated.")


def migrate_challenges():
    if not CHALLENGES_FILE.exists():
        print("challenges.json not found, skipping.")
        return

    with open(CHALLENGES_FILE, encoding="utf-8") as f:
        challenges = json.load(f)

    print(f"\nFound {len(challenges)} community challenges.")
    ok = 0
    for cid, data in challenges.items():
        try:
            sb.table("community_challenges").upsert({"week_key": cid, "data": data}).execute()
            print(f"  OK {cid}")
            ok += 1
        except Exception as e:
            print(f"  FAIL {cid}: {e}")

    print(f"Challenges: {ok}/{len(challenges)} migrated.")


if __name__ == "__main__":
    print("=== Supabase Migration Starting ===\n")
    migrate_users()
    migrate_challenges()
    print("\n=== Migration Complete ===")
