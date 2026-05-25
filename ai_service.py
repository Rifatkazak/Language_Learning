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

# Tek örnek oluştur
deepseek = DeepSeekService()