import streamlit as st


def analyze_weak_patterns(words: list, custom_words: list) -> dict:
    p = st.session_state.progress
    all_words = words + custom_words

    analysis = {
        "by_type": {
            "Verb":    {"hard": 0, "ok": 0, "easy": 0},
            "Nomen":   {"hard": 0, "ok": 0, "easy": 0},
            "Adj/Adv": {"hard": 0, "ok": 0, "easy": 0},
        },
        "by_length": {
            "short":  {"hard": 0, "total": 0},
            "medium": {"hard": 0, "total": 0},
            "long":   {"hard": 0, "total": 0},
        },
        "recommended_focus": "",
    }

    for w in all_words:
        word_text = w.get("word", "")
        prog = p.get(word_text, {})
        if not prog:
            continue
        status = prog.get("status", "ok")
        wtype = w.get("type", "")
        wlen = len(word_text)

        if wtype in analysis["by_type"]:
            analysis["by_type"][wtype][status] = analysis["by_type"][wtype].get(status, 0) + 1

        bucket = "short" if wlen <= 5 else ("medium" if wlen <= 9 else "long")
        analysis["by_length"][bucket]["total"] += 1
        if status == "hard":
            analysis["by_length"][bucket]["hard"] += 1

    max_ratio = 0.0
    for wtype, counts in analysis["by_type"].items():
        total = sum(counts.values())
        if total > 0:
            ratio = counts.get("hard", 0) / total
            if ratio > max_ratio:
                max_ratio = ratio
                analysis["recommended_focus"] = wtype

    return analysis
