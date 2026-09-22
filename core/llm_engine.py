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


SYSTEM_PROMPT = """You are an elite short-form video creator and scriptwriter specializing in viral Instagram Reels, YouTube Shorts, and TikTok videos.
Your task is to take a given topic or prompt and generate a high-retention, engaging 15-45 second video script divided into 3 to 5 scenes.

For each scene, provide:
1. "narration": Punchy, engaging, spoken voiceover text (1 to 2 sentences per scene).
2. "visual_prompt": A highly detailed, cinematic, photorealistic visual description suitable for AI image generation. Include lighting, mood, camera angle, and vertical 9:16 composition hints.

Also provide:
- "title": A catchy hook title for the reel.
- "caption": A compelling, engaging social media caption with a call to action.
- "hashtags": A list of 5-8 trending and relevant hashtags.

CRITICAL: Return ONLY a valid JSON object without markdown code blocks, backticks, or extra text. Format:
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
  "hashtags": ["#reel", "#fact"]
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

    def generate_script(self, prompt: str, niche: str = "General") -> Dict[str, Any]:
        """Generate structured script, visual prompts, and social copy."""
        full_prompt = f"Topic/Theme: {prompt}\nNiche: {niche}\nCreate a viral 3-4 scene reel."

        # 1. Try Gemini if API key available
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
                except Exception as e:
                    continue

        # 2. Try Groq if API key available
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

        # 3. Intelligent Built-in Fallback Generator (100% Free, Zero API Keys Required)
        return self._generate_fallback_script(prompt, niche)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Safely extract JSON from text response."""
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

    def _generate_fallback_script(self, prompt: str, niche: str) -> Dict[str, Any]:
        """Intelligent offline script generator when API keys are not provided."""
        clean_topic = prompt.strip().title() if prompt else "Unbelievable Facts"
        
        return {
            "title": f"The Untold Truth About {clean_topic}",
            "scenes": [
                {
                    "scene_id": 1,
                    "narration": f"Did you know this mind-blowing truth about {clean_topic}? Most people get this completely wrong.",
                    "visual_prompt": f"Cinematic vertical shot representing {clean_topic}, dramatic volumetric lighting, highly detailed, photorealistic 8k resolution, vertical 9:16 framing"
                },
                {
                    "scene_id": 2,
                    "narration": f"Deep beneath the surface, {clean_topic} reveals an extraordinary mystery that experts are still investigating today.",
                    "visual_prompt": f"Epic visualization of {clean_topic} in action, intense glowing reflections, stunning depth of field, vertical 9:16 format"
                },
                {
                    "scene_id": 3,
                    "narration": f"When you look closer, the sheer scale and complexity will change how you view the world forever.",
                    "visual_prompt": f"Breathtaking wide-angle cinematic perspective of {clean_topic}, cosmic lighting, vibrant colors, 9:16 vertical ratio"
                },
                {
                    "scene_id": 4,
                    "narration": f"Follow for more incredible daily discoveries and comment your thoughts below!",
                    "visual_prompt": f"Inspiring and aesthetic cinematic ending visual representing the future of {clean_topic}, golden hour rays, vertical composition"
                }
            ],
            "caption": f"Mind = blown! The fascinating reality of {clean_topic}. What surprised you the most? Let us know in the comments! 👇",
            "hashtags": ["#viralreels", "#explorepage", f"#{clean_topic.replace(' ', '').lower()}", "#didyouknow", "#mindblown", "#dailyreels", "#fyp"]
        }
