# ai_service.py - mevcut app.py ile aynı klasöre koyun
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class DeepSeekService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1"
        )
    
    def generate_example_sentences(self, word: str, translation: str, level: str = "B1") -> str:
        """Kelime için örnek cümleler üret"""
        prompt = f"""
        Kelime: {word}
        Anlamı: {translation}
        Seviye: {level} (Goethe B1)
        
        Bu Almanca kelime için 2 tane kısa, günlük hayatta kullanılan örnek cümle yaz.
        Her cümlenin altına Türkçe çevirisini ekle.
        Cümleler B1 seviyesinde olsun.
        
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
            return f"AI servis hatası: {str(e)}"
    
    def analyze_weak_words(self, weak_words: list, user_stats: dict) -> str:
        """Zayıf kelimeleri analiz et ve öneri sun"""
        if not weak_words:
            return "Henüz zorlandığın kelime yok, harika gidiyorsun! 🎉"
        
        prompt = f"""
        Kullanıcı şu Almanca kelimelerde zorlanıyor: {', '.join(weak_words[:15])}
        Kullanıcının toplam XP'si: {user_stats.get('total_xp', 0)}
        Günlük serisi: {user_stats.get('streak', 0)} gün
        
        Bu kelimeleri analiz et ve kullanıcıya:
        1. Hangi kalıplarda zorlandığını
        2. Nasıl çalışması gerektiğini
        3. Motive edici bir öneri
        
        Kısa ve samimi bir dille yaz (2-3 cümle).
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Analiz hatası: {str(e)}"
    
    def generate_quiz_question_ai(self, word: str, translation: str) -> list:
        """AI ile çeldirici seçenekler üret"""
        prompt = f"""
        Kelime: {word}
        Doğru anlam: {translation}
        
        Bu Almanca kelime için 3 tane yanlış (çeldirici) Türkçe anlam üret.
        Çeldiriciler anlamca yakın ama doğru olmayan kelimeler olsun.
        Sadece JSON formatında cevap ver: {{"wrong_options": ["seçenek1", "seçenek2", "seçenek3"]}}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=150
            )
            import json
            result = json.loads(response.choices[0].message.content)
            return result.get("wrong_options", [])
        except:
            return []

# Tek örnek oluştur
deepseek = DeepSeekService()