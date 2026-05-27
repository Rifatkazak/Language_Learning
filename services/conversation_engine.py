from services.ai_service import get_ai_service


_SYSTEM_TEMPLATE = """\
You are playing the role of {ai_role} in a German language learning roleplay.

SCENARIO:
{context}

Your role: {ai_role}
Learner's role: {user_role}
Target level: {cefr_level} — keep your German simple and clear for a B1 learner.

IN-CHARACTER RULES:
- Stay fully in character. Respond naturally as {ai_role}.
- Use simple, clear German: short sentences, common vocabulary.
- Keep your in-character reply SHORT: 2-4 sentences maximum.
- Be patient, friendly and realistic.

AFTER your in-character reply, write ---FEEDBACK--- on a new line, then:
CORRECTION: [Copy the user's last sentence with mistakes corrected. If it was correct, write exactly: OK]
EXPLANATION: [One sentence in Turkish explaining the main correction. If correct, write: Harika! 👏]
VOCAB: [1-3 useful words from this exchange, formatted as: word=translation separated by | — or leave empty if none]
---END---

Example of full output:
Natürlich! Haben Sie Fieber oder nur Kopfschmerzen?
---FEEDBACK---
CORRECTION: Ich habe Kopfschmerzen und Halsschmerzen.
EXPLANATION: Almancada isimler büyük harfle başlar: "Kopfschmerzen", "Halsschmerzen".
VOCAB: die Kopfschmerzen=headache|der Halsschmerz=sore throat
---END---
"""

_XP_PER_MESSAGE = 10
_XP_BONUS_CORRECT = 5
_XP_PER_VOCAB_ITEM = 2


class ConversationEngine:
    def __init__(self, scenario: dict):
        self.scenario = scenario
        self.ai = get_ai_service()

    def get_opening_message(self) -> dict:
        return {
            "role": "assistant",
            "content": self.scenario.get("opening", "Guten Tag! Wie kann ich Ihnen helfen?"),
            "feedback": None,
        }

    def send_message(self, user_message: str, history: list) -> dict:
        """
        Sends user_message with conversation history to the AI.
        Returns parsed result: reply, correction, explanation, vocab, xp, is_correct.
        """
        if not self.ai.is_available():
            return _fallback_response()

        messages = self._build_api_messages(user_message, history)
        try:
            response = self.ai.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.75,
                max_tokens=600,
            )
            raw = response.choices[0].message.content
            return _parse_and_score(raw)
        except Exception:
            return _fallback_response()

    def _build_api_messages(self, user_message: str, history: list) -> list:
        s = self.scenario
        system = _SYSTEM_TEMPLATE.format(
            ai_role=s.get("ai_role", "German speaker"),
            context=s.get("context", ""),
            user_role=s.get("user_role", "Learner"),
            cefr_level=s.get("cefr_level", "B1"),
        )
        msgs = [{"role": "system", "content": system}]
        for msg in history:
            if msg.get("role") in ("user", "assistant"):
                msgs.append({"role": msg["role"], "content": msg["content"]})
        msgs.append({"role": "user", "content": user_message})
        return msgs


def _parse_and_score(raw: str) -> dict:
    correction = "OK"
    explanation = "Harika! 👏"
    vocab: list = []
    reply = raw.strip()

    if "---FEEDBACK---" in raw:
        parts = raw.split("---FEEDBACK---", 1)
        reply = parts[0].strip()
        feedback_block = parts[1].replace("---END---", "").strip()

        for line in feedback_block.splitlines():
            line = line.strip()
            if line.startswith("CORRECTION:"):
                correction = line[len("CORRECTION:"):].strip()
            elif line.startswith("EXPLANATION:"):
                explanation = line[len("EXPLANATION:"):].strip()
            elif line.startswith("VOCAB:"):
                vocab_str = line[len("VOCAB:"):].strip()
                if vocab_str:
                    for item in vocab_str.split("|"):
                        if "=" in item:
                            word, tr = item.split("=", 1)
                            vocab.append({"word": word.strip(), "translation": tr.strip()})

    is_correct = correction.strip().upper() == "OK" or correction.strip() == ""
    xp = _XP_PER_MESSAGE
    if is_correct:
        xp += _XP_BONUS_CORRECT
    xp += len(vocab) * _XP_PER_VOCAB_ITEM

    return {
        "reply": reply,
        "correction": None if is_correct else correction,
        "explanation": explanation,
        "vocab": vocab,
        "xp": xp,
        "is_correct": is_correct,
    }


def _fallback_response() -> dict:
    return {
        "reply": (
            "Entschuldigung, ich habe das nicht ganz verstanden. "
            "Können Sie das bitte noch einmal sagen?"
        ),
        "correction": None,
        "explanation": "",
        "vocab": [],
        "xp": _XP_PER_MESSAGE,
        "is_correct": True,
    }
