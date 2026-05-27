import json
import streamlit as st
from pathlib import Path

SCENARIOS_FILE = Path(__file__).parent.parent / "data" / "scenarios.json"


@st.cache_data
def load_scenarios() -> list:
    if not SCENARIOS_FILE.exists():
        return []
    try:
        with open(SCENARIOS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def get_scenario_by_id(scenario_id: str) -> dict | None:
    for s in load_scenarios():
        if s["id"] == scenario_id:
            return s
    return None


def get_categories() -> list:
    """Return unique categories with their scenarios, preserving order."""
    seen: dict = {}
    for s in load_scenarios():
        cat = s["category"]
        if cat not in seen:
            seen[cat] = {
                "id": cat,
                "name": cat,
                "name_tr": s.get("category_tr", cat),
                "scenarios": [],
            }
        seen[cat]["scenarios"].append(s)
    return list(seen.values())
