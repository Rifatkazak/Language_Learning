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

    def generate_example_sentences(self, word: str, translation: str, level: str = "B1") -> str | None:
        if not self.is_available():
            return self._fallback_sentences(word, translation)
        prompt = (
            f"Kelime: {word}\nAnlamı: {translation}\nSeviye: {level}\n\n"
            "Bu Almanca kelime için 2 tane kısa, günlük hayatta kullanılan örnek cümle yaz.\n"
            "Her cümlenin altına Türkçe çevirisini ekle.\n\n"
            "Format:\n1. [Almanca cümle]\n   → [Türkçe çeviri]\n2. [Almanca cümle]\n   → [Türkçe çeviri]"
        )
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Sen bir Almanca öğretmenisin. Öğrencilerine B1 seviyesinde yardımcı oluyorsun."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=300,
            )
            return response.choices[0].message.content
        except Exception:
            return self._fallback_sentences(word, translation)

    def _fallback_sentences(self, word: str, translation: str) -> str:
        templates = [
            f"1. Ich möchte {word} lernen.\n   → {translation} öğrenmek istiyorum.",
            f"2. Kannst du mir helfen, {word} zu verstehen?\n   → {translation} anlamama yardım eder misin?",
            f"3. {word.capitalize()} ist sehr wichtig für den Alltag.\n   → {translation} günlük hayat için çok önemli.",
            f"4. Wir sollten mehr {word} üben.\n   → Daha fazla {translation} pratiği yapmalıyız.",
            f"5. Hast du das Wort '{word}' schon gehört?\n   → '{translation}' kelimesini daha önce duydun mu?",
        ]
        return "\n\n".join(random.sample(templates, 2))

    def analyze_weak_words(self, weak_words: list, user_stats: dict) -> str:
        if not self.is_available() or not weak_words:
            return "Çalışmaya devam et! Her gün biraz daha ilerliyorsun. 💪"
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
            return "Zorlandığın kelimeleri düzenli tekrar etmeye devam et! Başaracaksın! 🎯"

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
        prompt = (
            f"Aşağıdaki Almanca kelimeleri kullanarak kısa ve doğal bir diyalog oluştur.\n\n"
            f"KELİMELER:\n{word_list}\n\n"
            "KURALLAR:\n- Diyalog 6-10 satır olsun\n- Her satırda farklı bir karakter konuşsun\n"
            "- Her Almanca cümlenin hemen altında Türkçe çevirisi olsun\n"
            "- Verilen kelimelerin hepsini kullanmaya çalış\n\n"
            "FORMAT:\nAli: [Almanca cümle]\n🇹🇷 [Türkçe çeviri]\n\n"
            "Lütfen sadece diyaloğu yaz, başka açıklama ekleme."
        )
        if self.is_available():
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "Sen bir Almanca öğretmenisin. B1 seviyesinde öğrenciler için doğal diyaloglar hazırlıyorsun."},
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
        return f"Ich möchte das ___ ({verb}).\nTürkçe: {meaning} istiyorum."

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


@st.cache_resource
def get_ai_service() -> AIService:
    return AIService()
