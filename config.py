import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file if present
load_dotenv(BASE_DIR / ".env")

# Directory Paths
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "music"
FONTS_DIR = ASSETS_DIR / "fonts"

# Branding & Logo
LOGO_PATH = ASSETS_DIR / "nd_reel.png"
ENABLE_WATERMARK = True

for path in [OUTPUT_DIR, ASSETS_DIR, MUSIC_DIR, FONTS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

import re

def get_config_val(key: str, default: str = "") -> str:
    """Reads from Streamlit Cloud secrets if available, else os.getenv."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)

# LLM Keys (Supports multiple backup keys: key1, key2, key3)
raw_gemini_keys = get_config_val("GEMINI_API_KEYS") or get_config_val("GEMINI_API_KEY", "")
GEMINI_API_KEYS = [k.strip() for k in re.split(r"[,;\n]+", raw_gemini_keys) if k.strip()]
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""

raw_groq_keys = get_config_val("GROQ_API_KEYS") or get_config_val("GROQ_API_KEY", "")
GROQ_API_KEYS = [k.strip() for k in re.split(r"[,;\n]+", raw_groq_keys) if k.strip()]
GROQ_API_KEY = GROQ_API_KEYS[0] if GROQ_API_KEYS else ""

# Video Configuration (Standard 9:16 Vertical Reel)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# TTS Voice Configuration (Default: Hindi Female)
VOICE_OPTIONS = {
    "Hindi Female (Swara)": "hi-IN-SwaraNeural",
    "Hindi Male (Madhur)": "hi-IN-MadhurNeural",
    "Indian English Female (Neerja)": "en-IN-NeerjaNeural",
    "Indian English Male (Prabhat)": "en-IN-PrabhatNeural",
    "Deep American Male (Christopher)": "en-US-ChristopherNeural",
    "Energetic American Male (Guy)": "en-US-GuyNeural",
    "Casual American Male (Andrew)": "en-US-AndrewNeural",
    "Empathetic American Female (Jenny)": "en-US-JennyNeural",
    "Storyteller American Female (Aria)": "en-US-AriaNeural",
    "British Male (Ryan)": "en-GB-RyanNeural",
    "British Female (Sonia)": "en-GB-SoniaNeural"
}
DEFAULT_VOICE = "hi-IN-SwaraNeural"

# Meta Graph API Credentials (for Instagram & Facebook Auto-Posting)
META_ACCESS_TOKEN = get_config_val("META_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID = get_config_val("INSTAGRAM_ACCOUNT_ID", "")
FACEBOOK_PAGE_ID = get_config_val("FACEBOOK_PAGE_ID", "")
