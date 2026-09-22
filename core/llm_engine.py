import os
import sys
import json
import re
import warnings
from typing import Dict, Any, List
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

    def generate_script(self, prompt: str, niche: str = "Bhagavad Gita & Spirituality") -> Dict[str, Any]:
        """Generate structured script, visual prompts, and social copy with multi-key failover."""
        full_prompt = f"Topic/Theme: {prompt}\nNiche: {niche}\nLanguage: Hindi + Sanskrit Shloka\nCreate a viral 4-scene Bhagavad Gita Reel."

        # 1. Try Gemini Keys with automatic backup failover
        if self.gemini_api_keys:
            # Free-tier Flash & Lite models in priority order
            models_to_try = [
                "gemini-3.8-flash",
                "gemini-3.7-flash",
                "gemini-3.5-flash",
                "gemini-3.5-flash-lite",
                "gemini-3.1-flash-lite",
                "gemini-3.6-flash",
                "gemini-flash-latest"
            ]
            for key_idx, key in enumerate(self.gemini_api_keys):
                masked_key = f"...{key[-6:]}" if len(key) > 6 else "key"
                
                # A. Try modern google.genai SDK
                if modern_genai:
                    try:
                        client = modern_genai.Client(api_key=key)
                        for m in models_to_try:
                            try:
                                response = client.models.generate_content(
                                    model=m,
                                    contents=f"{SYSTEM_PROMPT}\n\nUser Request: {full_prompt}",
                                    config={"response_mime_type": "application/json"}
                                )
                                if response and response.text:
                                    parsed = self._extract_json(response.text)
                                    if parsed and "scenes" in parsed:
                                        print(f"[LLMEngine] Successfully generated script using Gemini ({m}, key {key_idx+1}/{len(self.gemini_api_keys)} [{masked_key}])")
                                        return parsed
                            except Exception as me:
                                err_str = str(me).upper()
                                if any(k in err_str for k in ["API_KEY_INVALID", "PERMISSION_DENIED", "RESOURCE_EXHAUSTED", "QUOTA"]):
                                    print(f"[LLMEngine] Gemini key #{key_idx+1} ({masked_key}) quota/auth error. Trying backup key...")
                                    break
                                continue
                    except Exception:
                        pass

                # B. Fallback to legacy SDK if needed
                if legacy_genai:
                    try:
                        legacy_genai.configure(api_key=key)
                        for m in models_to_try:
                            try:
                                model = legacy_genai.GenerativeModel(m)
                                response = model.generate_content(
                                    f"{SYSTEM_PROMPT}\n\nUser Request: {full_prompt}",
                                    request_options={"timeout": 15}
                                )
                                parsed = self._extract_json(response.text)
                                if parsed and "scenes" in parsed:
                                    print(f"[LLMEngine] Successfully generated script using legacy Gemini ({m})")
                                    return parsed
                            except Exception:
                                continue
                    except Exception:
                        pass

        # 2. Try Groq Keys with backup failover
        if Groq and self.groq_api_keys:
            for key_idx, key in enumerate(self.groq_api_keys):
                masked_key = f"...{key[-6:]}" if len(key) > 6 else "key"
                try:
                    client = Groq(api_key=key)
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
                        print(f"[LLMEngine] Successfully generated script using Groq (key {key_idx+1}/{len(self.groq_api_keys)} [{masked_key}])")
                        return parsed
                except Exception as e:
                    print(f"[LLMEngine] Groq key #{key_idx+1} ({masked_key}) failed: {e}. Trying backup...")

        # 3. Intelligent Built-in Spiritual Fallback Generator (100% Free, Zero Keys Required)
        print("[LLMEngine] Using intelligent built-in spiritual script generator...")
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

    def generate_poetry_script(
        self,
        poem_text: str,
        mood: str = "Soulful & Emotional",
        language: str = "Hindi",
        art_style: str = "Cinematic 8K"
    ) -> Dict[str, Any]:
        """
        Takes original poem/shayari text, preserves user's exact words,
        and generates a 3-5 scene vertical poetry reel with emotional visual prompts.
        """
        full_prompt = (
            f"Original Poem/Writing:\n{poem_text.strip()}\n\n"
            f"Language: {language}\n"
            f"Mood / Atmosphere: {mood}\n"
            f"Visual Art Style: {art_style}\n"
            f"Please structure this poem into 3-5 visual scenes while preserving the exact poetic lines."
        )

        models_to_try = [
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.6-flash",
            "gemini-flash-latest"
        ]

        # 1. Try Gemini
        if self.gemini_api_keys:
            for key_idx, key in enumerate(self.gemini_api_keys):
                masked_key = f"...{key[-6:]}" if len(key) > 6 else "key"
                if modern_genai:
                    try:
                        client = modern_genai.Client(api_key=key)
                        for m in models_to_try:
                            try:
                                response = client.models.generate_content(
                                    model=m,
                                    contents=f"{POETRY_SYSTEM_PROMPT}\n\nUser Request: {full_prompt}",
                                    config={"response_mime_type": "application/json"}
                                )
                                if response and response.text:
                                    parsed = self._extract_json(response.text)
                                    if parsed and "scenes" in parsed:
                                        print(f"[LLMEngine] Successfully generated poetry script with Gemini ({m})")
                                        return parsed
                            except Exception as me:
                                err_str = str(me).upper()
                                if any(k in err_str for k in ["API_KEY_INVALID", "PERMISSION_DENIED", "RESOURCE_EXHAUSTED", "QUOTA"]):
                                    break
                                continue
                    except Exception:
                        pass

        # 2. Try Groq
        if Groq and self.groq_api_keys:
            for key in self.groq_api_keys:
                try:
                    client = Groq(api_key=key)
                    completion = client.chat.completions.create(
                        model="llama-3.1-70b-versatile",
                        messages=[
                            {"role": "system", "content": POETRY_SYSTEM_PROMPT},
                            {"role": "user", "content": full_prompt}
                        ],
                        temperature=0.7,
                        response_format={"type": "json_object"}
                    )
                    parsed = json.loads(completion.choices[0].message.content)
                    if parsed and "scenes" in parsed:
                        return parsed
                except Exception:
                    continue

        # 3. Intelligent Built-in Stanza Splitting Fallback
        return self._generate_poetry_fallback_script(poem_text, mood, art_style)

    def _generate_poetry_fallback_script(self, poem_text: str, mood: str, art_style: str) -> Dict[str, Any]:
        """Intelligently divides user poem by lines/stanzas and assigns mood-matching visual prompts."""
        lines = [l.strip() for l in poem_text.strip().split("\n") if l.strip()]
        if not lines:
            lines = ["मेरी खामोशियाँ भी एक दास्तान कहती हैं।"]

        # Group lines into 3-4 scenes
        num_scenes = min(4, max(2, len(lines)))
        chunk_size = max(1, math.ceil(len(lines) / num_scenes)) if 'math' in globals() else max(1, (len(lines) + num_scenes - 1) // num_scenes)
        
        scenes = []
        visual_themes = [
            f"Cinematic aesthetic vertical 9:16 shot, {art_style.lower()}, emotional solitude, golden twilight sunlight glowing through window, soft bokeh, 8k photography",
            f"Aesthetic vertical 9:16 portrait, {art_style.lower()}, deep melancholic atmosphere, rainy evening cafe with warm glowing lights, raindrops on glass",
            f"Moody poetic visual, {art_style.lower()}, solitary figure walking under starry night sky, misty distant mountains, ethereal moonlight, 9:16 framing",
            f"Breathtaking vertical 9:16 cinematic visual, {art_style.lower()}, vintage open journal with fountain pen, rose petals in gentle wind, soft atmospheric lighting"
        ]

        current_idx = 0
        scene_id = 1
        while current_idx < len(lines) and scene_id <= 4:
            chunk = lines[current_idx:current_idx + chunk_size]
            current_idx += chunk_size
            narration_text = " । ".join(chunk)
            vis = visual_themes[(scene_id - 1) % len(visual_themes)]
            scenes.append({
                "scene_id": scene_id,
                "narration": narration_text,
                "visual_prompt": vis
            })
            scene_id += 1

        first_line = lines[0][:40]
        return {
            "title": f"Poetic Soul — {first_line}",
            "mood": mood,
            "scenes": scenes,
            "caption": f"✨ \"{poem_text[:120]}...\"\n\nशब्दों की गहराइयां। अगर ये पंक्तियां आपके दिल को छू गईं तो शेयर अवश्य करें। 🖋️\n\n— ND Poetry",
            "hashtags": ["#hindipoetry", "#shayari", "#kavita", "#spokenword", "#poetryreels", "#hindikavita", "#writerslife", "#reelsindia", "#viralreels"]
        }
