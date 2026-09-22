import os
import json
import time
from pathlib import Path
from datetime import datetime
import streamlit as st
import config
from core.pipeline import ReelPipeline
from core.publisher import MetaPublisher
from core.tag_engine import TagOptimizer
from core.weekly_planner import WeeklyPlanner

# Check if custom logo exists
has_custom_logo = config.LOGO_PATH.exists()

st.set_page_config(
    page_title="ND Reel Studio & 7-Day Auto-Publisher",
    page_icon=str(config.LOGO_PATH) if has_custom_logo else "🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Desktop & Studio App
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    #MainMenu {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    header[data-testid="stHeader"] {visibility: hidden !important; height: 0px !important;}
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    .stDeployButton, [data-testid="stDeployButton"], button[title*="Deploy"] {display: none !important; visibility: hidden !important;}
    
    /* Ensure sidebar is prominent, clean, and never permanently hidden */
    section[data-testid="stSidebar"] {
        border-right: 1px solid #30363D;
        background-color: #12151D;
    }
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 2.3rem;
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


# Sidebar Configuration
with st.sidebar:
    if has_custom_logo:
        st.image(str(config.LOGO_PATH), width=100)
    else:
        st.image("https://img.icons8.com/3d-fluency/94/video-editing.png", width=64)

    st.title("ND Reel Agent")
    st.caption("7-Day Automated AI Studio")

    st.subheader("🎙️ Voice Settings")
    selected_voice_label = st.selectbox(
        "Voice Character",
        options=list(config.VOICE_OPTIONS.keys()),
        index=0
    )
    selected_voice_id = config.VOICE_OPTIONS[selected_voice_label]

    st.divider()
    st.subheader("🎵 Background Music")
    music_tracks = get_available_music_tracks()
    selected_music_label = st.selectbox("Audio Track", list(music_tracks.keys()), index=1 if len(music_tracks) > 1 else 0)
    selected_music_path = music_tracks[selected_music_label]

    st.divider()
    st.subheader("🎨 Branding & Watermark")
    opt_watermark = st.checkbox("Overlay ND Reel Logo Watermark", value=has_custom_logo, help="Adds subtle branded watermark badge to protect your content.")

    st.divider()
    st.subheader("⚡ Meta Optimization Settings")
    opt_share_feed = st.checkbox("Instagram: Share to Main Feed Grid", value=True)
    opt_allow_remix = st.checkbox("Facebook: Allow Remixing & Stitches", value=True)
    opt_audio_name = st.text_input("Custom Branded Audio Name", value="Original Audio • ND Studio")

    st.divider()
    st.subheader("📱 Meta API Accounts")
    fb_page_id_input = st.text_input("Facebook Page ID", value=config.FACEBOOK_PAGE_ID)
    ig_account_id_input = st.text_input("Instagram Account ID", value=config.INSTAGRAM_ACCOUNT_ID)
    meta_token_input = st.text_input("Meta Graph Access Token", value=config.META_ACCESS_TOKEN, type="password")


# Top Hero Header
hcol1, hcol2 = st.columns([0.15, 0.85])
with hcol1:
    if has_custom_logo:
        st.image(str(config.LOGO_PATH), width=80)
with hcol2:
    st.markdown('<div class="main-title">🎬 ND Reel Studio & 7-Day Auto-Publisher</div>', unsafe_allow_html=True)
    st.markdown("""
    <div>
        <span class="badge">🚀 100% Free Tier</span>
        <span class="badge">📅 7-Day Content Plan</span>
        <span class="badge">🎙️ Neural Voiceover</span>
        <span class="badge">🎵 Music Ducking</span>
        <span class="badge">🎨 ND Branding</span>
    </div>
    """, unsafe_allow_html=True)

st.write("")

tabs = st.tabs(["✨ Generate Reel", "✍️ Poetry & Writings", "📅 7-Day Weekly Planner", "🏷️ Tags & Optimization", "📁 Video Library", "📘 Meta Setup"])

# TAB 1: GENERATE NEW REEL
with tabs[0]:
    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        st.subheader("💡 Video Concept & Prompt")
        
        niche_options = [
            "Bhagavad Gita & Spirituality",
            "Science & Space",
            "Motivation & Mindset",
            "AI & Future Tech",
            "Dark History & Mysteries",
            "Psychology Facts",
            "Business & Wealth",
            "Custom Theme"
        ]
        selected_niche = st.selectbox("Select Niche / Category", niche_options)

        default_prompts = {
            "Bhagavad Gita & Spirituality": "श्रीमद्भगवद्गीता अध्याय 2 श्लोक 47: कर्मण्येवाधिकारस्ते मा फलेषु कदाचन। कर्म का असली रहस्य।",
            "Science & Space": "The terrifying truth about what happens if you fall into a supermassive black hole.",
            "Motivation & Mindset": "3 stoic rules to become emotionally untouchable and laser-focused.",
            "AI & Future Tech": "How humanoid robots are about to change daily human life forever.",
            "Dark History & Mysteries": "The mysterious ancient underground city of Derinkuyu that housed 20,000 people.",
            "Psychology Facts": "Subtle psychological signs that someone is lying right to your face.",
            "Business & Wealth": "How billionaire investors use asymmetry to make massive fortunes while risking almost nothing.",
            "Custom Theme": "Enter your custom topic here..."
        }

        user_prompt = st.text_area(
            "Topic / Prompt Description",
            value=default_prompts.get(selected_niche, ""),
            height=110
        )

        with st.expander("🎙️ Voice & Background Music Settings", expanded=False):
            scol1, scol2 = st.columns(2)
            with scol1:
                tab_voice_label = st.selectbox("Speech Voice", options=list(config.VOICE_OPTIONS.keys()), index=0, key="tab_voice_select")
                selected_voice_id = config.VOICE_OPTIONS[tab_voice_label]
            with scol2:
                tab_music_tracks = get_available_music_tracks()
                tab_music_label = st.selectbox("Background Track", list(tab_music_tracks.keys()), index=1 if len(tab_music_tracks) > 1 else 0, key="tab_music_select")
                selected_music_path = tab_music_tracks[tab_music_label]

        with st.expander("🏷️ Custom Tags & Account Mentions", expanded=False):
            custom_tags_input = st.text_input("Custom Hashtags (comma separated)", value="#NDStudio, #NDTechHub, #Trending")
            custom_mentions_input = st.text_input("Account Mentions (comma separated)", value="@NDTechHub")

        auto_post = st.checkbox("Auto-publish to Facebook Page upon completion", value=False)

        generate_btn = st.button("🚀 Generate 9:16 Reel Now", type="primary", use_container_width=True)

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
                    voice=selected_voice_id,
                    gemini_key=config.GEMINI_API_KEY,
                    groq_key=config.GROQ_API_KEY
                )

                if meta_token_input:
                    pipeline.publisher.access_token = meta_token_input
                if fb_page_id_input:
                    pipeline.publisher.fb_page_id = fb_page_id_input
                if ig_account_id_input:
                    pipeline.publisher.ig_account_id = ig_account_id_input

                result = pipeline.generate_full_reel(
                    prompt=user_prompt,
                    niche=selected_niche,
                    voice=selected_voice_id,
                    bg_music_path=selected_music_path,
                    custom_tags=custom_tags_input,
                    custom_mentions=custom_mentions_input,
                    enable_watermark=opt_watermark,
                    watermark_path=config.LOGO_PATH if opt_watermark else None,
                    audio_name=opt_audio_name,
                    share_to_feed=opt_share_feed,
                    allow_remixing=opt_allow_remix,
                    auto_publish=auto_post,
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
                st.subheader("📝 Optimized Caption & Tags")
                script_data = result["script_data"]

                meta_col1, meta_col2 = st.columns([1, 1])
                with meta_col1:
                    st.write("**Hook Title:**", script_data.get("title", ""))
                    st.write("**SEO Description & Tags:**")
                    st.text_area("Caption", result["caption"], height=160)

                with meta_col2:
                    st.write("**Scene Breakdown:**")
                    for s in script_data.get("scenes", []):
                        st.markdown(f"""
                        <div class="scene-card">
                            <b>Scene {s.get('scene_id')}:</b> {s.get('narration')}<br>
                            <small style="color: #8B949E;">🖼️ Visual: {s.get('visual_prompt')}</small>
                        </div>
                        """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error generating reel: {e}")
                import traceback
                st.code(traceback.format_exc())


# TAB 2: POETRY & PERSONAL WRITINGS (Dedicated Isolated Section)
with tabs[1]:
    st.subheader("✍️ Poetry, Shayari & Spoken Word Reel Studio")
    st.caption("Turn your original Hindi / English poetry, shayaris, and spoken words into cinematic 9:16 vertical reels.")

    pcol1, pcol2 = st.columns([1.1, 0.9])

    with pcol1:
        st.write("### 🖋️ Your Original Poem / Writing")

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
            "Paste or Type Your Poem / Lines Here (Each stanza becomes a cinematic visual scene):",
            value=sample_poem,
            height=140
        )

        poem_auto_post = st.checkbox("Auto-publish to Facebook upon completion", value=False, key="poem_autopost")

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
                pipeline = ReelPipeline(
                    voice=poem_voice_id,
                    gemini_key=config.GEMINI_API_KEY,
                    groq_key=config.GROQ_API_KEY
                )

                if meta_token_input:
                    pipeline.publisher.access_token = meta_token_input
                if fb_page_id_input:
                    pipeline.publisher.fb_page_id = fb_page_id_input
                if ig_account_id_input:
                    pipeline.publisher.ig_account_id = ig_account_id_input

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
                    share_to_feed=opt_share_feed,
                    allow_remixing=opt_allow_remix,
                    auto_publish=poem_auto_post,
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

                st.subheader("📝 Poetry Caption & Scene Breakdown")
                p_script = poem_res["script_data"]
                p_m1, p_m2 = st.columns([1, 1])
                with p_m1:
                    st.write("**Title:**", p_script.get("title", ""))
                    st.text_area("Poetry Caption & Hashtags", poem_res["caption"], height=160, key="poem_cap_view")
                with p_m2:
                    st.write("**Stanza Scenes:**")
                    for s in p_script.get("scenes", []):
                        st.markdown(f"""
                        <div class="scene-card">
                            <b>Stanza {s.get('scene_id')}:</b> {s.get('narration')}<br>
                            <small style="color: #79FFE1;">🎨 AI Visual Prompt: {s.get('visual_prompt')}</small>
                        </div>
                        """, unsafe_allow_html=True)

            except Exception as pe:
                st.error(f"Error creating poetry reel: {pe}")
                import traceback
                st.code(traceback.format_exc())


# TAB 3: 7-DAY WEEKLY PLANNER
with tabs[2]:
    st.subheader("📅 7-Day Weekly Content Calendar")
    st.markdown("Configure your prompts for Monday through Sunday. The agent will automatically generate and post each day's topic at **09:00 PM**!")

    weekly_schedule = WeeklyPlanner.load_schedule()
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    current_day = datetime.now().strftime("%A")

    today_box = st.info(f"📆 **Today is {current_day}** — Scheduled Topic: *'{weekly_schedule.get(current_day, {}).get('topic', '')}'*")

    updated_schedule = {}

    for day in days_of_week:
        day_data = weekly_schedule.get(day, {})
        is_today = (day == current_day)
        
        day_header = f"🗓️ **{day}** {'✨ (TODAY)' if is_today else ''}"
        
        with st.expander(day_header, expanded=is_today):
            dcol1, dcol2 = st.columns([0.7, 0.3])
            
            with dcol1:
                t_val = st.text_area(f"Prompt / Topic for {day}", value=day_data.get("topic", ""), height=80, key=f"topic_{day}")
            
            with dcol2:
                n_val = st.selectbox(
                    f"Niche ({day})",
                    ["Science & Space", "Motivation & Mindset", "AI & Future Tech", "Dark History & Mysteries", "Psychology Facts", "Business & Wealth"],
                    index=max(0, ["Science & Space", "Motivation & Mindset", "AI & Future Tech", "Dark History & Mysteries", "Psychology Facts", "Business & Wealth"].index(day_data.get("niche", "Science & Space")) if day_data.get("niche") in ["Science & Space", "Motivation & Mindset", "AI & Future Tech", "Dark History & Mysteries", "Psychology Facts", "Business & Wealth"] else 0),
                    key=f"niche_{day}"
                )
                m_val = st.selectbox(
                    f"Music ({day})",
                    ["suspense", "motivation", "lofi", "cyberpunk", "none"],
                    index=max(0, ["suspense", "motivation", "lofi", "cyberpunk", "none"].index(day_data.get("music", "motivation")) if day_data.get("music") in ["suspense", "motivation", "lofi", "cyberpunk", "none"] else 1),
                    key=f"music_{day}"
                )

            updated_schedule[day] = {
                "niche": n_val,
                "topic": t_val,
                "music": m_val,
                "voice": day_data.get("voice", config.DEFAULT_VOICE)
            }

    if st.button("💾 Save 7-Day Weekly Schedule", type="primary", use_container_width=True):
        WeeklyPlanner.save_schedule(updated_schedule)
        st.success("✅ Weekly schedule saved successfully! Your daily 9:00 PM automation will now use these prompts.")


# TAB 4: TAGS & OPTIMIZATION SETTINGS
with tabs[3]:
    st.subheader("🏷️ Algorithmic Tag & Setting Optimization")
    tcol1, tcol2 = st.columns([1, 1])

    with tcol1:
        st.write("### 📌 Niche Trending Hashtag Bundles")
        for niche, tag_list in TagOptimizer.NICHE_TAG_BUNDLES.items():
            with st.expander(f"📁 {niche} ({len(tag_list)} tags)"):
                for t in tag_list:
                    st.markdown(f'<span class="badge-opt">{t}</span>', unsafe_allow_html=True)

    with tcol2:
        st.write("### 🚀 Best Practices for Meta Reels Algorithm")
        st.markdown("""
        1. **Creator Watermark / Branding**:
           - Meta **rewards** original creator badges like your ND logo watermark.
        2. **Share to Main Feed Grid (`share_to_feed=true`)**:
           - Reels shared to the main feed receive up to **300% more impressions**.
        3. **Allow Remixing (`enable_remixing=true`)**:
           - Facebook prioritizes videos that allow users to create remixes and stitches.
        """)


# TAB 5: LIBRARY & QUEUE
with tabs[4]:
    st.subheader("📚 Generated Reels Library")
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
                    st.write("**Caption:**")
                    st.text_area("Caption", item.get("caption", ""), height=120, key=f"cap_{item['id']}")
                    
                    st.write("**Direct Publishing:**")
                    p1, p2 = st.columns(2)
                    with p1:
                        if st.button("📤 Post to Facebook Page", key=f"fb_{item['id']}"):
                            pub = MetaPublisher(access_token=meta_token_input, facebook_page_id=fb_page_id_input)
                            res = pub.publish_facebook_reel(
                                video_path=Path(vpath),
                                caption=item.get("caption", ""),
                                title=item.get("title", ""),
                                allow_remixing=True
                            )
                            if res.get("success"):
                                st.success("✅ Successfully published to Facebook Page!")
                            else:
                                st.error(f"Failed: {res.get('error')}")
                    with p2:
                        st.info("Instagram publishing container active via Graph API.")


# TAB 6: META API SETUP GUIDE
with tabs[5]:
    st.subheader("📘 Meta Graph API Configuration")
    st.markdown(f"""
    Your connected accounts:
    - **Facebook Page**: `ND Studio by NDTechHub` (`{config.FACEBOOK_PAGE_ID}`)
    - **Instagram Account ID**: `{config.INSTAGRAM_ACCOUNT_ID}`
    - **Access Token**: `{'Configured ✅' if config.META_ACCESS_TOKEN else 'Missing ❌'}`
    """)
