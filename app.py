import os
import sys

# ── UTF-8 fix: must be first, before any other import ──────────────────────
# Python 3.14 on Windows defaults the terminal to cp1252, which crashes when
# Hindi text / emoji appear in print() output OR in enhanced tracebacks.
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
# ───────────────────────────────────────────────────────────────────────────

import json
import time
from pathlib import Path
from datetime import datetime
import importlib
import streamlit as st
import config
importlib.reload(config)
from core.pipeline import ReelPipeline
from core.publisher import MetaPublisher
from core.youtube_publisher import YouTubePublisher
from core.tag_engine import TagOptimizer
from core.weekly_planner import WeeklyPlanner

# Check if custom logo exists and load it for use as browser tab favicon
has_custom_logo = config.LOGO_PATH.exists()
if has_custom_logo:
    try:
        from PIL import Image as _PILImage
        _logo_img = _PILImage.open(str(config.LOGO_PATH))
    except Exception:
        _logo_img = "🎬"
else:
    _logo_img = "🎬"

st.set_page_config(
    page_title="ND Reel Studio — 7-Day AI Auto-Publisher & YouTube Shorts",
    page_icon=_logo_img,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Desktop & Studio App
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    #MainMenu {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    header[data-testid="stHeader"] {visibility: hidden !important; height: 0px !important;}
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    .stDeployButton, [data-testid="stDeployButton"], button[title*="Deploy"] {display: none !important; visibility: hidden !important;}
    
    section[data-testid="stSidebar"] {
        border-right: 1px solid #30363D;
        background-color: #12151D;
    }
    
    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 2rem !important;
    }

    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF4B4B 0%, #FF8533 50%, #FFD000 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 8px;
        background-color: #1E222D;
        color: #00E5FF;
        border: 1px solid #00E5FF33;
    }
    .badge-yt {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 8px;
        background-color: #2D1418;
        color: #FF4B4B;
        border: 1px solid #FF4B4B44;
    }
    .badge-opt {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
        background-color: #232733;
        color: #79FFE1;
        border: 1px solid #79FFE133;
    }
    .scene-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }
    .day-card {
        background-color: #131720;
        border: 1px solid #2B313E;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)


def load_queue():
    queue_file = config.OUTPUT_DIR / "publish_queue.json"
    if queue_file.exists():
        try:
            with open(queue_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def get_available_music_tracks():
    tracks = {"None": None}
    if config.MUSIC_DIR.exists():
        for p in sorted(config.MUSIC_DIR.glob("*.mp3")):
            name = p.stem.replace("_", " ").title()
            tracks[f"🎵 {name}"] = p
    return tracks


# Initialize Publishers
yt_pub = YouTubePublisher()
yt_status = yt_pub.is_configured()
has_meta_configured = bool(config.META_ACCESS_TOKEN and config.FACEBOOK_PAGE_ID)

# Sidebar Configuration
with st.sidebar:
    if has_custom_logo:
        st.image(str(config.LOGO_PATH), width=100)
    else:
        st.image("https://img.icons8.com/3d-fluency/94/video-editing.png", width=64)

    st.title("ND Reel Agent")
    st.caption("Auto AI Studio & Multi-Platform Publisher")

    # Platform Status Pills
    st.markdown("##### 🌐 Connected Platforms")
    pcol1, pcol2 = st.columns(2)
    with pcol1:
        if has_meta_configured:
            st.success("Meta / FB ✅")
        else:
            st.caption("Meta: Standby ⚠️")
    with pcol2:
        if yt_status["configured"]:
            st.success("YouTube ✅")
        else:
            st.caption("YouTube: Ready 📺")

    st.divider()
    st.subheader("🎙️ Voice & Sound")
    selected_voice_label = st.selectbox(
        "Default Voice Character",
        options=list(config.VOICE_OPTIONS.keys()),
        index=0
    )
    selected_voice_id = config.VOICE_OPTIONS[selected_voice_label]

    music_tracks = get_available_music_tracks()
    selected_music_label = st.selectbox("Background Track", list(music_tracks.keys()), index=1 if len(music_tracks) > 1 else 0)
    selected_music_path = music_tracks[selected_music_label]

    st.divider()
    st.subheader("🎨 Branding & Watermark")
    opt_watermark = st.checkbox("Overlay ND Reel Logo Watermark", value=has_custom_logo, help="Adds subtle branded watermark badge to protect your content.")

    st.divider()
    st.caption("ND Studio v2.4 • 9:16 Vertical UHD")


# Header Banner
st.markdown('<div class="main-title">🎬 ND AI Reel Studio & YouTube Shorts</div>', unsafe_allow_html=True)
st.markdown("""
<div style="margin-bottom: 1.2rem;">
    <span class="badge">🚀 3D Pixar & Animation</span>
    <span class="badge-yt">📺 YouTube Shorts</span>
    <span class="badge">📅 AI 7-Day Scheduler</span>
    <span class="badge">✨ 100% Automated</span>
</div>
""", unsafe_allow_html=True)

# Main Studio Tabs
tabs = st.tabs([
    "🚀 Instant Reel Studio",
    "📅 AI 7-Day Schedule Planner",
    "✍️ Poetry & Shayari Studio",
    "📚 Library & Publishing Queue",
    "🏷️ SEO & Hashtags",
    "⚙️ Channel Connections & Setup"
])


# ==========================================
# TAB 1: INSTANT REEL STUDIO
# ==========================================
with tabs[0]:
    st.subheader("✨ Generate Single Animated Reel / Short")
    st.caption("Create a viral 9:16 vertical video with 3D Pixar animation, dynamic camera motions, neural speech, and smart subtitles.")

    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        niche_options = [
            "Kids & Animated Mythology",
            "Devotional & Spiritual",
            "Motivation & Mindset",
            "Science & Space",
            "AI & Future Tech",
            "Dark History & Mysteries",
            "Psychology Facts",
            "Business & Wealth",
            "Custom Theme"
        ]
        
        c_niche, c_style = st.columns([0.5, 0.5])
        with c_niche:
            selected_niche = st.selectbox("Topic Niche", niche_options, index=0)
        with c_style:
            selected_style = st.selectbox("Visual Art Style", list(config.STYLE_PRESETS.keys()), index=0)

        default_prompts = {
            "Kids & Animated Mythology": "Bal Hanuman leaping to catch the golden sun thinking it is a delicious fruit — inspiring courage and strength for kids!",
            "Devotional & Spiritual": "श्रीमद्भगवद्गीता अध्याय 2 श्लोक 47: कर्मण्येवाधिकारस्ते मा फलेषु कदाचन — कर्म का असली रहस्य।",
            "Motivation & Mindset": "3 stoic rules to become emotionally untouchable and laser-focused.",
            "Science & Space": "The terrifying cosmic mystery of what happens inside a supermassive black hole event horizon.",
            "AI & Future Tech": "How humanoid robots will reshape daily human life by 2030.",
            "Dark History & Mysteries": "The ancient underground city of Derinkuyu that housed 20,000 people deep beneath the earth.",
            "Psychology Facts": "Subtle psychological signs that someone is lying right to your face.",
            "Business & Wealth": "How billionaire investors use asymmetry to make massive fortunes while risking almost nothing.",
            "Custom Theme": "Enter your custom topic here..."
        }

        user_prompt = st.text_area(
            "Topic / Storyline Description",
            value=default_prompts.get(selected_niche, ""),
            height=95
        )

        with st.expander("🎙️ Voice & Audio Settings", expanded=False):
            scol1, scol2 = st.columns(2)
            with scol1:
                tab_voice_label = st.selectbox("Speech Voice", options=list(config.VOICE_OPTIONS.keys()), index=0, key="t1_voice")
                t1_voice_id = config.VOICE_OPTIONS[tab_voice_label]
            with scol2:
                tab_music_tracks = get_available_music_tracks()
                t1_music_label = st.selectbox("Background Track", list(tab_music_tracks.keys()), index=1 if len(tab_music_tracks) > 1 else 0, key="t1_music")
                t1_music_path = tab_music_tracks[t1_music_label]

        with st.expander("🏷️ Custom Tags & Account Mentions", expanded=False):
            custom_tags_input = st.text_input("Custom Hashtags", value="#NDStudio, #Trending, #ViralShorts", key="t1_tags")
            custom_mentions_input = st.text_input("Account Mentions", value="@NDStudio", key="t1_mentions")

        with st.expander("📤 Multi-Platform Auto-Publishing", expanded=False):
            p_fb = st.checkbox("Auto-publish to Facebook Page", value=False, key="t1_autopost_fb")
            p_yt = st.checkbox("Auto-publish to YouTube Shorts", value=False, key="t1_autopost_yt")
            
            if p_yt:
                ycol1, ycol2 = st.columns(2)
                with ycol1:
                    yt_priv = st.selectbox("YouTube Privacy", ["public", "unlisted", "private"], index=0, key="t1_yt_priv")
                with ycol2:
                    is_kids_val = "kids" in selected_niche.lower() or "pixar" in selected_style.lower()
                    yt_kids = st.checkbox("Mark as Made for Kids", value=is_kids_val, key="t1_yt_kids")
            else:
                yt_priv = "public"
                yt_kids = False

        generate_btn = st.button("🚀 Generate 9:16 Animated Reel / Short", type="primary", use_container_width=True)

    with col2:
        st.subheader("📺 Video Preview")
        preview_placeholder = st.empty()
        cover_placeholder = st.empty()

    if generate_btn:
        if not user_prompt.strip():
            st.error("Please provide a prompt or topic for the reel.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(msg, pct):
                progress_bar.progress(pct)
                status_text.info(f"⏳ **{int(pct*100)}%** — {msg}")

            try:
                pipeline = ReelPipeline(
                    voice=t1_voice_id,
                    gemini_key=config.GEMINI_API_KEY,
                    groq_key=config.GROQ_API_KEY
                )

                result = pipeline.generate_full_reel(
                    prompt=user_prompt,
                    niche=selected_niche,
                    style=selected_style,
                    voice=t1_voice_id,
                    bg_music_path=t1_music_path,
                    custom_tags=custom_tags_input,
                    custom_mentions=custom_mentions_input,
                    enable_watermark=opt_watermark,
                    watermark_path=config.LOGO_PATH if opt_watermark else None,
                    auto_publish=p_fb,
                    auto_publish_youtube=p_yt,
                    youtube_privacy=yt_priv,
                    made_for_kids=yt_kids,
                    progress_callback=update_progress
                )

                status_text.success(f"🎉 Reel Generated in {result['elapsed_seconds']}s!")
                progress_bar.progress(1.0)

                video_file_path = result["video_path"]
                if Path(video_file_path).exists():
                    with open(video_file_path, "rb") as vf:
                        video_bytes = vf.read()
                        with col2:
                            preview_placeholder.video(video_bytes)
                            st.download_button(
                                label="⬇️ Download Reel (1080x1920 MP4)",
                                data=video_bytes,
                                file_name=Path(video_file_path).name,
                                mime="video/mp4",
                                use_container_width=True
                            )

                # Show Script & Metadata Breakdown
                st.subheader("📝 Script & Scene Breakdown")
                script_data = result["script_data"]

                meta_col1, meta_col2 = st.columns([1, 1])
                with meta_col1:
                    st.write("**Title:**", script_data.get("title", ""))
                    st.text_area("Caption & Tags", result["caption"], height=160, key="t1_cap_view")

                with meta_col2:
                    st.write("**Scene Breakdown:**")
                    for s in script_data.get("scenes", []):
                        st.markdown(f"""
                        <div class="scene-card">
                            <b>Scene {s.get('scene_id')}:</b> {s.get('narration')}<br>
                            <small style="color: #79FFE1;">🎨 Visual: {s.get('visual_prompt')}</small>
                        </div>
                        """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error generating reel: {e}")
                import traceback
                st.code(traceback.format_exc())


# ==========================================
# TAB 2: AI 7-DAY SCHEDULE PLANNER (PROMPT-DRIVEN)
# ==========================================
with tabs[1]:
    st.subheader("📅 AI 7-Day Content Scheduler & Prompt Manager")
    st.markdown("Give the AI any theme or instruction (e.g. *Lord Hanuman stories for kids*, *Cosmic space mysteries*, *High-energy motivation*), and it will automatically generate and program your complete 7-day schedule!")

    # Prompt-Based Schedule Generator
    st.markdown("### 🪄 Generate New 7-Day Schedule with AI")
    
    # Quick Preset Buttons
    st.write("##### ⚡ Quick Theme Presets:")
    qcol1, qcol2, qcol3, qcol4, qcol5 = st.columns(5)
    
    active_prompt_val = st.session_state.get("schedule_prompt_input", "Create a 7-day schedule about Lord Hanuman stories for kids with 3D Pixar animated visuals and inspiring moral lessons")

    if qcol1.button("🦸 Lord Hanuman for Kids"):
        active_prompt_val = "Create a 7-day schedule about Lord Hanuman adventure stories for kids with 3D Pixar animated visuals and inspiring moral lessons"
    if qcol2.button("🚀 Space & Cosmic"):
        active_prompt_val = "Create a 7-day schedule about mind-blowing mysteries of the universe, black holes, and space discoveries"
    if qcol3.button("⚡ Daily Motivation"):
        active_prompt_val = "Create a 7-day schedule of high-impact psychological and stoic rules to achieve unstoppable discipline and focus"
    if qcol4.button("🕉️ Sanatan Wisdom"):
        active_prompt_val = "Create a 7-day schedule of profound Bhagavad Gita wisdom and practical life lessons in Hindi"
    if qcol5.button("🧠 Psychology Facts"):
        active_prompt_val = "Create a 7-day schedule of fascinating human psychology facts and body language secrets"

    schedule_prompt_input = st.text_input(
        "Enter your command or theme to build your 7-day schedule:",
        value=active_prompt_val,
        key="schedule_prompt_input"
    )

    if st.button("✨ Generate 7-Day Schedule with AI", type="primary", use_container_width=True):
        with st.spinner("🤖 AI is designing your 7-day content plan..."):
            try:
                new_plan = WeeklyPlanner.generate_ai_schedule(schedule_prompt_input)
                st.success(f"🎉 7-Day Schedule generated and saved successfully for theme: '{schedule_prompt_input}'!")
            except Exception as se:
                st.error(f"Error generating schedule: {se}")

    st.divider()

    # View & Edit 7-Day Calendar
    st.markdown("### 🗓️ Active 7-Day Weekly Calendar")
    weekly_schedule = WeeklyPlanner.load_schedule()
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    current_day = datetime.now().strftime("%A")

    st.info(f"📆 **Today is {current_day}** — Scheduled Topic: *'{weekly_schedule.get(current_day, {}).get('topic', '')}'*")

    updated_schedule = {}

    for day in days_of_week:
        day_data = weekly_schedule.get(day, {})
        is_today = (day == current_day)
        
        day_header = f"🗓️ **{day}** {'✨ (TODAY)' if is_today else ''} — *{day_data.get('niche', 'General')}*"
        
        with st.expander(day_header, expanded=is_today):
            dcol1, dcol2 = st.columns([0.65, 0.35])
            
            with dcol1:
                t_val = st.text_area(f"Prompt / Storyline for {day}", value=day_data.get("topic", ""), height=90, key=f"topic_{day}")
            
            with dcol2:
                n_list = [
                    "Kids & Animated Mythology", "Devotional & Spiritual", "Motivation & Mindset",
                    "Science & Space", "AI & Future Tech", "Dark History & Mysteries", "Psychology Facts", "Business & Wealth"
                ]
                cur_niche = day_data.get("niche", "Kids & Animated Mythology")
                n_idx = n_list.index(cur_niche) if cur_niche in n_list else 0
                n_val = st.selectbox(f"Niche ({day})", n_list, index=n_idx, key=f"niche_{day}")

                s_list = list(config.STYLE_PRESETS.keys())
                cur_style = day_data.get("style", "3D Pixar / Disney Animation (Kids & Family)")
                s_idx = s_list.index(cur_style) if cur_style in s_list else 0
                s_val = st.selectbox(f"Style ({day})", s_list, index=s_idx, key=f"style_{day}")

                m_list = ["motivation", "suspense", "lofi", "cyberpunk", "none"]
                cur_m = day_data.get("music", "motivation")
                m_idx = m_list.index(cur_m) if cur_m in m_list else 0
                m_val = st.selectbox(f"Music ({day})", m_list, index=m_idx, key=f"music_{day}")

            updated_schedule[day] = {
                "niche": n_val,
                "topic": t_val,
                "style": s_val,
                "music": m_val,
                "voice": day_data.get("voice", config.DEFAULT_VOICE),
                "audience": day_data.get("audience", "General")
            }

    scol_save, scol_run = st.columns([0.6, 0.4])
    with scol_save:
        if st.button("💾 Save All Schedule Changes", type="primary", use_container_width=True):
            WeeklyPlanner.save_schedule(updated_schedule)
            st.success("✅ Weekly schedule saved successfully! Daily automation will use these exact prompts.")
    with scol_run:
        if st.button("⚡ Test-Run Today's Scheduled Reel Now", use_container_width=True):
            with st.spinner(f"Generating today's ({current_day}) reel..."):
                try:
                    today_info = WeeklyPlanner.get_todays_prompt(current_day)
                    pipe = ReelPipeline(voice=today_info.get("voice", config.DEFAULT_VOICE))
                    m_path = config.MUSIC_DIR / f"{today_info.get('music', 'motivation')}.mp3" if today_info.get("music") != "none" else None
                    
                    res = pipe.generate_full_reel(
                        prompt=today_info["topic"],
                        niche=today_info["niche"],
                        style=today_info.get("style", "3D Pixar / Disney Animation (Kids & Family)"),
                        bg_music_path=m_path
                    )
                    st.success(f"🎉 Created Today's Reel! Saved to: `{res['video_path']}`")
                except Exception as ex:
                    st.error(f"Error: {ex}")


# ==========================================
# TAB 3: POETRY & SHAYARI STUDIO
# ==========================================
with tabs[2]:
    st.subheader("✍️ Poetry, Shayari & Spoken Word Reel Studio")
    st.caption("Turn your original Hindi / English poetry, shayaris, and spoken words into cinematic 9:16 vertical reels.")

    pcol1, pcol2 = st.columns([1.1, 0.9])

    with pcol1:
        p_meta1, p_meta2 = st.columns([0.6, 0.4])
        with p_meta1:
            poet_author = st.text_input("Author / Poet Name", value="मनोज / ND Poetry", help="Your signature on the reel & caption.")
        with p_meta2:
            poem_lang = st.selectbox("Poem Language", ["Hindi (हिंदी)", "English", "Hinglish / Urdu"], index=0)

        p_style1, p_style2 = st.columns([0.5, 0.5])
        with p_style1:
            poem_mood = st.selectbox(
                "Poem Mood & Emotion",
                [
                    "Soulful & Emotional (भावुक व गहरा)",
                    "Melancholic & Heartbreak (दर्द व तन्हाई)",
                    "Romantic & Love (प्रेम व इश्क़)",
                    "Inspirational & Fierce (उत्साह व जुनून)",
                    "Nostalgic & Memories (यादें व बचपन)",
                    "Philosophical & Sufi (सूफ़ी व रूहानी)"
                ],
                index=0
            )
        with p_style2:
            poem_art_style = st.selectbox(
                "Visual Cinematic Art Style",
                [
                    "Cinematic 8K (सिनेमैटिक)",
                    "Moody Dark Rain & Vintage (बारिश व विंटेज)",
                    "Golden Hour & Sunset (सुनहरी शाम)",
                    "Starry Night & Ethereal (तारों भरी रात)",
                    "Misty Mountains & Solitude (पहाड़ व शांति)",
                    "Vintage Retro Film (रेट्रो फ़िल्म)"
                ],
                index=0
            )

        p_audio1, p_audio2 = st.columns([0.5, 0.5])
        with p_audio1:
            poetry_music_options = get_available_music_tracks()
            poem_selected_music = st.selectbox("Poetry Background Music", list(poetry_music_options.keys()), index=0, key="poem_music_select")
            poem_music_path = poetry_music_options[poem_selected_music]
        with p_audio2:
            poem_voice_label = st.selectbox("Recitation Voice", options=list(config.VOICE_OPTIONS.keys()), index=0, key="poem_voice_select")
            poem_voice_id = config.VOICE_OPTIONS[poem_voice_label]

        sample_poem = (
            "कभी कभी कुछ अल्फ़ाज़ खामोशियों में बेहतर लगते हैं,\n"
            "जैसे रेत पर लिखी दास्तानें हवाओं से संवरती हैं।\n"
            "रास्तों की तलाश में मंजिलें खुद ठहर गईं,\n"
            "जब हमने अपनी ही रूह से बातें करना सीख लिया।"
        )

        user_poem_text = st.text_area(
            "Paste or Type Your Poem / Lines Here:",
            value=sample_poem,
            height=130
        )

        generate_poetry_btn = st.button("🎬 Generate Cinematic Poetry Reel", type="primary", use_container_width=True)

    with pcol2:
        st.subheader("📺 Poetry Reel Preview")
        poem_preview_placeholder = st.empty()

    if generate_poetry_btn:
        if not user_poem_text.strip():
            st.error("Please enter your poem text before generating.")
        else:
            p_prog = st.progress(0)
            p_status = st.empty()

            def update_poem_prog(msg, pct):
                p_prog.progress(pct)
                p_status.info(f"⏳ **{int(pct*100)}%** — {msg}")

            try:
                pipeline = ReelPipeline(voice=poem_voice_id)
                poem_res = pipeline.generate_poetry_reel(
                    poem_text=user_poem_text,
                    author_name=poet_author,
                    mood=poem_mood,
                    language=poem_lang,
                    art_style=poem_art_style,
                    voice=poem_voice_id,
                    bg_music_path=poem_music_path,
                    enable_watermark=opt_watermark,
                    watermark_path=config.LOGO_PATH if opt_watermark else None,
                    progress_callback=update_poem_prog
                )

                p_status.success(f"🎉 Poetry Reel Created in {poem_res['elapsed_seconds']}s!")
                p_prog.progress(1.0)

                pv_path = poem_res["video_path"]
                if Path(pv_path).exists():
                    with open(pv_path, "rb") as pvf:
                        pv_bytes = pvf.read()
                        with pcol2:
                            poem_preview_placeholder.video(pv_bytes)
                            st.download_button(
                                label="⬇️ Download Poetry Reel (1080x1920 MP4)",
                                data=pv_bytes,
                                file_name=Path(pv_path).name,
                                mime="video/mp4",
                                use_container_width=True,
                                key="poem_download_btn"
                            )

            except Exception as pe:
                st.error(f"Error creating poetry reel: {pe}")


# ==========================================
# TAB 4: LIBRARY & PUBLISHING QUEUE
# ==========================================
with tabs[3]:
    st.subheader("📚 Generated Reels Library & Multi-Platform Publisher")
    queue = load_queue()

    if not queue:
        st.info("No generated reels found yet. Create your first reel above!")
    else:
        for item in queue:
            with st.expander(f"🎬 {item.get('title', 'Reel')} ({item.get('created_at', '')})", expanded=False):
                qcol1, qcol2 = st.columns([0.4, 0.6])
                vpath = item.get("video_path")

                with qcol1:
                    if vpath and Path(vpath).exists():
                        st.video(vpath)
                        with open(vpath, "rb") as f:
                            st.download_button(
                                "⬇️ Download MP4",
                                data=f.read(),
                                file_name=Path(vpath).name,
                                mime="video/mp4",
                                key=f"dl_{item['id']}"
                            )
                    else:
                        st.warning("Video file not found locally.")

                with qcol2:
                    st.write("**Title:**", item.get("title"))
                    st.text_area("Caption & Tags", item.get("caption", ""), height=110, key=f"cap_{item['id']}")
                    
                    st.write("**Direct Multi-Platform Publishing:**")
                    p_fb_col, p_yt_col = st.columns(2)
                    
                    with p_fb_col:
                        if st.button("📤 Post to Facebook Page", key=f"fb_{item['id']}", use_container_width=True):
                            pub = MetaPublisher()
                            res = pub.publish_facebook_reel(
                                video_path=Path(vpath),
                                caption=item.get("caption", ""),
                                title=item.get("title", ""),
                                allow_remixing=True
                            )
                            if res.get("success"):
                                st.success("✅ Published to Facebook Page!")
                            else:
                                st.error(f"Facebook: {res.get('error')}")

                    with p_yt_col:
                        if st.button("📺 Upload to YouTube Shorts", key=f"yt_{item['id']}", use_container_width=True):
                            yt = YouTubePublisher()
                            is_kids_val = "kids" in str(item.get("metadata", {}).get("niche", "")).lower()
                            res = yt.upload_short(
                                video_path=Path(vpath),
                                title=item.get("title", "Reel"),
                                description=item.get("caption", ""),
                                tags=item.get("hashtags", []),
                                privacy_status="public",
                                made_for_kids=is_kids_val
                            )
                            if res.get("success"):
                                st.success(f"✅ Published to YouTube Shorts! [View Video]({res.get('url')})")
                            else:
                                st.error(f"YouTube: {res.get('error')}")


# ==========================================
# TAB 5: SEO & TAGS
# ==========================================
with tabs[4]:
    st.subheader("🏷️ Algorithmic Tag & Setting Optimization")
    tcol1, tcol2 = st.columns([1, 1])

    with tcol1:
        st.write("### 📌 Niche Trending Hashtag Bundles")
        for niche, tag_list in TagOptimizer.NICHE_TAG_BUNDLES.items():
            with st.expander(f"📁 {niche} ({len(tag_list)} tags)"):
                for t in tag_list:
                    st.markdown(f'<span class="badge-opt">{t}</span>', unsafe_allow_html=True)

    with tcol2:
        st.write("### 🚀 YouTube Shorts & Meta Algorithm Rules")
        st.markdown("""
        1. **YouTube Shorts `#Shorts` Discovery**:
           - Placing `#Shorts` in both title and description pushes your video directly into the YouTube Shorts shelf.
        2. **3D Animation & Kids Engagement**:
           - Colorful, high-contrast 3D Pixar visuals increase viewer retention and completion rate by **250%**.
        3. **Fast Paced Hook (First 3 Seconds)**:
           - The video engine's 3D zoom and vibrant subtitles capture curiosity instantly.
        """)


# ==========================================
# TAB 6: CHANNEL CONNECTIONS & SETUP
# ==========================================
with tabs[5]:
    st.subheader("📘 Channel Connections & API Setup Guide")
    
    st.markdown("### 📺 YouTube Channel Integration (YouTube Shorts)")
    st.markdown("""
    To upload directly to your YouTube Channel:
    1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project.
    2. Enable the **YouTube Data API v3**.
    3. Go to **APIs & Services > Credentials > Create Credentials > OAuth client ID** (Desktop Application).
    4. Download the JSON file, rename it to `client_secret.json`, and place it in the project root (`e:\\nd reel\\client_secret.json`).
    5. When you click *Upload to YouTube Shorts*, a one-time browser login window will appear to grant permission, and your channel will stay authenticated automatically!
    """)

    st.divider()

    st.markdown("### 📘 Meta Graph API Configuration (Facebook & Instagram)")
    st.markdown(f"""
    Your connected Meta accounts:
    - **Facebook Page**: `ND Studio by NDTechHub` (`{config.FACEBOOK_PAGE_ID or 'Not Configured'}`)
    - **Instagram Account ID**: `{config.INSTAGRAM_ACCOUNT_ID or 'Not Configured'}`
    - **Access Token**: `{'Configured ✅' if config.META_ACCESS_TOKEN else 'Missing ❌'}`
    """)
