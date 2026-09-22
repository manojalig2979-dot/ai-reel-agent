import os
import json
import time
from pathlib import Path
import streamlit as st
import config
from core.pipeline import ReelPipeline
from core.publisher import MetaPublisher

st.set_page_config(
    page_title="Free AI Reel Generator & Auto-Publisher",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 2.4rem;
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
    .scene-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
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
    st.image("https://img.icons8.com/3d-fluency/94/video-editing.png", width=64)
    st.title("Agent Settings")
    st.caption("100% Free AI Reel Generator")

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
    st.subheader("🔑 API Keys (Optional)")
    st.info("No paid keys needed! Free AI script generation and local rendering are active by default.")
    
    gemini_key_input = st.text_input("Google Gemini API Key (Free)", value=config.GEMINI_API_KEY, type="password")
    groq_key_input = st.text_input("Groq API Key (Free)", value=config.GROQ_API_KEY, type="password")

    st.divider()
    st.subheader("📱 Meta Publishing")
    meta_token_input = st.text_input("Meta Graph Access Token", value=config.META_ACCESS_TOKEN, type="password")
    fb_page_id_input = st.text_input("Facebook Page ID", value=config.FACEBOOK_PAGE_ID)
    ig_account_id_input = st.text_input("Instagram Account ID", value=config.INSTAGRAM_ACCOUNT_ID)


# Top Hero Header
st.markdown('<div class="main-title">🎬 AI Reel Studio & Auto-Publisher</div>', unsafe_allow_html=True)
st.markdown("""
<div>
    <span class="badge">🚀 100% Free Tier</span>
    <span class="badge">🎙️ Microsoft Neural TTS</span>
    <span class="badge">🖼️ 9:16 Vertical AI Visuals</span>
    <span class="badge">🎵 Background Music Ducking</span>
    <span class="badge">📱 Instagram & Facebook Ready</span>
</div>
""", unsafe_allow_html=True)

st.write("")

tabs = st.tabs(["✨ Generate New Reel", "📁 Video Library & Queue", "📘 Meta API Setup Guide"])

# TAB 1: GENERATE NEW REEL
with tabs[0]:
    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        st.subheader("💡 Video Concept & Prompt")
        
        niche_options = [
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
            height=120
        )

        auto_post = st.checkbox("Auto-publish to Facebook/Instagram upon completion", value=False)

        generate_btn = st.button("🚀 Generate 9:16 Reel Now", type="primary", use_container_width=True)

    with col2:
        st.subheader("📺 Video Preview")
        preview_placeholder = st.empty()
        status_box = st.empty()

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
                    gemini_key=gemini_key_input,
                    groq_key=groq_key_input
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
                st.subheader("📝 Generated Script & Social Copy")
                script_data = result["script_data"]

                meta_col1, meta_col2 = st.columns([1, 1])
                with meta_col1:
                    st.write("**Title:**", script_data.get("title", ""))
                    st.write("**Caption & Hashtags:**")
                    st.text_area("Caption", result["caption"], height=120)

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


# TAB 2: LIBRARY & QUEUE
with tabs[1]:
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
                    st.text_area("Caption", item.get("caption", ""), height=100, key=f"cap_{item['id']}")
                    
                    st.write("**Direct Publishing:**")
                    p1, p2 = st.columns(2)
                    with p1:
                        if st.button("📤 Post to Facebook", key=f"fb_{item['id']}"):
                            pub = MetaPublisher(access_token=meta_token_input, facebook_page_id=fb_page_id_input)
                            res = pub.publish_facebook_reel(Path(vpath), item.get("caption", ""))
                            if res.get("success"):
                                st.success("Published to Facebook Page!")
                            else:
                                st.error(res.get("error"))
                    with p2:
                        st.info("For Instagram, upload video to public URL or use Meta Graph Container.")


# TAB 3: META API SETUP GUIDE
with tabs[2]:
    st.subheader("📘 100% Free Meta Graph API Setup Guide")
    st.markdown("""
    You can publish directly to Instagram Reels and Facebook Pages for free using the official Meta Graph API:

    #### Step 1: Create a Meta for Developers Account (Free)
    1. Go to [developers.facebook.com](https://developers.facebook.com) and log in with your Facebook account.
    2. Click **Create App** ➔ Select **Business** or **Other** ➔ Choose **Instagram Graph API** and **Facebook Graph API**.

    #### Step 2: Link Facebook Page and Instagram Account
    1. Create a Facebook Page (e.g., *My Daily Reels*).
    2. In your Instagram App Settings, switch your Instagram account to **Professional / Creator Account**.
    3. Link your Instagram Account to your Facebook Page in Page Settings.

    #### Step 3: Generate Access Token
    1. Go to the [Graph API Explorer](https://developers.facebook.com/tools/explorer/).
    2. Select your App and grant the following permissions:
       - `pages_show_list`
       - `pages_read_engagement`
       - `pages_manage_posts`
       - `instagram_basic`
       - `instagram_content_publish`
    3. Click **Generate Access Token** and copy it into the sidebar or `.env` file (`META_ACCESS_TOKEN`).

    #### Step 4: Add IDs to `.env`
    - `INSTAGRAM_ACCOUNT_ID`: Your Instagram Business Account ID.
    - `FACEBOOK_PAGE_ID`: Your Facebook Page ID.
    """)
