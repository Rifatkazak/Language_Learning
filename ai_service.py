# ai_service.py
import os
import streamlit as st
from openai import OpenAI

class DeepSeekService:
    def __init__(self):
        self.client = None
        self.init_client()
    
    def init_client(self):
        """OpenAI istemcisini başlat"""
        try:
            # Streamlit Cloud secrets veya environment variable
            api_key = None
            
            # Önce st.secrets dene (Streamlit Cloud)
            try:
                if hasattr(st, 'secrets') and 'DEEPSEEK_API_KEY' in st.secrets:
                    api_key = st.secrets["DEEPSEEK_API_KEY"]
            except:
                pass
            
            # Yoksa environment variable dene
            if not api_key:
                api_key = os.getenv("DEEPSEEK_API_KEY")
            
            if api_key:
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com/v1"
                )
                return True
            else:
                return False
        except Exception as e:
            print(f"AI init error: {e}")
            return False
    
    def is_available(self):
        return self.client is not None
    
    def generate_example_sentences(self, word: str, translation: str, level: str = "B1") -> str:
        if not self.is_available():
            return self._get_template_sentences(word, translation)
        
        prompt = f"""
        Kelime: {word}
        Anlamı: {translation}
        Seviye: {level}
        
        Bu Almanca kelime için 2 tane kısa, günlük hayatta kullanılan örnek cümle yaz.
        Her cümlenin altına Türkçe çevirisini ekle.
        
        Format:
        1. [Almanca cümle]
           → [Türkçe çeviri]
        2. [Almanca cümle]
           → [Türkçe çeviri]
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Sen bir Almanca öğretmenisin. Öğrencilerine B1 seviyesinde yardımcı oluyorsun."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI generate error: {e}")
            return self._get_template_sentences(word, translation)
    
    def _get_template_sentences(self, word: str, translation: str) -> str:
        """API yoksa template cümleler"""
        templates = [
            f"1. Ich möchte {word} lernen.\n   → {translation} öğrenmek istiyorum.",
            f"2. Kannst du mir helfen, {word} zu verstehen?\n   → {translation} anlamama yardım eder misin?",
            f"3. {word.capitalize()} ist sehr wichtig für den Alltag.\n   → {translation} günlük hayat için çok önemli.",
            f"4. Wir sollten mehr {word} üben.\n   → Daha fazla {translation} pratiği yapmalıyız.",
            f"5. Hast du das Wort '{word}' schon gehört?\n   → '{translation}' kelimesini daha önce duydun mu?",
        ]
        import random
        return "\n\n".join(random.sample(templates, 2))
    
    def analyze_weak_words(self, weak_words: list, user_stats: dict) -> str:
        if not self.is_available() or not weak_words:
            return "Çalışmaya devam et! Her gün biraz daha ilerliyorsun. 💪"
        
        prompt = f"""
        Kullanıcı şu Almanca kelimelerde zorlanıyor: {', '.join(weak_words[:10])}
        Günlük serisi: {user_stats.get('streak', 0)} gün
        
        Bu kelimeleri analiz et ve kullanıcıya:
        1. Hangi kalıplarda zorlandığını
        2. Nasıl çalışması gerektiğini
        3. Motive edici bir öneri
        
        Kısa ve samimi bir dille yaz (2-3 cümle).
        """
        
        try:
            response = self.client.chat.completions.create(
                model="DeepSeek-V4-Flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception:
            return "Zorlandığın kelimeleri düzenli tekrar etmeye devam et! Başaracaksın! 🎯"

    
    # ai_service.py'ye ekleyin veya app.py'nin başına

    # ── AI Diyalog Oluşturma Fonksiyonu ──────────────────────────────────────────────
    def create_challenge_dialog(self, target_words_list, get_translation):
        """Haftalık kelimelerle AI diyalog oluştur - KAYDEDİLİR VE TEKRAR KULLANILIR"""
        
        # Hedef kelimelerden ilk 8-10 tanesini al (diyalog çok uzun olmasın)
        words_to_use = target_words_list[:10]
        
        # Kelimeleri ve çevirilerini hazırla
        words_data = []
        for w in words_to_use:
            words_data.append({
                "word": w["word"],
                "translation": get_translation(w["word"]),
                "article": w.get("article", ""),
                "type": w.get("type", "")
            })
        
        # Prompt hazırla
        word_list = "\n".join([f"- {w['article']} {w['word']} ({w['translation']})" for w in words_data])
        
        prompt = f"""Aşağıdaki Almanca kelimeleri kullanarak kısa ve doğal bir diyalog oluştur.

    KELİMELER:
    {word_list}

    KURALLAR:
    - Diyalog 6-10 satır olsun
    - Her satırda farklı bir karakter konuşsun (Ali, Ayşe, Mehmet, vs.)
    - Her Almanca cümlenin hemen altında Türkçe çevirisi olsun
    - Diyalog günlük hayatta geçen doğal bir konuşma olsun
    - Verilen kelimelerin hepsini kullanmaya çalış

    FORMAT:
    Ali: [Almanca cümle]
    🇹🇷 [Türkçe çeviri]

    Ayşe: [Almanca cümle]
    🇹🇷 [Türkçe çeviri]

    Mehmet: [Almanca cümle]
    🇹🇷 [Türkçe çeviri]

    Lütfen sadece diyaloğu yaz, başka açıklama ekleme."""
        
        # DeepSeek API dene
        if deepseek.is_available():
            try:
                response = deepseek.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "Sen bir Almanca öğretmenisin. B1 seviyesinde öğrenciler için doğal diyaloglar hazırlıyorsun."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    max_tokens=800
                )
                dialog = response.choices[0].message.content
                
                # Diyaloğu challenge'a kaydet
                return dialog
                
            except Exception as e:
                print(f"AI Diyalog hatası: {e}")
                return self.generate_fallback_dialog(words_data)
        else:
            return self.generate_fallback_dialog(words_data)


    def generate_fallback_dialog(self,words_data):
        """API yoksa gösterilecek zengin fallback diyalog"""
        
        if len(words_data) < 2:
            return "Yeterli kelime yok. Lütfen daha fazla kelime ekleyin."
        
        # Kelimeleri al
        w1 = words_data[0] if len(words_data) > 0 else {"word": "lernen", "translation": "öğrenmek"}
        w2 = words_data[1] if len(words_data) > 1 else {"word": "sprechen", "translation": "konuşmak"}
        w3 = words_data[2] if len(words_data) > 2 else {"word": "verstehen", "translation": "anlamak"}
        w4 = words_data[3] if len(words_data) > 3 else {"word": "helfen", "translation": "yardım etmek"}
        w5 = words_data[4] if len(words_data) > 4 else {"word": "üben", "translation": "pratik yapmak"}
        
        # Dinamik diyalog oluştur
        dialog = f"""Ali: Hallo! Ich möchte {w1['word']}.
    🇹🇷 Merhaba! {w1['translation']} istiyorum.

    Ayşe: Das ist super! Kannst du schon {w2['word']}?
    🇹🇷 Bu harika! Zaten {w2['translation']} biliyor musun?

    Ali: Ja, aber ich möchte besser {w3['word']}.
    🇹🇷 Evet, ama daha iyi {w3['translation']} istiyorum.

    Ayşe: Kein Problem! Ich kann dir {w4['word']}.
    🇹🇷 Sorun değil! Sana {w4['translation']} yardım edebilirim.

    Ali: Das wäre toll! Wann können wir {w5['word']}?
    🇹🇷 Bu harika olur! Ne zaman {w5['translation']} yapabiliriz?

    Ayşe: Wie wäre es mit heute Nachmittag?
    🇹🇷 Bu öğleden sonra nasıl olur?

    Ali: Perfekt! Bis später!
    🇹🇷 Mükemmel! Sonra görüşürüz!

    Ayşe: Tschüss und bis gleich!
    🇹🇷 Hoşça kal ve hemen görüşürüz!"""
        
        # Eğer daha fazla kelime varsa ekle
        if len(words_data) > 5:
            w6 = words_data[5]
            dialog += f"""

    Ali: Ach ja, und {w6['word']} ist auch wichtig.
    🇹🇷 Ah evet, {w6['translation']} de önemli.

    Ayşe: Ja, das stimmt! Das lernen wir auch.
    🇹🇷 Evet, doğru! Onu da öğreneceğiz."""
        
        return dialog


    def text_to_speech(text: str, lang: str = "de") -> str:
        """Metni sese çevir (opsiyonel)"""
        try:
            from gtts import gTTS
            import io
            import base64
            
            tts = gTTS(text=text, lang=lang, slow=False)
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            audio_base64 = base64.b64encode(audio_bytes.read()).decode()
            return f'<audio controls style="display:none" autoplay><source src="data:audio/mp3;base64,{audio_base64}" type="audio/mpeg"></audio>'
        except:
            return ""
# Tek örnek oluştur
deepseek = DeepSeekService()