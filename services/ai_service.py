import json
import os
import random
import io
import base64
import streamlit as st
from openai import OpenAI


class AIService:
    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self) -> bool:
        api_key = None
        try:
            if hasattr(st, "secrets") and "DEEPSEEK_API_KEY" in st.secrets:
                api_key = st.secrets["DEEPSEEK_API_KEY"]
        except Exception:
            pass
        if not api_key:
            api_key = os.getenv("DEEPSEEK_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
            return True
        return False

    def is_available(self) -> bool:
        return self.client is not None

    def _ui_lang(self) -> str:
        return st.session_state.get("ui_lang", "tr")

    def generate_example_sentences(self, word: str, translation: str, level: str = "B1") -> str | None:
        if not self.is_available():
            return self._fallback_sentences(word, translation)
        if self._ui_lang() == "en":
            prompt = (
                f"Word: {word}\nMeaning: {translation}\nLevel: {level}\n\n"
                "Write 2 short, everyday example sentences for this German word.\n"
                "Add the English translation below each sentence.\n\n"
                "Format:\n1. [German sentence]\n   → [English translation]\n2. [German sentence]\n   → [English translation]"
            )
            system = "You are a German language teacher helping B1 level students."
        else:
            prompt = (
                f"Kelime: {word}\nAnlamı: {translation}\nSeviye: {level}\n\n"
                "Bu Almanca kelime için 2 tane kısa, günlük hayatta kullanılan örnek cümle yaz.\n"
                "Her cümlenin altına Türkçe çevirisini ekle.\n\n"
                "Format:\n1. [Almanca cümle]\n   → [Türkçe çeviri]\n2. [Almanca cümle]\n   → [Türkçe çeviri]"
            )
            system = "Sen bir Almanca öğretmenisin. Öğrencilerine B1 seviyesinde yardımcı oluyorsun."
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=300,
            )
            return response.choices[0].message.content
        except Exception:
            return self._fallback_sentences(word, translation)

    def _fallback_sentences(self, word: str, translation: str) -> str:
        if self._ui_lang() == "en":
            templates = [
                f"1. Ich möchte {word} lernen.\n   → I want to learn {translation}.",
                f"2. Kannst du mir helfen, {word} zu verstehen?\n   → Can you help me understand {translation}?",
                f"3. {word.capitalize()} ist sehr wichtig für den Alltag.\n   → {translation.capitalize()} is very important for daily life.",
                f"4. Wir sollten mehr {word} üben.\n   → We should practice {translation} more.",
                f"5. Hast du das Wort '{word}' schon gehört?\n   → Have you heard the word '{translation}' before?",
            ]
        else:
            templates = [
                f"1. Ich möchte {word} lernen.\n   → {translation} öğrenmek istiyorum.",
                f"2. Kannst du mir helfen, {word} zu verstehen?\n   → {translation} anlamama yardım eder misin?",
                f"3. {word.capitalize()} ist sehr wichtig für den Alltag.\n   → {translation} günlük hayat için çok önemli.",
                f"4. Wir sollten mehr {word} üben.\n   → Daha fazla {translation} pratiği yapmalıyız.",
                f"5. Hast du das Wort '{word}' schon gehört?\n   → '{translation}' kelimesini daha önce duydun mu?",
            ]
        return "\n\n".join(random.sample(templates, 2))

    def generate_challenge_story(self, target_words_list: list, get_translation_fn) -> str:
        words_data = [
            {"word": w["word"], "article": w.get("article", ""), "translation": get_translation_fn(w["word"])}
            for w in target_words_list[:15]
        ]
        word_list = "\n".join(f"- {w['article']} {w['word']} ({w['translation']})".strip() for w in words_data)
        if self._ui_lang() == "en":
            prompt = (
                f"Write a short, engaging story using this week's German words:\n\n"
                f"WORDS:\n{word_list}\n\n"
                "RULES:\n"
                "- 3-4 paragraphs, B1 level, everyday topic\n"
                "- Use the words naturally\n"
                "- Add the English translation in italics below each German paragraph\n"
                "- Write only the story, no title or explanation"
            )
            system = "You are a German story writer. You write natural stories for B1 level learners."
        else:
            prompt = (
                f"Bu haftanin Almanca kelimelerini kullanarak kisa, ilgi cekici bir hikaye yaz:\n\n"
                f"KELIMELER:\n{word_list}\n\n"
                "KURALLAR:\n"
                "- 3-4 paragraf, B1 seviyesi, gundelik hayattan bir konu\n"
                "- Kelimeleri dogal bir sekilde kullan\n"
                "- Her Almanca paragrafin hemen altina Turkce cevirisini italik yaz\n"
                "- Sadece hikayeyi yaz, baslik veya aciklama ekleme"
            )
            system = "Sen bir Almanca hikaye yazarisin. B1 seviyesinde ogrendiler icin dogal hikayeler yazarsin."
        if self.is_available():
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.8,
                    max_tokens=1200,
                )
                return response.choices[0].message.content
            except Exception:
                pass
        return f"Es war einmal ein Mensch, der {words_data[0]['word'] if words_data else 'Deutsch'} lernen wollte..."

    def chat_with_challenge_words(self, messages: list, target_words: list) -> str | None:
        if not self.is_available():
            return None
        word_list = ", ".join(target_words[:15])
        if self._ui_lang() == "en":
            system_prompt = (
                f"You are a German teacher. Help the student reinforce this week's words through conversation practice.\n"
                f"This week's words: {word_list}\n\n"
                "RULES:\n"
                "- Naturally use one or more of the words in each response\n"
                "- Write in German first, then give the English translation on the next line (with ->)\n"
                "- Gently correct the student's mistakes\n"
                "- Keep responses short (2-3 German sentences)\n"
                "- Introduce yourself and open a topic in the first message"
            )
        else:
            system_prompt = (
                f"Sen bir Almanca ogretmenisin. Ogrencinin bu haftaki kelimeleri konusma pratigiyle pekistirmesine yardim et.\n"
                f"Bu haftanin kelimeleri: {word_list}\n\n"
                "KURALLAR:\n"
                "- Her yanitinda bu kelimelerden birini veya birkacini dogal olarak kullan\n"
                "- Once Almanca yaz, sonra Turkce cevirisini yeni satirda ver (-> ile)\n"
                "- Ogrencinin hatalarini nazikce duzelt\n"
                "- Yaniti kisa tut (2-3 Almanca cumle)\n"
                "- Ilk mesajda kendini tanit ve konuyu ac"
            )
        api_messages = [{"role": "system", "content": system_prompt}] + messages[-12:]
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=api_messages,
                temperature=0.7,
                max_tokens=300,
            )
            return response.choices[0].message.content
        except Exception:
            return None

    def generate_word_family(self, word: str, translation: str) -> list:
        """Returns [{word, meaning}, ...] — words sharing the same root/compound."""
        if not self.is_available():
            return []
        if self._ui_lang() == "en":
            prompt = (
                f"List the word family (Wortfamilie) of the German word '{word}' ({translation}).\n"
                "Give 4-6 words derived from the same root or forming compounds with it.\n"
                "Use exactly this format for each line:\n"
                "WORD: [German word] | MEANING: [English meaning]\n"
                "Write nothing else."
            )
        else:
            prompt = (
                f"Almanca '{word}' ({translation}) kelimesinin kelime ailesini (Wortfamilie) listele.\n"
                "Aynı kökten türeyen veya bu kelimeyle bileşik oluşturan 4-6 kelime ver.\n"
                "Her satira tam olarak su formati kullan:\n"
                "WORD: [Almanca kelime] | MEANING: [Turkce anlam]\n"
                "Baska hicbir sey yazma."
            )
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=200,
            )
            result = []
            for line in response.choices[0].message.content.strip().split("\n"):
                line = line.strip()
                if line.startswith("WORD:") and "| MEANING:" in line:
                    parts = line.split("| MEANING:")
                    w = parts[0].replace("WORD:", "").strip()
                    m = parts[1].strip() if len(parts) > 1 else ""
                    if w:
                        result.append({"word": w, "meaning": m})
            return result
        except Exception:
            return []

    def generate_case_sentence(self, word: str, article: str, translation: str, case: str) -> dict | None:
        if not self.is_available():
            return None
        case_hints = {
            "Nominativ": "Subjekt (wer/was)",
            "Akkusativ": "direktes Objekt (wen/was)",
            "Dativ":     "indirektes Objekt (wem)",
        }
        hint = case_hints.get(case, case)
        if self._ui_lang() == "en":
            prompt = (
                f"German word: {article} {word} ({translation})\n"
                f"Write a short B1-level sentence using this word in the '{case}' case ({hint}).\n\n"
                "Reply in exactly this format:\n"
                "SENTENCE: [German sentence]\n"
                "TRANSLATION: [English translation]\n"
                "EXPLANATION: [Why this case? 1 sentence in English]\n"
                "Write nothing else."
            )
            system = "You are a German grammar teacher. Use only the given format."
        else:
            prompt = (
                f"Almanca kelime: {article} {word} ({translation})\n"
                f"Bu kelimeyi '{case}' halinde ({hint}) kullanan B1 seviyesinde kısa bir cümle yaz.\n\n"
                "Yanıtı kesinlikle bu formatta ver:\n"
                "SENTENCE: [Almanca cümle]\n"
                "TRANSLATION: [Türkçe çeviri]\n"
                "EXPLANATION: [Neden bu kasus? Türkçe 1 cümle]\n"
                "Başka hiçbir şey yazma."
            )
            system = "Sen bir Almanca dilbilgisi öğretmenisin. Yalnızca verilen formatı kullan."
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=250,
            )
            text = response.choices[0].message.content.strip()
            result = {}
            for line in text.split("\n"):
                if line.startswith("SENTENCE:"):
                    result["sentence"] = line[9:].strip()
                elif line.startswith("TRANSLATION:"):
                    result["translation"] = line[12:].strip()
                elif line.startswith("EXPLANATION:"):
                    result["explanation"] = line[12:].strip()
            if "sentence" in result and "translation" in result:
                result.setdefault("explanation", "")
                return result
        except Exception:
            pass
        return None

    def analyze_weak_words(self, weak_words: list, user_stats: dict) -> str:
        if self._ui_lang() == "en":
            fallback_empty = "Keep studying! You're making progress every day. 💪"
            fallback_error = "Keep reviewing the words you find difficult! You've got this! 🎯"
        else:
            fallback_empty = "Çalışmaya devam et! Her gün biraz daha ilerliyorsun. 💪"
            fallback_error = "Zorlandığın kelimeleri düzenli tekrar etmeye devam et! Başaracaksın! 🎯"
        if not self.is_available() or not weak_words:
            return fallback_empty
        if self._ui_lang() == "en":
            prompt = (
                f"The user is struggling with these German words: {', '.join(weak_words[:10])}\n"
                f"Daily streak: {user_stats.get('streak', 0)} days\n\n"
                "Analyze these words and tell the user:\n"
                "1. What patterns they're struggling with\n2. How they should study\n3. A motivating suggestion\n"
                "Write in a short, friendly tone (2-3 sentences)."
            )
        else:
            prompt = (
                f"Kullanıcı şu Almanca kelimelerde zorlanıyor: {', '.join(weak_words[:10])}\n"
                f"Günlük serisi: {user_stats.get('streak', 0)} gün\n\n"
                "Bu kelimeleri analiz et ve kullanıcıya:\n"
                "1. Hangi kalıplarda zorlandığını\n2. Nasıl çalışması gerektiğini\n3. Motive edici bir öneri\n"
                "Kısa ve samimi bir dille yaz (2-3 cümle)."
            )
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=200,
            )
            return response.choices[0].message.content
        except Exception:
            return fallback_error

    def create_challenge_dialog(self, target_words_list: list, get_translation_fn) -> str:
        words_to_use = target_words_list[:10]
        words_data = [
            {
                "word": w["word"],
                "translation": get_translation_fn(w["word"]),
                "article": w.get("article", ""),
                "type": w.get("type", ""),
            }
            for w in words_to_use
        ]
        word_list = "\n".join(
            [f"- {w['article']} {w['word']} ({w['translation']})" for w in words_data]
        )
        if self._ui_lang() == "en":
            prompt = (
                f"Create a short, natural dialogue using the following German words.\n\n"
                f"WORDS:\n{word_list}\n\n"
                "RULES:\n- Dialogue should be 6-10 lines\n- Different character speaks each line\n"
                "- Add the English translation directly below each German sentence\n"
                "- Try to use all the given words\n\n"
                "FORMAT:\nAli: [German sentence]\n🇬🇧 [English translation]\n\n"
                "Write only the dialogue, no extra explanation."
            )
            system = "You are a German teacher. You prepare natural dialogues for B1 level students."
        else:
            prompt = (
                f"Aşağıdaki Almanca kelimeleri kullanarak kısa ve doğal bir diyalog oluştur.\n\n"
                f"KELİMELER:\n{word_list}\n\n"
                "KURALLAR:\n- Diyalog 6-10 satır olsun\n- Her satırda farklı bir karakter konuşsun\n"
                "- Her Almanca cümlenin hemen altında Türkçe çevirisi olsun\n"
                "- Verilen kelimelerin hepsini kullanmaya çalış\n\n"
                "FORMAT:\nAli: [Almanca cümle]\n🇹🇷 [Türkçe çeviri]\n\n"
                "Lütfen sadece diyaloğu yaz, başka açıklama ekleme."
            )
            system = "Sen bir Almanca öğretmenisin. B1 seviyesinde öğrenciler için doğal diyaloglar hazırlıyorsun."
        if self.is_available():
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.8,
                    max_tokens=800,
                )
                return response.choices[0].message.content
            except Exception:
                pass
        return self._fallback_dialog(words_data)

    def _fallback_dialog(self, words_data: list) -> str:
        if self._ui_lang() == "en":
            def w(i):
                return words_data[i] if i < len(words_data) else {"word": "lernen", "translation": "to learn"}
            d = (
                f"Ali: Hallo! Ich möchte {w(0)['word']} lernen.\n"
                f"🇬🇧 Hello! I want to learn {w(0)['translation']}.\n\n"
                f"Ayşe: Das ist super! Kannst du schon {w(1)['word']}?\n"
                f"🇬🇧 That's great! Do you already know {w(1)['translation']}?\n\n"
            )
            if len(words_data) > 2:
                d += (
                    f"Ali: Ja, aber ich möchte besser {w(2)['word']} verstehen.\n"
                    f"🇬🇧 Yes, but I want to understand {w(2)['translation']} better.\n\n"
                )
            if len(words_data) > 3:
                d += (
                    f"Ayşe: Ich kann dir beim {w(3)['word']} helfen.\n"
                    f"🇬🇧 I can help you with {w(3)['translation']}.\n\n"
                )
            d += "Ali: Perfekt! Bis später!\n🇬🇧 Perfect! See you later!"
        else:
            def w(i):
                return words_data[i] if i < len(words_data) else {"word": "lernen", "translation": "öğrenmek"}
            d = (
                f"Ali: Hallo! Ich möchte {w(0)['word']} lernen.\n"
                f"🇹🇷 Merhaba! {w(0)['translation']} öğrenmek istiyorum.\n\n"
                f"Ayşe: Das ist super! Kannst du schon {w(1)['word']}?\n"
                f"🇹🇷 Bu harika! Zaten {w(1)['translation']} biliyor musun?\n\n"
            )
            if len(words_data) > 2:
                d += (
                    f"Ali: Ja, aber ich möchte besser {w(2)['word']} verstehen.\n"
                    f"🇹🇷 Evet, ama {w(2)['translation']} daha iyi anlamak istiyorum.\n\n"
                )
            if len(words_data) > 3:
                d += (
                    f"Ayşe: Ich kann dir beim {w(3)['word']} helfen.\n"
                    f"🇹🇷 Sana {w(3)['translation']} konusunda yardım edebilirim.\n\n"
                )
            d += "Ali: Perfekt! Bis später!\n🇹🇷 Mükemmel! Sonra görüşürüz!"
        return d

    def generate_sentence_with_blank(self, verb: str, meaning: str) -> str:
        if self.is_available():
            try:
                if self._ui_lang() == "en":
                    prompt = (
                        f"Create a simple sentence for the German verb '{verb}'.\n"
                        "Replace the verb with '___' in the sentence. At the end, give the English translation.\n\n"
                        f"Now write for '{verb}':"
                    )
                else:
                    prompt = (
                        f"Almanca '{verb}' fiili için basit bir cümle oluştur.\n"
                        "Cümlede fiilin yerinde '___' olsun. Cümlenin sonunda Türkçe çevirisini ver.\n\n"
                        f"Şimdi '{verb}' için yaz:"
                    )
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=150,
                )
                return response.choices[0].message.content
            except Exception:
                pass
        if self._ui_lang() == "en":
            return f"Ich möchte das ___ ({verb}).\nEnglish: I want to {meaning}."
        return f"Ich möchte das ___ ({verb}).\nTürkçe: {meaning} istiyorum."

    def translate_to_english(self, german_word: str, turkish_translation: str) -> str | None:
        if not self.is_available():
            return None
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": (
                    f"Translate the German word '{german_word}' to English. "
                    f"Turkish meaning for context: '{turkish_translation}'. "
                    "Reply with only the English translation, nothing else."
                )}],
                temperature=0.3,
                max_tokens=30,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return None

    @staticmethod
    def text_to_speech(text: str, lang: str = "de") -> str:
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=lang, slow=False)
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            audio_b64 = base64.b64encode(audio_bytes.read()).decode()
            return (
                f'<audio controls style="display:none" autoplay>'
                f'<source src="data:audio/mp3;base64,{audio_b64}" type="audio/mpeg"></audio>'
            )
        except Exception:
            return ""


def get_ai_service() -> AIService:
    # Session-state cache: cleared on every app restart/deployment,
    # so new methods are always available after a redeploy.
    if "_ai_service" not in st.session_state:
        st.session_state["_ai_service"] = AIService()
    return st.session_state["_ai_service"]
