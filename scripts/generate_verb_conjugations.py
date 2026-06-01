"""
One-time batch script: adds prateritum + perfekt fields to all Verb entries
in data/words.json using DeepSeek.

Run from the project root:
    python scripts/generate_verb_conjugations.py

Safe to re-run: already-processed verbs are skipped.
"""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

WORDS_PATH = Path("data/words.json")
BATCH_SIZE = 40
DELAY_BETWEEN_BATCHES = 1.2  # seconds


def build_prompt(verbs: list) -> str:
    lines = "\n".join(f"- {v['word']}" for v in verbs)
    return (
        "For each German verb below, provide the Präteritum (ich-form) and Perfekt.\n"
        "Use EXACTLY this format — one line per verb, nothing else:\n"
        "VERB: [infinitive] | PRT: [ich-form] | PRF: [hat/ist + Partizip II]\n\n"
        "Examples:\n"
        "VERB: fahren | PRT: fuhr | PRF: ist gefahren\n"
        "VERB: lernen | PRT: lernte | PRF: hat gelernt\n"
        "VERB: abfahren | PRT: fuhr ab | PRF: ist abgefahren\n"
        "VERB: sich waschen | PRT: wusch mich | PRF: hat sich gewaschen\n\n"
        f"Verbs:\n{lines}"
    )


def parse_response(text: str) -> dict:
    result = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if "VERB:" not in line or "| PRT:" not in line or "| PRF:" not in line:
            continue
        try:
            parts = [p.strip() for p in line.split("|")]
            verb = parts[0].replace("VERB:", "").strip()
            prt  = parts[1].replace("PRT:", "").strip()
            prf  = parts[2].replace("PRF:", "").strip()
            if verb and prt and prf:
                result[verb] = {"prateritum": prt, "perfekt": prf}
        except (IndexError, ValueError):
            continue
    return result


def main() -> None:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise SystemExit("DEEPSEEK_API_KEY not found in environment / .env")

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

    with open(WORDS_PATH, encoding="utf-8") as f:
        words = json.load(f)

    word_map = {w["word"]: w for w in words}
    todo = [w for w in words if w.get("type") == "Verb" and not w.get("prateritum")]
    print(f"Total verbs to process: {len(todo)}")

    total_updated = 0
    total_missed  = 0

    for batch_start in range(0, len(todo), BATCH_SIZE):
        batch = todo[batch_start : batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (len(todo) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"\nBatch {batch_num}/{total_batches}: {[v['word'] for v in batch[:4]]} ...")

        prompt = build_prompt(batch)
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
            )
            parsed = parse_response(resp.choices[0].message.content)

            batch_updated = 0
            for v in batch:
                if v["word"] in parsed:
                    word_map[v["word"]]["prateritum"] = parsed[v["word"]]["prateritum"]
                    word_map[v["word"]]["perfekt"]    = parsed[v["word"]]["perfekt"]
                    batch_updated += 1
                else:
                    print(f"  MISSED: {v['word']}")
                    total_missed += 1

            total_updated += batch_updated
            print(f"  → {batch_updated}/{len(batch)} updated")

        except Exception as e:
            print(f"  ERROR in batch {batch_num}: {e}")

        # Save after every batch (safe to interrupt and resume)
        with open(WORDS_PATH, "w", encoding="utf-8") as f:
            json.dump(words, f, ensure_ascii=False, indent=2)

        if batch_start + BATCH_SIZE < len(todo):
            time.sleep(DELAY_BETWEEN_BATCHES)

    print(f"\nDone. Updated: {total_updated}  |  Missed: {total_missed}")
    coverage = sum(1 for w in words if w.get("type") == "Verb" and w.get("prateritum"))
    total_verbs = sum(1 for w in words if w.get("type") == "Verb")
    print(f"Coverage: {coverage}/{total_verbs} verbs have conjugations")


if __name__ == "__main__":
    main()
