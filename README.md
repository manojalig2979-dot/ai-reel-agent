# 🎬 Free AI Reel Generator & Auto-Publisher

An end-to-end, **100% free-tier** AI agent that takes any topic/prompt, creates a structured script, synthesizes neural voiceover audio, downloads 9:16 vertical AI imagery, animates scenes with Ken Burns motion & subtitles, and publishes or queues them to **Instagram Reels** and **Facebook Pages**.

---

## ⚡ Zero-Cost Architecture

| Component | Technology | Cost / Free Tier |
| :--- | :--- | :--- |
| **Script Generation** | Google Gemini 1.5 Flash / Groq Llama-3 / Built-in Smart Fallback | Free |
| **Voiceover (TTS)** | `edge-tts` (Microsoft Neural Voices) | **100% Free, No API Key Required** |
| **Vertical Imagery** | Pollinations AI (1080x1920 9:16 Flux/SD) | **100% Free, No API Key Required** |
| **Video Engine** | `moviepy` + `ffmpeg` (Ken Burns Motion + High-retention Subtitles) | **100% Free, Local Engine** |
| **Direct Publishing** | Meta Graph API (Instagram & Facebook) | Free Official Developer API |
| **Automation** | APScheduler / Cron | Free |

---

## 🚀 Quick Start

### 1. Launch the Web Studio Dashboard
```bash
python -m streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### 2. Run via Command Line
Generate a single reel immediately:
```bash
python run_cli.py --prompt "The mysterious ocean trenches no human has ever explored" --niche "Science"
```

### 3. Run Automated Daily Scheduler
Start hands-free daily reel creation and posting at 09:00 AM:
```bash
python run_cli.py --schedule --time 09:00
```

---

## 📁 Project Structure

```
e:\nd reel\
│
├── config.py                 # Core paths, voices, dimensions, and API keys
├── requirements.txt          # Python dependencies
├── app.py                    # Streamlit Web UI Dashboard
├── run_cli.py                # Command-Line & Automation Runner
├── .env.example              # Environment variables template
│
├── core/
│   ├── llm_engine.py         # Multi-scene script & visual prompt generator
│   ├── tts_engine.py         # Microsoft Edge TTS neural audio generator
│   ├── image_engine.py       # Pollinations AI vertical 9:16 image fetcher
│   ├── subtitle_engine.py    # High-contrast, dynamic PIL subtitle renderer
│   ├── video_engine.py       # Ken Burns animator, composite & audio mixer
│   ├── publisher.py          # Meta Graph API publisher for IG/FB
│   ├── scheduler.py          # Daily automated job runner
│   └── pipeline.py           # Master end-to-end orchestrator
│
└── output/                   # Rendered MP4 reels, audio files, and publish queue
```

---

## 📱 Meta Graph API Setup (Optional for Auto-Publishing)

1. Create a free developer app at [developers.facebook.com](https://developers.facebook.com).
2. Connect your **Facebook Page** and **Instagram Professional Account**.
3. In Graph API Explorer, obtain a User Access Token with permissions: `pages_manage_posts`, `instagram_content_publish`.
4. Add your credentials to `.env`:
   ```env
   META_ACCESS_TOKEN=your_token_here
   INSTAGRAM_ACCOUNT_ID=your_ig_id
   FACEBOOK_PAGE_ID=your_fb_page_id
   ```
