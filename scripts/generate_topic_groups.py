"""
Run once to classify all words by topic and save to data/word_topics.json.
Usage: python scripts/generate_topic_groups.py
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from openai import OpenAI

TOPICS = [
    "Work & Career",
    "Health & Body",
    "Home & Living",
    "Travel & Transport",
    "Education",
    "Sports & Hobbies",
    "Food & Drink",
    "Family & Relationships",
    "Bureaucracy & Law",
    "Nature & Environment",
    "Shopping",
    "Technology & Media",
    "Emotions & Personality",
    "Time & Calendar",
]

TOPIC_TR = {
    "Work & Career":           "İş & Kariyer",
    "Health & Body":           "Sağlık & Vücut",
    "Home & Living":           "Ev & Yaşam",
    "Travel & Transport":      "Seyahat & Ulaşım",
    "Education":               "Eğitim",
    "Sports & Hobbies":        "Spor & Hobiler",
    "Food & Drink":            "Yiyecek & İçecek",
    "Family & Relationships":  "Aile & İlişkiler",
    "Bureaucracy & Law":       "Bürokrasi & Hukuk",
    "Nature & Environment":    "Doğa & Çevre",
    "Shopping":                "Alışveriş",
    "Technology & Media":      "Teknoloji & Medya",
    "Emotions & Personality":  "Duygular & Kişilik",
    "Time & Calendar":         "Zaman & Takvim",
}

BATCH_SIZE = 100
DATA_DIR = Path(__file__).parent.parent / "data"


def classify_batch(client, words_batch):
    lines = "\n".join(
        f"{w['word']} ({w.get('translation_en') or w.get('translation', '')})"
        for w in words_batch
    )
    topics_str = " | ".join(TOPICS)
    prompt = (
        f"Classify each German word into exactly one of these topics: {topics_str}\n\n"
        f"Words:\n{lines}\n\n"
        "Reply with one line per word, exactly:\n"
        "WORD: [German word] | TOPIC: [topic]\n"
        "Use the exact topic names listed. If none fit well, pick the closest one."
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2500,
    )
    result = {}
    for line in response.choices[0].message.content.strip().split("\n"):
        line = line.strip().lstrip("-•* ")
        # Try strict format first: WORD: x | TOPIC: y
        if "WORD:" in line and "| TOPIC:" in line:
            parts = line.split("| TOPIC:")
            word = parts[0].replace("WORD:", "").strip()
            topic = parts[1].strip() if len(parts) > 1 else TOPICS[0]
        # Fallback: first token is word, last token after → or | is topic
        elif "|" in line:
            parts = line.split("|")
            word = parts[0].strip().split("(")[0].strip()
            topic = parts[-1].strip()
        elif "→" in line or "->" in line:
            sep = "→" if "→" in line else "->"
            parts = line.split(sep)
            word = parts[0].strip().split("(")[0].strip()
            topic = parts[-1].strip() if len(parts) > 1 else ""
        else:
            continue
        # Validate topic
        topic = topic.strip().strip("\"'")
        if topic not in TOPICS:
            # fuzzy match
            matched = next((t for t in TOPICS if t.lower() in topic.lower() or topic.lower() in t.lower()), None)
            topic = matched or TOPICS[0]
        if word:
            result[word] = topic
    return result


def main():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY not set in .env")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

    words_path = DATA_DIR / "words.json"
    with open(words_path, encoding="utf-8") as f:
        words = json.load(f)

    # Load existing results to skip already-classified words
    out_path = DATA_DIR / "word_topics.json"
    groups_en: dict = {t: [] for t in TOPICS}
    already_classified = set()
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            existing = json.load(f)
        for topic_en, data in existing.items():
            if topic_en in groups_en:
                groups_en[topic_en] = data.get("words", [])
                already_classified.update(data.get("words", []))
        print(f"Resuming: {len(already_classified)} words already classified.")

    remaining = [w for w in words if w["word"] not in already_classified]
    print(f"Classifying {len(remaining)} remaining words in batches of {BATCH_SIZE}...")
    batches = [remaining[i:i + BATCH_SIZE] for i in range(0, len(remaining), BATCH_SIZE)]

    for i, batch in enumerate(batches):
        print(f"  Batch {i + 1}/{len(batches)}...", end=" ", flush=True)
        try:
            classified = classify_batch(client, batch)
            for word_text, topic in classified.items():
                if topic in groups_en:
                    groups_en[topic].append(word_text)
                else:
                    groups_en[TOPICS[0]].append(word_text)
            print(f"OK ({len(classified)} classified)")
        except Exception as e:
            print(f"FAILED: {e}")
        time.sleep(0.5)

    # Build output: both EN and TR group names
    output = {}
    for topic_en, word_list in groups_en.items():
        if word_list:
            topic_tr = TOPIC_TR.get(topic_en, topic_en)
            output[topic_en] = {
                "label_en": topic_en,
                "label_tr": topic_tr,
                "words": sorted(set(word_list)),
            }

    out_path = DATA_DIR / "word_topics.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = sum(len(v["words"]) for v in output.values())
    print(f"\nDone! {total} words classified into {len(output)} topics.")
    print(f"Saved to {out_path}")
    for topic_en, data in output.items():
        print(f"  {topic_en}: {len(data['words'])} words")


if __name__ == "__main__":
    main()
