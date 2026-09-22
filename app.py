import os
import json
import time
from pathlib import Path
import streamlit as st
import config
from core.pipeline import ReelPipeline
from core.publisher import MetaPublisher
from core.tag_engine import TagOptimizer

st.set_page_config(
    page_title="AI Reel Studio & Algorithmic Auto-Publisher",
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
    st.caption("Algorithm-Optimized AI Reel Generator")

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
    st.subheader("⚡ Meta Optimization Settings")
    opt_share_feed = st.checkbox("Instagram: Share to Main Feed Grid", value=True, help="Distributes video to both Reels tab and Profile Grid for 3x reach.")
    opt_allow_remix = st.checkbox("Facebook: Allow Remixing & Stitches", value=True, help="Allows audience to remix your video, heavily boosted by FB algorithm.")
    opt_audio_name = st.text_input("Custom Branded Audio Name", value="Original Audio • ND Studio")

    st.divider()
    st.subheader("📱 Meta API Accounts")
    fb_page_id_input = st.text_input("Facebook Page ID", value=config.FACEBOOK_PAGE_ID)
    ig_account_id_input = st.text_input("Instagram Account ID", value=config.INSTAGRAM_ACCOUNT_ID)
    meta_token_input = st.text_input("Meta Graph Access Token", value=config.META_ACCESS_TOKEN, type="password")


# Top Hero Header
st.markdown('<div class="main-title">🎬 AI Reel Studio & Algorithmic Auto-Publisher</div>', unsafe_allow_html=True)
st.markdown("""
<div>
    <span class="badge">🚀 100% Free Tier</span>
    <span class="badge">🎙️ Neural Voiceover</span>
    <span class="badge">🎵 Background Ducking</span>
    <span class="badge">🏷️ Smart Tag Optimizer</span>
    <span class="badge">⚡ Algorithm Max Reach</span>
</div>
""", unsafe_allow_html=True)

st.write("")

tabs = st.tabs(["✨ Generate New Reel", "🏷️ Tags & Optimization", "📁 Video Library & Queue", "📘 Meta Setup Guide"])

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
            height=110
        )

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


# TAB 2: TAGS & OPTIMIZATION SETTINGS
with tabs[1]:
    st.subheader("🏷️ Algorithmic Tag & Setting Optimization")
    st.markdown("These settings ensure your reels are favored by Meta's recommendation algorithms for maximum reach.")

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
        1. **Share to Main Feed Grid (`share_to_feed=true`)**:
           - Reels shared to the main feed receive up to **300% more impressions** from current followers in the first 2 hours.
        2. **Allow Remixing (`enable_remixing=true`)**:
           - Facebook prioritizes videos that allow users to create remixes, stitches, and duets.
        3. **Custom Branded Audio (`audio_name`)**:
           - Naming your audio (e.g. *Original Audio • ND Studio*) allows other creators to click and use your sound, creating a viral snowball effect.
        4. **Cover Frame Thumbnails**:
           - The agent automatically extracts a vibrant frame from 1.0s to avoid black first-frame thumbnails.
        5. **Balanced Tagging**:
           - The optimizer mixes **broad viral tags** (`#viralreels`, `#explorepage`) with **specific micro-niche tags** for targeted viewer retention.
        """)


# TAB 3: LIBRARY & QUEUE
with tabs[2]:
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


# TAB 4: META API SETUP GUIDE
with tabs[3]:
    st.subheader("📘 Meta Graph API Configuration")
    st.markdown(f"""
    Your current connected accounts:
    - **Facebook Page ID**: `{config.FACEBOOK_PAGE_ID}`
    - **Instagram Account ID**: `{config.INSTAGRAM_ACCOUNT_ID}`
    - **Access Token**: `{'Configured ✅' if config.META_ACCESS_TOKEN else 'Missing ❌'}`
    """)
