import random
import datetime


def calculate_priority_score(word: dict, progress: dict) -> float:
    word_text = word.get("word", "")
    p = progress.get(word_text, {})
    if not p:
        return 0.0

    today = datetime.date.today()
    status = p.get("status", "unseen")
    streak = p.get("streak", 0)

    next_review_str = p.get("next_review", str(today))
    next_review = datetime.date.fromisoformat(next_review_str)
    days_overdue = (today - next_review).days

    status_weights = {"hard": -10, "ok": 0, "easy": 5}
    base_score = status_weights.get(status, 0)
    overdue_bonus = -days_overdue * 2 if days_overdue > 0 else 0
    streak_delay = streak * 1.5

    return base_score + overdue_bonus + streak_delay


def build_adaptive_deck(pool: list, progress: dict, size: int = 30) -> list:
    scored = [(w, calculate_priority_score(w, progress)) for w in pool]
    scored.sort(key=lambda x: x[1])

    critical_count = int(size * 0.7)
    random_count = size - critical_count

    critical = [w for w, _ in scored[:critical_count]]
    remaining = [w for w, _ in scored[critical_count:]]

    random_sample = random.sample(remaining, min(random_count, len(remaining)))
    deck = critical + random_sample
    random.shuffle(deck)
    return deck[:size]


def build_deck_from_composition(pool: list, comp: dict, deck_size: int) -> list:
    available = {
        "Verb": [w for w in pool if w.get("type") == "Verb" and w.get("translation") not in ("Çeviri yok", "—", None, "")],
        "Nomen": [w for w in pool if w.get("type") == "Nomen" and w.get("translation") not in ("Çeviri yok", "—", None, "")],
        "Adj/Adv": [w for w in pool if w.get("type") == "Adj/Adv" and w.get("translation") not in ("Çeviri yok", "—", None, "")],
    }
    deck = []
    for t in ("Verb", "Nomen", "Adj/Adv"):
        req = int(comp.get(t, 0)) if comp else 0
        if req <= 0:
            continue
        take = min(req, len(available[t]))
        if take:
            deck.extend(random.sample(available[t], take))

    translated_pool = [w for w in pool if w.get("translation") not in ("Çeviri yok", "—", None, "") and w not in deck]
    need = deck_size - len(deck)
    if need > 0:
        extra = random.sample(translated_pool, min(need, len(translated_pool)))
        deck.extend(extra)

    random.shuffle(deck)
    return deck[:deck_size]
