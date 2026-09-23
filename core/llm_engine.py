import os
import sys
import json
import re
import warnings
from typing import Dict, Any, List, Optional
import config

warnings.filterwarnings("ignore", category=FutureWarning)

try:
    from google import genai as modern_genai
except ImportError:
    modern_genai = None

try:
    import google.generativeai as legacy_genai
except ImportError:
    legacy_genai = None

try:
    from groq import Groq
except ImportError:
    Groq = None


def get_system_prompt(niche: str = "General", style: str = "3D Pixar / Disney Animation (Kids & Family)") -> str:
    """Dynamically builds an optimized system prompt based on the chosen niche & visual art style."""
    is_kids_or_animated = any(k in f"{niche} {style}".lower() for k in ["kid", "child", "pixar", "disney", "animation", "hanuman", "bal "])

    if is_kids_or_animated:
        return """You are a world-class children's animated storyteller and viral video creator specializing in captivating mythological stories (like Lord Hanuman, Bal Krishna, Ganesha), moral fables, and inspiring kids content for YouTube Shorts & Instagram Reels.

Your goal is to create a delightful, highly engaging, and child-friendly 3-4 scene vertical reel script in HINDI (or simple English if requested).

Storytelling Rules for Kids:
1. "narration": Energetic, warm, exciting, and simple language that instantly grabs a child's imagination.
2. "visual_prompt": ALWAYS describe the scene in stunning 3D Pixar / Disney style CGI animation:
   - Adorable, heroic, and expressive character designs (e.g. cute mighty young Lord Hanuman with glowing golden gada, bright smiling eyes, divine aura).
   - Rich vibrant colors, magical glowing sparkles, cinematic volumetric lighting, soft Disney-quality textures.
   - Composition: Vertical 9:16 orientation, 8k resolution, cinematic framing.
3. Structure:
   - Scene 1: Exciting hook (e.g. young Hanuman leaping into the sky thinking the sun is a golden fruit!).
   - Scene 2: The thrilling feat / action scene full of wonder and magic.
   - Scene 3: The sweet, inspiring lesson (courage, kindness, devotion, helping friends).
   - Scene 4: A warm, cheerful closing / call to action with a blessing ("बोलो जय श्री राम / जय बजरंगबली!").

Return ONLY a valid JSON object:
{
  "title": "...",
  "scenes": [
    {
      "scene_id": 1,
      "narration": "...",
      "visual_prompt": "3D Pixar Disney style CGI animation, adorable heroic young Lord Hanuman leaping over fluffy clouds..."
    }
  ],
  "caption": "...",
  "hashtags": ["#hanuman", "#kidsstories", "#3danimation", "#mythologyforkids", "#bajrangbali", "#shorts", "#reels"]
}
"""

    return f"""You are an elite short-form video creator and scriptwriter specializing in viral YouTube Shorts & Instagram Reels for the niche: '{niche}'.

Create a captivating, high-retention 3-4 scene vertical reel script tailored to the user's prompt.

Rules:
1. "narration": Compelling, natural, high-retention spoken script (Hindi or English matching user prompt).
2. "visual_prompt": Highly detailed, cinematic visual prompt matching the style '{style}'. Specify 9:16 vertical composition, 8k resolution, cinematic lighting, and vivid atmosphere.
3. Generate a viral hook title, SEO-rich caption, and high-CTR hashtags including #Shorts.

Return ONLY a valid JSON object:
{{
  "title": "...",
  "scenes": [
    {{
      "scene_id": 1,
      "narration": "...",
      "visual_prompt": "..."
    }}
  ],
  "caption": "...",
  "hashtags": ["#shorts", "#reels", "#trending", "#viral"]
}}
"""


POETRY_SYSTEM_PROMPT = """You are an artistic poetry filmmaker and visual storyteller specializing in cinematic Hindi & English poetry reels, spoken word, and soulful shayari on Instagram & YouTube Shorts.

Your task is to take the user's original poem/writing, preserve their exact poetic words, and turn it into a 3-5 scene cinematic vertical reel.

Rules:
1. Divide the poem logically across 3 to 5 scenes so the flow feels organic, rhythmic, and captivating.
2. In each scene:
   - "narration": The EXACT poetic lines/stanza from the user's poem (do NOT modify their words).
   - "visual_prompt": A deeply evocative, aesthetic, cinematic visual prompt (9:16 vertical orientation, 8k resolution, cinematic lighting, artistic mood like golden hour rain, vintage cafe, starry night sky, misty mountains, glowing candlelight, emotional portrait, etc.) that beautifully amplifies the emotion of those specific lines.
3. Generate a compelling poetic title.
4. Generate a caption with emotional hook, author signature, and viral poetry hashtags (#hindipoetry, #kavita, #shayari, #spokenword, #poetryreels, #writersofinstagram, #instapoetry, #reelsindia).

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
  "hashtags": ["#hindipoetry", "#shayari", "#kavita", "#spokenword", "#poetryreels", "#reelsindia"]
}
"""


SCHEDULE_SYSTEM_PROMPT = """You are an expert viral content strategist and weekly programming director for top YouTube Shorts & Instagram Reels creators.

Given a user's instruction or theme (e.g. "Create a 7-day schedule about Lord Hanuman stories for kids in 3D animated style", or "7 days of cosmic space mysteries"), generate a structured 7-day schedule for Monday through Sunday.

For EACH day (Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday), provide:
- "topic": A specific, exciting, high-retention storyline or prompt for that day's reel.
- "niche": Category (e.g. "Kids & Animated Mythology", "Motivation & Mindset", "Science & Space", "Devotional & Spiritual", etc.)
- "style": One of the standard styles: "3D Pixar / Disney Animation (Kids & Family)", "Cinematic Hyper-Realistic (8K Masterwork)", "Divine Sanatan & Sacred Aura", "Dynamic Anime & Manga Action", "Sci-Fi & Cosmic 3D Space"
- "voice": Recommended TTS voice (e.g. "hi-IN-MadhurNeural", "hi-IN-SwaraNeural", "en-US-AnaNeural", "en-US-JennyNeural", "en-US-ChristopherNeural")
- "music": Recommended track keyword ("motivation", "suspense", "lofi", "cyberpunk", "spiritual")
- "audience": Target audience label (e.g. "Kids & Families", "General", "Spiritual Seekers", "Youth")
- "time": Optimal high-traffic schedule time in HH:MM 24-hour format (e.g. "09:00", "18:00", "21:00")

Return ONLY a valid JSON object formatted exactly as:
{
  "Monday": {
    "topic": "...",
    "niche": "...",
    "style": "...",
    "voice": "...",
    "music": "...",
    "audience": "...",
    "time": "21:00"
  },
  "Tuesday": { ... },
  "Wednesday": { ... },
  "Thursday": { ... },
  "Friday": { ... },
  "Saturday": { ... },
  "Sunday": { ... }
}
"""


class LLMEngine:
    def __init__(self, gemini_api_key: Any = None, groq_api_key: Any = None):
        if isinstance(gemini_api_key, list):
            self.gemini_api_keys = [k for k in gemini_api_key if k]
        elif isinstance(gemini_api_key, str) and gemini_api_key.strip():
            self.gemini_api_keys = [k.strip() for k in re.split(r"[,;\n]+", gemini_api_key) if k.strip()]
        else:
            self.gemini_api_keys = config.GEMINI_API_KEYS

        if isinstance(groq_api_key, list):
            self.groq_api_keys = [k for k in groq_api_key if k]
        elif isinstance(groq_api_key, str) and groq_api_key.strip():
            self.groq_api_keys = [k.strip() for k in re.split(r"[,;\n]+", groq_api_key) if k.strip()]
        else:
            self.groq_api_keys = config.GROQ_API_KEYS

    def _call_llm_json(self, system_prompt: str, user_prompt: str) -> Optional[Dict[str, Any]]:
        """Unified LLM caller with multi-tier failover (Gemini -> Groq -> None)."""
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-flash-latest"
        ]

        # 1. Try Gemini
        if self.gemini_api_keys:
            for key in self.gemini_api_keys:
                if modern_genai:
                    try:
                        client = modern_genai.Client(api_key=key)
                        for m in models_to_try:
                            try:
                                response = client.models.generate_content(
                                    model=m,
                                    contents=f"{system_prompt}\n\nUser Request: {user_prompt}",
                                    config={"response_mime_type": "application/json"}
                                )
                                if response and response.text:
                                    parsed = self._extract_json(response.text)
                                    if parsed:
                                        return parsed
                            except Exception:
                                continue
                    except Exception:
                        pass

                if legacy_genai:
                    try:
                        legacy_genai.configure(api_key=key)
                        for m in models_to_try:
                            try:
                                model = legacy_genai.GenerativeModel(m)
                                response = model.generate_content(
                                    f"{system_prompt}\n\nUser Request: {user_prompt}",
                                    request_options={"timeout": 15}
                                )
                                parsed = self._extract_json(response.text)
                                if parsed:
                                    return parsed
                            except Exception:
                                continue
                    except Exception:
                        pass

        # 2. Try Groq
        if Groq and self.groq_api_keys:
            for key in self.groq_api_keys:
                try:
                    client = Groq(api_key=key)
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        response_format={"type": "json_object"}
                    )
                    parsed = json.loads(completion.choices[0].message.content)
                    if parsed:
                        return parsed
                except Exception:
                    continue

        return None

    def generate_script(
        self,
        prompt: str,
        niche: str = "General",
        style: str = "3D Pixar / Disney Animation (Kids & Family)"
    ) -> Dict[str, Any]:
        """Generate structured script, visual prompts, and social copy tailored to topic & style."""
        sys_prompt = get_system_prompt(niche=niche, style=style)
        user_prompt = f"Topic/Theme: {prompt}\nNiche: {niche}\nVisual Style: {style}\nCreate a viral 4-scene Reel / Short."

        res = self._call_llm_json(sys_prompt, user_prompt)
        if res and "scenes" in res:
            return res

        # Built-in fallback generator
        return self._generate_intelligent_fallback(prompt, niche, style)

    def generate_poetry_script(
        self,
        poem_text: str,
        mood: str = "Soulful & Emotional",
        language: str = "Hindi",
        art_style: str = "Cinematic 8K"
    ) -> Dict[str, Any]:
        """Generates scene breakdown and visual prompts for poetry recitation."""
        user_msg = f"Poem Text:\n{poem_text}\n\nMood: {mood}\nLanguage: {language}\nVisual Art Style: {art_style}"
        res = self._call_llm_json(POETRY_SYSTEM_PROMPT, user_msg)
        if res and "scenes" in res:
            return res

        # Built-in fallback poetry parser
        lines = [l.strip() for l in poem_text.strip().split("\n") if l.strip()]
        scenes = []
        chunk_size = max(1, len(lines) // 3) if len(lines) >= 3 else 1
        chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)][:4]
        
        for idx, chunk in enumerate(chunks):
            stanza_text = " ".join(chunk)
            scenes.append({
                "scene_id": idx + 1,
                "narration": stanza_text,
                "visual_prompt": f"Cinematic {art_style} aesthetic visualization of {mood.lower()} poetry, atmospheric misty twilight, subtle glowing bokeh, emotional depth, 8k resolution, vertical 9:16"
            })
        
        return {
            "title": f"Soulful {mood} Poetry",
            "scenes": scenes,
            "caption": f"🖋️ \"{poem_text[:120]}...\"\n\n#Poetry #Shayari #ViralShorts",
            "hashtags": ["#Poetry", "#Shayari", "#HindiPoetry", "#Shorts", "#Reels"]
        }


    def generate_custom_weekly_schedule(self, schedule_prompt: str) -> Dict[str, Dict[str, Any]]:
        """Generates a complete 7-day personalized content schedule from a user's prompt."""
        user_msg = f"User Schedule Request: {schedule_prompt}\nGenerate a complete 7-day schedule (Monday to Sunday) following this theme."
        res = self._call_llm_json(SCHEDULE_SYSTEM_PROMPT, user_msg)
        
        if res and isinstance(res, dict) and "Monday" in res:
            return res

        # Fallback schedule generator tailored to prompt keywords
        return self._generate_fallback_schedule(schedule_prompt)

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
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

    def _generate_intelligent_fallback(self, prompt: str, niche: str, style: str) -> Dict[str, Any]:
        """Intelligent fallback script generator matching the prompt theme."""
        p_lower = prompt.lower()
        
        # Hanuman / Kids Mythology
        if any(k in p_lower for k in ["hanuman", "bajrangbali", "maruti", "sita", "ram", "kid", "child"]):
            return {
                "title": "बाल हनुमान की बाल लीला — असीम शक्ति और भक्ति! 🚩",
                "scenes": [
                    {
                        "scene_id": 1,
                        "narration": "क्या आप जानते हैं? जब बाल हनुमान छोटे थे, तो उन्होंने चमकते सूरज को एक मीठा लाल फल समझकर पकड़ने के लिए छलांग लगा दी थी!",
                        "visual_prompt": "3D Pixar Disney style CGI animation, adorable cute young Bal Hanuman with playful big smiling eyes leaping joyfully through fluffy golden sunset clouds towards the warm radiant sun, vibrant colors, magical sparkles, 9:16 vertical 8k"
                    },
                    {
                        "scene_id": 2,
                        "narration": "इंद्रदेव के वज्र प्रहार के बाद सभी देवताओं ने बाल हनुमान को असीम शक्तियां, अजेय बल और उड़ने का वरदान दिया!",
                        "visual_prompt": "3D animated cinematic rendering of young Bal Hanuman surrounded by divine glowing golden celestial aura and gentle deities showering golden flower petals, Disney Pixar 3D quality, vertical 9:16"
                    },
                    {
                        "scene_id": 3,
                        "narration": "बाल हनुमान हमें सिखाते हैं कि सच्ची शक्ति का उपयोग हमेशा दूसरों की भलाई, रक्षा और प्रेम के लिए करना चाहिए।",
                        "visual_prompt": "3D Pixar style charming young Hanuman lifting a miniature glowing mountain with a warm friendly smile, magical Sanjeevani herbs glowing with cyan light, cute animation, 9:16 vertical"
                    },
                    {
                        "scene_id": 4,
                        "narration": "कमेंट में प्रेम से 'जय बजरंगबली' लिखें और अपने बच्चों को यह सुंदर कहानी सुनाएं!",
                        "visual_prompt": "Cute 3D animated Lord Hanuman folding hands in loving Namaste with glowing heart aura, vibrant festive fireworks in background, cheerful family friendly Disney 3D style, 9:16 vertical"
                    }
                ],
                "caption": "🚩 बाल हनुमान की अद्भुत बाल लीला! 🌸 बच्चों को साहस, भक्ति और सेवा का मार्ग सिखाएं। कमेंट में 'जय श्री राम' लिखें! ✨\n\n#LordHanuman #BalHanuman #KidsStories #3DAnimation #PixarStyle #Bajrangbali #Shorts #ViralReels #SanatanDharma",
                "hashtags": ["#LordHanuman", "#BalHanuman", "#KidsStories", "#3DAnimation", "#Bajrangbali", "#Shorts", "#Reels"]
            }

        # Space / Science
        if any(k in p_lower for k in ["space", "black hole", "universe", "planet", "cosmic"]):
            return {
                "title": "The Terrifying Mystery of Black Holes 🌌",
                "scenes": [
                    {
                        "scene_id": 1,
                        "narration": "If you fell into a supermassive black hole, time would literally slow down for you while the entire universe ages in seconds!",
                        "visual_prompt": "Epic 3D CGI cinematic visualization of a glowing supermassive black hole accretion disk with radiant cyan and orange plasma vortex, deep cosmic stars, 9:16 vertical 8k"
                    },
                    {
                        "scene_id": 2,
                        "narration": "Beyond the Event Horizon, gravity becomes so intense that even light cannot escape, creating a tear in spacetime.",
                        "visual_prompt": "Futuristic astronaut in glowing spacesuit looking into a gravitational lensing cosmic wormhole, volumetric lighting, Unreal Engine 5 render, 9:16 vertical"
                    },
                    {
                        "scene_id": 3,
                        "narration": "Scientists believe that at the singularity, all laws of current physics break down into the unknown.",
                        "visual_prompt": "Mystical glowing quantum singularity with fractal geometry and cosmic nebula clouds, deep space aesthetic, 8k resolution, vertical 9:16"
                    },
                    {
                        "scene_id": 4,
                        "narration": "Subscribe for more mind-blowing cosmic discoveries every day!",
                        "visual_prompt": "Cinematic vertical shot of Earth rising over the Moon with a brilliant solar eclipse flare, 8k space photography, 9:16 vertical"
                    }
                ],
                "caption": "🌌 The terrifying cosmic mystery of Black Holes! Would you ever dare to explore deep space? #Shorts #Space #CosmicMysteries",
                "hashtags": ["#Shorts", "#Space", "#BlackHole", "#CosmicMysteries", "#Science", "#NASA", "#ViralShorts"]
            }

        # General High-Impact Motivational
        return {
            "title": f"The Ultimate Secret to {prompt[:30]}",
            "scenes": [
                {
                    "scene_id": 1,
                    "narration": f"Here is the powerful truth about {prompt[:40]} that 99% of people realize too late.",
                    "visual_prompt": f"Cinematic 3D masterwork representing determination and victory, dramatic golden rim lighting, 8k vertical 9:16"
                },
                {
                    "scene_id": 2,
                    "narration": "When you stop waiting for the perfect moment and start taking disciplined action, everything shifts.",
                    "visual_prompt": "Epic cinematic shot of a lone champion standing atop a mountain summit at golden sunrise, volumetric mist, 9:16 vertical"
                },
                {
                    "scene_id": 3,
                    "narration": "Remember: Consistency beats talent when talent forgets to work hard. Keep pushing forward.",
                    "visual_prompt": "Glowing golden hourglass with luminous sand flowing against gravity, cinematic lighting, 8k vertical"
                },
                {
                    "scene_id": 4,
                    "narration": "Type 'YES' if you are ready to conquer your goals, and follow for daily inspiration!",
                    "visual_prompt": "Majestic golden eagle soaring into a radiant sunburst sky, 8k hyper-realistic photography, 9:16 vertical"
                }
            ],
            "caption": f"⚡ Daily motivation on {prompt}! Drop a like and subscribe for more. #Shorts #Motivation",
            "hashtags": ["#Shorts", "#Motivation", "#Success", "#Discipline", "#Mindset", "#Trending"]
        }

    def _generate_fallback_schedule(self, prompt: str) -> Dict[str, Dict[str, Any]]:
        """Generates a contextual 7-day schedule when requested topic is detected."""
        p_lower = prompt.lower()
        if any(k in p_lower for k in ["hanuman", "kids", "child", "maruti", "mythology"]):
            return {
                "Monday": {
                    "topic": "Bal Hanuman and the Golden Sun — How young Hanuman leaped to catch the sun thinking it was a sweet fruit!",
                    "niche": "Kids & Animated Mythology",
                    "style": "3D Pixar / Disney Animation (Kids & Family)",
                    "voice": "hi-IN-MadhurNeural",
                    "music": "motivation",
                    "audience": "Kids & Families"
                },
                "Tuesday": {
                    "topic": "Hanuman's Mighty Ocean Leap — Crossing the turbulent sea with fearless courage and loyalty to Shri Ram!",
                    "niche": "Kids & Animated Mythology",
                    "style": "3D Pixar / Disney Animation (Kids & Family)",
                    "voice": "hi-IN-MadhurNeural",
                    "music": "motivation",
                    "audience": "Kids & Families"
                },
                "Wednesday": {
                    "topic": "Lifting Mount Dronagiri — When Hanuman brought the entire Sanjeevani mountain to save Lakshman!",
                    "niche": "Kids & Animated Mythology",
                    "style": "3D Pixar / Disney Animation (Kids & Family)",
                    "voice": "hi-IN-SwaraNeural",
                    "music": "motivation",
                    "audience": "Kids & Families"
                },
                "Thursday": {
                    "topic": "The Golden Lanka & Ring of Faith — How Hanuman met Mother Sita in Ashok Vatika and gave her hope!",
                    "niche": "Kids & Animated Mythology",
                    "style": "3D Pixar / Disney Animation (Kids & Family)",
                    "voice": "hi-IN-SwaraNeural",
                    "music": "lofi",
                    "audience": "Kids & Families"
                },
                "Friday": {
                    "topic": "Hanuman's Heart of Devotion — The divine moment Hanuman tore open his chest to show Sita-Ram in his heart!",
                    "niche": "Kids & Animated Mythology",
                    "style": "3D Pixar / Disney Animation (Kids & Family)",
                    "voice": "hi-IN-SwaraNeural",
                    "music": "spiritual",
                    "audience": "Kids & Families"
                },
                "Saturday": {
                    "topic": "Shani Dev and Hanuman's Protection — Why Hanuman protects everyone from fear, troubles, and negative energy!",
                    "niche": "Kids & Animated Mythology",
                    "style": "3D Pixar / Disney Animation (Kids & Family)",
                    "voice": "hi-IN-MadhurNeural",
                    "music": "suspense",
                    "audience": "Kids & Families"
                },
                "Sunday": {
                    "topic": "The Superpower of Hanuman Chalisa for Kids — 3 amazing lessons of strength, focus, and kindness for young champions!",
                    "niche": "Kids & Animated Mythology",
                    "style": "3D Pixar / Disney Animation (Kids & Family)",
                    "voice": "hi-IN-SwaraNeural",
                    "music": "motivation",
                    "audience": "Kids & Families"
                }
            }

        # Default versatile weekly plan
        return {
            "Monday": {
                "topic": "3 Stoic rules to become emotionally untouchable and laser-focused throughout the week",
                "niche": "Motivation & Mindset",
                "style": "Cinematic Hyper-Realistic (8K Masterwork)",
                "voice": "hi-IN-MadhurNeural",
                "music": "motivation",
                "audience": "Youth & Professionals"
            },
            "Tuesday": {
                "topic": "The terrifying cosmic mystery of what happens inside a supermassive black hole event horizon",
                "niche": "Science & Space",
                "style": "Sci-Fi & Cosmic 3D Space",
                "voice": "en-US-ChristopherNeural",
                "music": "suspense",
                "audience": "Curious Minds"
            },
            "Wednesday": {
                "topic": "How humanoid AI robots and neural interfaces will reshape daily human life by 2030",
                "niche": "AI & Future Tech",
                "style": "Sci-Fi & Cosmic 3D Space",
                "voice": "en-US-GuyNeural",
                "music": "cyberpunk",
                "audience": "Tech Enthusiasts"
            },
            "Thursday": {
                "topic": "The ancient underground city of Derinkuyu that housed 20,000 people deep beneath the earth",
                "niche": "Dark History & Mysteries",
                "style": "Cinematic Hyper-Realistic (8K Masterwork)",
                "voice": "en-US-ChristopherNeural",
                "music": "suspense",
                "audience": "History Buffs"
            },
            "Friday": {
                "topic": "5 subtle psychological tricks that instantly reveal if someone is lying right to your face",
                "niche": "Psychology Facts",
                "style": "Cinematic Hyper-Realistic (8K Masterwork)",
                "voice": "en-US-JennyNeural",
                "music": "lofi",
                "audience": "General"
            },
            "Saturday": {
                "topic": "How top billionaire investors use asymmetry to generate massive wealth while risking almost nothing",
                "niche": "Business & Wealth",
                "style": "Cinematic Hyper-Realistic (8K Masterwork)",
                "voice": "hi-IN-MadhurNeural",
                "music": "motivation",
                "audience": "Entrepreneurs"
            },
            "Sunday": {
                "topic": "The deepest unexplored ocean trenches that are more terrifying and mysterious than outer space",
                "niche": "Science & Space",
                "style": "Sci-Fi & Cosmic 3D Space",
                "voice": "en-US-ChristopherNeural",
                "music": "suspense",
                "audience": "General"
            }
        }
