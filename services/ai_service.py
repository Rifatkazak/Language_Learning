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

    def trial_days_remaining(self) -> int:
        """Days left in trial. 99 = unlimited (admin). 0 = last day. Negative = expired."""
        import datetime
        user = st.session_state.get("current_user", "")
        if user == "rifat":
            return 99
        ai_cache = st.session_state.get("ai_cache", {})
        trial_start = ai_cache.get("__trial_start__")
        if not trial_start:
            return 99  # Will be set on next login
        try:
            start = datetime.date.fromisoformat(str(trial_start))
            days_used = (datetime.date.today() - start).days
            return 2 - days_used  # 3-day trial: days 0, 1, 2 are valid
        except (ValueError, TypeError):
            return 99

    def can_generate(self) -> bool:
        """True if API key available AND (subscription active OR trial still running)."""
        if not self.is_available():
            return False
        user = st.session_state.get("current_user", "")
        if user == "rifat":
            return True
        ai_cache = st.session_state.get("ai_cache", {})
        if ai_cache.get("__subscription_active__"):
            return True
        return self.trial_days_remaining() >= 0

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

    def auto_classify_words(self, words_batch: list, topics: list) -> dict:
        """Classify a batch of words into topics. Returns {word: topic} dict."""
        if not self.is_available():
            return {}
        lines = "\n".join(
            f"{w['word']} ({w.get('translation_en') or w.get('translation', '')})"
            for w in words_batch
        )
        topics_str = " | ".join(topics)
        prompt = (
            f"Classify each German word into exactly one of these topics: {topics_str}\n\n"
            f"Words:\n{lines}\n\n"
            "Reply with one line per word, exactly:\n"
            "WORD: [German word] | TOPIC: [topic]\n"
            "Use the exact topic names listed. If none fit, write: Other"
        )
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
            )
            result = {}
            for line in response.choices[0].message.content.strip().split("\n"):
                if "WORD:" in line and "| TOPIC:" in line:
                    parts = line.split("| TOPIC:")
                    word = parts[0].replace("WORD:", "").strip()
                    topic = parts[1].strip() if len(parts) > 1 else "Other"
                    if word:
                        result[word] = topic
            return result
        except Exception:
            return {}

    def generate_grammar_quiz(self, topic_id: str, topic_de: str, user_words: list, quiz_type: str = "mc") -> list | None:
        if not self.is_available():
            return None
        lang = self._ui_lang()
        sample_words = [
            f"{w.get('article','')} {w['word']} ({w.get('translation','')})".strip()
            for w in user_words[:10]
        ]
        words_str = ", ".join(sample_words)

        is_mixed = topic_id == "__mixed__"
        if quiz_type == "mc":
            if lang == "en":
                topic_line = (
                    f"Create 5 multiple-choice grammar questions, one for each of these different topics: {topic_de}"
                    if is_mixed else
                    f"Create 5 multiple-choice grammar questions about: {topic_de}"
                )
                prompt = (
                    f"{topic_line}\n"
                    f"Use these vocabulary words where possible: {words_str}\n\n"
                    "Format EXACTLY like this for each question:\n"
                    "Q: [question or sentence with ___]\n"
                    "A: [correct answer]\n"
                    "W1: [wrong option 1]\n"
                    "W2: [wrong option 2]\n"
                    "W3: [wrong option 3]\n"
                    "E: [brief explanation, 1 sentence]\n"
                    "---"
                )
                system = "You are a German grammar quiz creator. Output only the specified format."
            else:
                topic_line = (
                    f"Şu farklı konulardan her biri için 1 tane olmak üzere toplamda 5 çoktan seçmeli soru oluştur: {topic_de}"
                    if is_mixed else
                    f"Şu konu için 5 çoktan seçmeli gramer sorusu oluştur: {topic_de}"
                )
                prompt = (
                    f"{topic_line}\n"
                    f"Mümkünse şu kelimeleri kullan: {words_str}\n\n"
                    "Her soru için AYNEN şu formatı kullan:\n"
                    "Q: [soru veya ___ boşluklu cümle]\n"
                    "A: [doğru cevap]\n"
                    "W1: [yanlış seçenek 1]\n"
                    "W2: [yanlış seçenek 2]\n"
                    "W3: [yanlış seçenek 3]\n"
                    "E: [Türkçe kısa açıklama, 1 cümle]\n"
                    "---"
                )
                system = "Sen bir Almanca gramer quiz hazırlayıcısısın. Sadece belirtilen formatı kullan."
        else:
            if lang == "en":
                topic_line = (
                    f"Create 5 fill-in-the-blank exercises, one for each of these different topics: {topic_de}"
                    if is_mixed else
                    f"Create 5 fill-in-the-blank exercises about: {topic_de}"
                )
                prompt = (
                    f"{topic_line}\n"
                    f"Use these vocabulary words where possible: {words_str}\n\n"
                    "Format EXACTLY like this for each exercise:\n"
                    "Q: [German sentence with ___ for the missing part]\n"
                    "A: [complete correct sentence]\n"
                    "E: [brief explanation, 1 sentence]\n"
                    "---"
                )
                system = "You are a German grammar exercise creator. Output only the specified format."
            else:
                topic_line = (
                    f"Şu farklı konulardan her biri için 1 tane olmak üzere toplamda 5 boşluk doldurma alıştırması oluştur: {topic_de}"
                    if is_mixed else
                    f"Şu konu için 5 boşluk doldurma alıştırması oluştur: {topic_de}"
                )
                prompt = (
                    f"{topic_line}\n"
                    f"Mümkünse şu kelimeleri kullan: {words_str}\n\n"
                    "Her alıştırma için AYNEN şu formatı kullan:\n"
                    "Q: [___ boşluklu Almanca cümle]\n"
                    "A: [tam doğru cümle]\n"
                    "E: [Türkçe kısa açıklama, 1 cümle]\n"
                    "---"
                )
                system = "Sen bir Almanca gramer alıştırması hazırlayıcısısın. Sadece belirtilen formatı kullan."

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=1400,
            )
            text = response.choices[0].message.content
            questions = []
            for block in text.split("---"):
                block = block.strip()
                if not block:
                    continue
                q: dict = {}
                for line in block.split("\n"):
                    line = line.strip()
                    if line.startswith("Q:"):    q["question"]    = line[2:].strip()
                    elif line.startswith("A:"): q["answer"]      = line[2:].strip()
                    elif line.startswith("W1:"): q["w1"]         = line[3:].strip()
                    elif line.startswith("W2:"): q["w2"]         = line[3:].strip()
                    elif line.startswith("W3:"): q["w3"]         = line[3:].strip()
                    elif line.startswith("E:"): q["explanation"] = line[2:].strip()
                if "question" in q and "answer" in q:
                    q.setdefault("explanation", "")
                    if quiz_type == "mc":
                        wrong = [q.get("w1",""), q.get("w2",""), q.get("w3","")]
                        wrong = [w for w in wrong if w]
                        opts = wrong[:3] + [q["answer"]]
                        random.shuffle(opts)
                        q["options"] = opts
                    questions.append(q)
            return questions if questions else None
        except Exception:
            return None

    def generate_writing_exercises(self, topic_id: str, topic_de: str, user_words: list) -> list | None:
        if not self.is_available():
            return None
        lang = self._ui_lang()
        is_mixed = topic_id == "__mixed__"
        sample_words = [
            f"{w.get('article','')} {w['word']} ({w.get('translation','')})".strip()
            for w in user_words[:8]
        ]
        words_str = ", ".join(sample_words)
        if lang == "en":
            topic_line = (
                f"covering these different grammar topics: {topic_de}"
                if is_mixed else
                f"specifically requiring the grammar topic: {topic_de}"
            )
            prompt = (
                f"Create 3 English sentences for a German B1 learner to translate, {topic_line}.\n"
                f"Use these vocabulary words in the sentences if possible: {words_str}\n\n"
                "Format EXACTLY like this for each sentence:\n"
                "SOURCE: [English sentence]\n"
                "HINT: [1 short phrase: what grammar structure to use]\n"
                "---"
            )
            system = "You are a German B1 writing exercise creator. Output only the specified format."
        else:
            topic_line = (
                f"şu farklı gramer konularını kapsayan (her cümle farklı bir konu): {topic_de}"
                if is_mixed else
                f"özellikle şu gramer yapısını gerektiren: {topic_de}"
            )
            prompt = (
                f"B1 seviyesi için Almancaya çevrilecek 3 Türkçe cümle oluştur, {topic_line}.\n"
                f"Mümkünse şu kelimeleri kullan: {words_str}\n\n"
                "Her cümle için AYNEN şu formatı kullan:\n"
                "SOURCE: [Türkçe cümle]\n"
                "HINT: [kullanılacak gramer yapısı, kısa]\n"
                "---"
            )
            system = "Sen bir Almanca B1 yazma alıştırması hazırlayıcısısın. Sadece belirtilen formatı kullan."
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=600,
            )
            exercises = []
            for block in response.choices[0].message.content.split("---"):
                block = block.strip()
                if not block:
                    continue
                ex: dict = {}
                for line in block.split("\n"):
                    line = line.strip()
                    if line.startswith("SOURCE:"):
                        ex["source"] = line[7:].strip()
                    elif line.startswith("HINT:"):
                        ex["hint"] = line[5:].strip()
                if "source" in ex:
                    ex.setdefault("hint", "")
                    exercises.append(ex)
            return exercises if exercises else None
        except Exception:
            return None

    def check_writing_answer(self, source: str, user_answer: str, topic_de: str) -> dict | None:
        if not self.is_available():
            return None
        lang = self._ui_lang()
        if lang == "en":
            prompt = (
                f"Evaluate this German translation.\n\n"
                f"Original sentence: {source}\n"
                f"Grammar focus: {topic_de}\n"
                f"Student's answer: {user_answer}\n\n"
                "Reply in EXACTLY this format:\n"
                "SCORE: [1-5 where 5=perfect, 4=minor error, 3=partially correct, 2=major error, 1=wrong]\n"
                "CORRECTION: [corrected German sentence, or write 'Correct!' if score is 5]\n"
                "EXPLANATION: [1 sentence: explain the main error or confirm what was good]\n"
                "Write nothing else."
            )
            system = "You are a strict but encouraging German grammar teacher. Use only the given format."
        else:
            prompt = (
                f"Bu Almanca çeviriyi değerlendir.\n\n"
                f"Kaynak cümle: {source}\n"
                f"Gramer konusu: {topic_de}\n"
                f"Öğrencinin cevabı: {user_answer}\n\n"
                "AYNEN şu formatta yanıt ver:\n"
                "SCORE: [1-5, 5=mükemmel, 4=küçük hata, 3=kısmen doğru, 2=büyük hata, 1=yanlış]\n"
                "CORRECTION: [düzeltilmiş Almanca cümle, veya '✓ Doğru!' puan 5 ise]\n"
                "EXPLANATION: [ana hatayı veya doğru yapıyı açıklayan 1 Türkçe cümle]\n"
                "Başka hiçbir şey yazma."
            )
            system = "Sen titiz ama motive edici bir Almanca gramer öğretmenisin. Yalnızca verilen formatı kullan."
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=200,
            )
            text = response.choices[0].message.content.strip()
            result: dict = {}
            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("SCORE:"):
                    try:
                        result["score"] = max(1, min(5, int(line[6:].strip()[0])))
                    except (ValueError, IndexError):
                        result["score"] = 3
                elif line.startswith("CORRECTION:"):
                    result["correction"] = line[11:].strip()
                elif line.startswith("EXPLANATION:"):
                    result["explanation"] = line[12:].strip()
            if "score" in result:
                result.setdefault("correction", "")
                result.setdefault("explanation", "")
                return result
        except Exception:
            pass
        return None

    def generate_grammar_lesson(self, topic_id: str, topic_de: str, user_words: list) -> str | None:
        if not self.is_available():
            return None
        sample_words = []
        for w in user_words[:12]:
            art = w.get("article", "")
            entry = f"{art} {w['word']} ({w.get('translation', '')})".strip()
            sample_words.append(entry)
        words_str = ", ".join(sample_words)
        if self._ui_lang() == "en":
            prompt = (
                f"Create a B1-level German grammar lesson for: **{topic_de}**\n\n"
                f"Use these words from the learner's vocabulary in your examples: {words_str}\n\n"
                "Write the lesson with exactly these 5 sections:\n\n"
                "### 📌 RULE\n[2-3 clear sentences explaining the rule in English]\n\n"
                "### 🏗️ STRUCTURE\n[Simple formula or table showing the grammatical structure]\n\n"
                "### 📝 EXAMPLES\n[3 example sentences using words from the vocabulary above, each with English translation]\n\n"
                "### ⚠️ WATCH OUT\n[The most common mistake learners make - 1-2 sentences]\n\n"
                "### 💡 MEMORY AID\n[One memorable tip or mnemonic]\n\n"
                "Keep it concise and practical for B1 level."
            )
            system = "You are an expert German grammar teacher. Write clear, concise lessons for B1 learners."
        else:
            prompt = (
                f"B1 seviyesi için **{topic_de}** konusunda Almanca gramer dersi oluştur.\n\n"
                f"Örneklerinde şu kelimeleri kullan: {words_str}\n\n"
                "Dersi tam olarak şu 5 bölümle yaz:\n\n"
                "### 📌 KURAL\n[Kuralı 2-3 net cümleyle Türkçe açıkla]\n\n"
                "### 🏗️ YAPI\n[Dilbilgisel yapıyı gösteren basit formül veya tablo]\n\n"
                "### 📝 ÖRNEKLER\n[Yukarıdaki kelimelerden kullanarak 3 örnek cümle, her birinin Türkçe çevirisiyle]\n\n"
                "### ⚠️ DİKKAT\n[Bu konuda öğrencilerin en sık yaptığı hata - 1-2 cümle]\n\n"
                "### 💡 HATIRLATICI\n[Kuralı hatırlamak için 1 pratik ipucu]\n\n"
                "B1 seviyesine uygun, kısa ve pratik tut."
            )
            system = "Sen bir Almanca dilbilgisi uzmanısın. B1 öğrencileri için net ve özlü dersler yazıyorsun."
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=800,
            )
            return response.choices[0].message.content
        except Exception:
            return None

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

    @staticmethod
    def text_to_speech_bytes(text: str, lang: str = "de") -> bytes | None:
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=lang, slow=False)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            return buf.read()
        except Exception:
            return None


def get_ai_service() -> AIService:
    # Session-state cache: cleared on every app restart/deployment,
    # so new methods are always available after a redeploy.
    if "_ai_service" not in st.session_state:
        st.session_state["_ai_service"] = AIService()
    return st.session_state["_ai_service"]
