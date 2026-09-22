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

# LLM Keys (Optional - Fallbacks available)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Video Configuration (Standard 9:16 Vertical Reel)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# TTS Voice Configuration
VOICE_OPTIONS = {
    "Deep American Male (Christopher)": "en-US-ChristopherNeural",
    "Energetic American Male (Guy)": "en-US-GuyNeural",
    "Casual American Male (Andrew)": "en-US-AndrewNeural",
    "Empathetic American Female (Jenny)": "en-US-JennyNeural",
    "Storyteller American Female (Aria)": "en-US-AriaNeural",
    "British Male (Ryan)": "en-GB-RyanNeural",
    "British Female (Sonia)": "en-GB-SoniaNeural",
    "Indian English Male (Prabhat)": "en-IN-PrabhatNeural",
    "Indian English Female (Neerja)": "en-IN-NeerjaNeural",
    "Hindi Male (Madhur)": "hi-IN-MadhurNeural",
    "Hindi Female (Swara)": "hi-IN-SwaraNeural"
}
DEFAULT_VOICE = "en-US-ChristopherNeural"

# Meta Graph API Credentials (for Instagram & Facebook Auto-Posting)
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")
