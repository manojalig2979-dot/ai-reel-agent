import os
from pathlib import Path
from dotenv import load_dotenv
import re

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file if present (override=True ensures latest .env values take effect)
load_dotenv(BASE_DIR / ".env", override=True)

# Directory Paths
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "music"
FONTS_DIR = ASSETS_DIR / "fonts"

# Branding & Logo
LOGO_PATH = ASSETS_DIR / "nd_reel.png"
ENABLE_WATERMARK = True

for path in [OUTPUT_DIR, ASSETS_DIR, MUSIC_DIR, FONTS_DIR]:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError):
        # Streamlit Cloud mounts /mount/src/ as read-only; fall back to /tmp
        import tempfile as _tempfile
        _tmp = Path(_tempfile.gettempdir()) / "nd_reel"
        _tmp.mkdir(parents=True, exist_ok=True)
        if path == OUTPUT_DIR:
            OUTPUT_DIR = _tmp / "output"
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        break


def get_config_val(key: str, default: str = "") -> str:
    """Reads from Streamlit Cloud secrets if available, else os.getenv."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


# LLM Keys (Supports multiple backup keys: comma-separated or separate GEMINI_API_KEY, GEMINI_API_KEY_BACKUP, GEMINI_API_KEY_2, etc.)
def _collect_keys(base_name: str) -> list:
    keys = []
    for var in [f"{base_name}S", base_name, f"{base_name}_1", f"{base_name}_2", f"{base_name}_3", f"{base_name}_4", f"{base_name}_5", f"{base_name}_BACKUP", f"{base_name}_BACKUP_1", f"{base_name}_BACKUP_2", f"{base_name}_BACKUP_3"]:
        raw = get_config_val(var, "")
        if raw:
            for item in re.split(r"[,;\n]+", raw):
                item = item.strip().strip("'\"")
                if item and item not in keys:
                    keys.append(item)
    return keys


GEMINI_API_KEYS = _collect_keys("GEMINI_API_KEY")
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""

GROQ_API_KEYS = _collect_keys("GROQ_API_KEY")
GROQ_API_KEY = GROQ_API_KEYS[0] if GROQ_API_KEYS else ""

# Video Configuration (Standard 9:16 Vertical Reel / YouTube Shorts)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# Visual Art Styles for Dynamic Image Generation
STYLE_PRESETS = {
    "3D Pixar / Disney Animation (Kids & Family)": {
        "tag": "3d_pixar_animation",
        "prompt_suffix": "3D Pixar Disney style CGI animation, vibrant luminous colors, adorable heroic character design, expressive eyes, magical sparkling aura, volumetric cinematic lighting, ultra high quality Disney animation movie render, vertical 9:16",
        "description": "Vibrant, lovable 3D animated style for kids & mythological heroes like Lord Hanuman"
    },
    "Cinematic Hyper-Realistic (8K Masterwork)": {
        "tag": "hyper_realistic",
        "prompt_suffix": "cinematic 8k photograph, photorealistic masterwork, dramatic volumetric lighting, anamorphic lens flare, sharp focus, octane render, vertical 9:16",
        "description": "Ultra-realistic, cinematic film look with rich depth and lighting"
    },
    "Divine Sanatan & Sacred Aura": {
        "tag": "divine_sanatan",
        "prompt_suffix": "divine sacred Vedic art, radiant golden aura, celestial sky, ethereal glowing lotus, magnificent spiritual aura, 8k wallpaper, holy atmosphere, vertical 9:16",
        "description": "Sacred, glowing golden spiritual and Vedic aesthetics"
    },
    "Dynamic Anime & Manga Action": {
        "tag": "anime_action",
        "prompt_suffix": "vibrant Japanese anime action style, high quality anime movie still, sharp line art, dramatic energy effects, glowing particles, vertical 9:16",
        "description": "High-octane anime movie aesthetic with energy particles"
    },
    "Sci-Fi & Cosmic 3D Space": {
        "tag": "sci_fi_cosmic",
        "prompt_suffix": "breathtaking cosmic nebula, deep space stars, futuristic holographic neon glow, Unreal Engine 5 cinematic render, 8k, vertical 9:16",
        "description": "Epic space mysteries and futuristic tech visual style"
    }
}
DEFAULT_STYLE = "3D Pixar / Disney Animation (Kids & Family)"

# TTS Voice Configuration
VOICE_OPTIONS = {
    "Hindi Storyteller Female (Swara)": "hi-IN-SwaraNeural",
    "Hindi Heroic / Energetic Male (Madhur)": "hi-IN-MadhurNeural",
    "English Kid / Animated Voice (Ana)": "en-US-AnaNeural",
    "English Friendly Female Storyteller (Jenny)": "en-US-JennyNeural",
    "Indian English Female (Neerja)": "en-IN-NeerjaNeural",
    "Indian English Male (Prabhat)": "en-IN-PrabhatNeural",
    "Deep American Male Narrator (Christopher)": "en-US-ChristopherNeural",
    "Energetic American Male (Guy)": "en-US-GuyNeural",
    "Casual American Male (Andrew)": "en-US-AndrewNeural",
    "Storyteller American Female (Aria)": "en-US-AriaNeural",
    "British Male (Ryan)": "en-GB-RyanNeural",
    "British Female (Sonia)": "en-GB-SoniaNeural"
}
DEFAULT_VOICE = "hi-IN-SwaraNeural"

# Meta Graph API Credentials (for Instagram & Facebook Auto-Posting)
META_ACCESS_TOKEN = get_config_val("META_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID = get_config_val("INSTAGRAM_ACCOUNT_ID", "")
FACEBOOK_PAGE_ID = get_config_val("FACEBOOK_PAGE_ID", "")

# YouTube Data API Credentials (for YouTube Shorts Auto-Publishing)
YOUTUBE_CLIENT_SECRETS_FILE = get_config_val("YOUTUBE_CLIENT_SECRETS_FILE", str(BASE_DIR / "client_secret.json"))
YOUTUBE_API_KEY = get_config_val("YOUTUBE_API_KEY", "")
YOUTUBE_CHANNEL_ID = get_config_val("YOUTUBE_CHANNEL_ID", "")
