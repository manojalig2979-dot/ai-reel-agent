import os
import sys
import json
import re
import warnings
from typing import Dict, Any, List
import config

warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from groq import Groq
except ImportError:
    Groq = None


SYSTEM_PROMPT = """You are an expert spiritual video creator and scriptwriter specializing in viral Bhagavad Gita, Sanatan Dharma, and motivational Hindi Instagram Reels & YouTube Shorts.

When given a Bhagavad Gita shloka or topic, generate a highly emotional, divine, and engaging 3-4 scene vertical reel script in HINDI (with Sanskrit shloka).

For each scene:
1. "narration": Spoken text in clear, pure, emotional Hindi (or Sanskrit for the shloka recitation).
2. "visual_prompt": A highly detailed, cinematic, spiritual visual prompt for AI image generation (e.g. Lord Krishna in golden chariot, divine aura, Kurukshetra battlefield, sacred lotus, cosmic Vishwaroop, 9:16 vertical orientation, 8k photography, cinematic lighting, ultra-realistic).

Structure:
- Scene 1: Sanskrit Shloka recitation with divine hook.
- Scene 2: Clear, impactful Hindi translation (सरल अर्थ).
- Scene 3: Practical Life Lesson / Wisdom application (जीवन सूत्र).
- Scene 4: Divine blessing & Call to action ("जय श्री कृष्णा / हरे कृष्णा").

Return ONLY a valid JSON object:
{
  "title": "...",
  "scenes": [
    {
      "scene_id": 1,
      "narration": "...",
      "visual_prompt": "..."
    }
  ],
  "caption": "...",
  "hashtags": ["#bhagavadgita", "#lordkrishna", "#krishnaquotes", "#geetaupdesh", "#dailygeeta", "#sanatandharma", "#reelsindia"]
}
"""

class LLMEngine:
    def __init__(self, gemini_api_key: str = None, groq_api_key: str = None):
        self.gemini_api_key = gemini_api_key or config.GEMINI_API_KEY
        self.groq_api_key = groq_api_key or config.GROQ_API_KEY

        if self.gemini_api_key and genai:
            try:
                genai.configure(api_key=self.gemini_api_key)
            except Exception:
                pass

    def generate_script(self, prompt: str, niche: str = "Bhagavad Gita & Spirituality") -> Dict[str, Any]:
        """Generate structured script, visual prompts, and social copy."""
        full_prompt = f"Topic/Theme: {prompt}\nNiche: {niche}\nLanguage: Hindi + Sanskrit Shloka\nCreate a viral 4-scene Bhagavad Gita Reel."

        # 1. Try Gemini
        if self.gemini_api_key and genai:
            models_to_try = ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-pro"]
            for m in models_to_try:
                try:
                    model = genai.GenerativeModel(m)
                    response = model.generate_content(
                        f"{SYSTEM_PROMPT}\n\nUser Request: {full_prompt}"
                    )
                    parsed = self._extract_json(response.text)
                    if parsed and "scenes" in parsed:
                        return parsed
                except Exception:
                    continue

        # 2. Try Groq
        if self.groq_api_key and Groq:
            try:
                client = Groq(api_key=self.groq_api_key)
                completion = client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                parsed = json.loads(completion.choices[0].message.content)
                if parsed and "scenes" in parsed:
                    return parsed
            except Exception as e:
                print(f"[LLMEngine] Groq error: {e}. Falling back...")

        # 3. Intelligent Built-in Spiritual Fallback Generator (100% Free, Zero Keys Required)
        return self._generate_gita_fallback_script(prompt)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        try:
            cleaned = re.sub(r"```(?:json)?", "", text).strip()
            return json.loads(cleaned)
        except Exception:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
        return None

    def _generate_gita_fallback_script(self, prompt: str) -> Dict[str, Any]:
        """Generates authentic Hindi Bhagavad Gita shloka script."""
        is_karmanye = "कर्मण्येवाधिकारस्ते" in prompt or "2" in prompt
        
        if is_karmanye:
            return {
                "title": "कर्मण्येवाधिकारस्ते — गीता का सबसे बड़ा ज्ञान",
                "scenes": [
                    {
                        "scene_id": 1,
                        "narration": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन। मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥",
                        "visual_prompt": "Cinematic vertical shot of Lord Krishna in divine golden chariot with Arjuna at Kurukshetra battlefield, glowing cosmic light aura, sacred peacock feather crown, photorealistic 8k, divine spiritual atmosphere, 9:16 vertical orientation"
                    },
                    {
                        "scene_id": 2,
                        "narration": "भगवान श्री कृष्ण कहते हैं: तुम्हारा अधिकार केवल कर्म करने में है, उसके फल में कभी नहीं। इसलिए फल की चिंता छोड़कर श्रेष्ठ कर्म करो।",
                        "visual_prompt": "Epic close-up of Lord Krishna with compassionate divine smile, radiant halo of golden sunlight, hands blessing, highly detailed 8k photography, vertical 9:16 framing"
                    },
                    {
                        "scene_id": 3,
                        "narration": "आज का जीवन सूत्र: जब आप परिणाम की चिंता छोड़ केवल अपनी मेहनत पर ध्यान देते हैं, तो तनाव खत्म हो जाता है और सफलता निश्चित होती है।",
                        "visual_prompt": "Cinematic symbolic visualization of self-mastery and inner peace, blooming glowing golden lotus floating on sacred river, mystical rays of divine light, 9:16 vertical ratio"
                    },
                    {
                        "scene_id": 4,
                        "narration": "कमेंट में 'जय श्री कृष्णा' जरूर लिखें और प्रतिदिन गीता ज्ञान के लिए अभी फॉलो करें!",
                        "visual_prompt": "Breathtaking spiritual visual of Lord Krishna playing divine bansuri flute in Vrindavan twilight, cosmic starry sky, serene transcendent aesthetic, 9:16 vertical composition"
                    }
                ],
                "caption": "🚩 श्रीमद्भगवद्गीता का अनमोल ज्ञान: कर्म करो, फल की चिंता परमात्मा पर छोड़ दो। 🌸\n\nकमेंट में 'जय श्री कृष्णा' अवश्य लिखें और इस पवित्र ज्ञान को अपने मित्रों के साथ शेयर करें। 🙏",
                "hashtags": ["#bhagavadgita", "#lordkrishna", "#krishnaquotes", "#geetaupdesh", "#dailygeeta", "#radhakrishna", "#sanatandharma", "#reelsindia", "#fyp", "#viralreels"]
            }
        else:
            return {
                "title": "श्रीमद्भगवद्गीता — आज का दिव्य ज्ञान",
                "scenes": [
                    {
                        "scene_id": 1,
                        "narration": "नैनं छिन्दन्ति शस्त्राणि नैनं दहति पावकः। न चैनं क्लेदयन्त्यापो न शोषयति मारुतः॥",
                        "visual_prompt": "Majestic vertical 9:16 cinematic visual of Lord Krishna in divine radiant golden form, cosmic spiritual energy vortex, sacred halo, 8k resolution"
                    },
                    {
                        "scene_id": 2,
                        "narration": "आत्मा को न शस्त्र काट सकते हैं, न आग जला सकती है, न जल भिगो सकता है और न वायु सुखा सकती है। आत्मा अमर और शाश्वत है।",
                        "visual_prompt": "Transcendent visualization of the immortal luminous soul, pure glowing golden energy surrounded by celestial cosmic stars, 9:16 vertical framing"
                    },
                    {
                        "scene_id": 3,
                        "narration": "आज का जीवन सूत्र: जीवन में कभी भयभीत मत होइए। परिस्थितियां बदलती हैं, परंतु आपकी अंतरात्मा अजेय और असीम शक्ति से भरी है।",
                        "visual_prompt": "Cinematic serene sunrise over ancient sacred Himalayan peaks, divine golden sun rays casting peace upon earth, spiritual aura, 9:16 vertical composition"
                    },
                    {
                        "scene_id": 4,
                        "narration": "कमेंट में 'हरे कृष्णा' लिखें और गीता के दैनिक ज्ञान से जुड़ने के लिए अभी फॉलो करें!",
                        "visual_prompt": "Aesthetic divine portrait of Lord Krishna holding the holy conch Panchajanya, golden rays, divine tranquility, vertical 9:16 orientation"
                    }
                ],
                "caption": "🌸 आत्मा अमर है, भय को त्यागकर अपने धर्म का पालन करें। — श्रीमद्भगवद्गीता 🚩\n\nकमेंट में 'हरे कृष्णा' लिखकर अपने दिन को मंगलमय बनाएं! 🙏",
                "hashtags": ["#bhagavadgita", "#lordkrishna", "#krishnaquotes", "#geetaupdesh", "#dailygeeta", "#radhakrishna", "#sanatandharma", "#reelsindia", "#fyp", "#viralreels"]
            }
