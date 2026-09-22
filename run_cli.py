import argparse
import sys
from pathlib import Path

# Force UTF-8 on Windows Console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import config
from core.pipeline import ReelPipeline
from core.scheduler import ReelScheduler


def safe_print(text: str) -> None:
    """Print string safely without encoding crash on Windows."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "ignore").decode("ascii"))


def main():
    parser = argparse.ArgumentParser(description="Algorithm-Optimized AI Reel Generator (100% Free)")
    parser.add_argument("--prompt", "-p", type=str, help="Topic or prompt for the reel")
    parser.add_argument("--niche", "-n", type=str, default="General", help="Niche/category")
    parser.add_argument("--voice", "-v", type=str, default=config.DEFAULT_VOICE, help="Voice identifier")
    parser.add_argument("--music", "-m", type=str, default="motivation", help="Background music mood (suspense/motivation/lofi/cyberpunk/none)")
    parser.add_argument("--tags", "-t", type=str, default="#NDStudio, #NDTechHub, #Trending", help="Custom comma-separated hashtags")
    parser.add_argument("--mention", type=str, default="@NDTechHub", help="Custom account mention")
    parser.add_argument("--audio-name", type=str, default="Original Audio • ND Studio", help="Custom audio title for Instagram")
    parser.add_argument("--publish", action="store_true", help="Auto-publish to Meta Graph API")
    parser.add_argument("--schedule", action="store_true", help="Start background daily scheduler")
    parser.add_argument("--time", type=str, default="09:00", help="Daily schedule time (HH:MM format)")

    args = parser.parse_args()

    if args.schedule:
        try:
            hour, minute = map(int, args.time.split(":"))
        except Exception:
            hour, minute = 9, 0

        scheduler = ReelScheduler(voice=args.voice)
        scheduler.start_schedule(hour=hour, minute=minute)
        safe_print("Press Ctrl+C to exit scheduler.")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.stop()
            sys.exit(0)

    prompt = args.prompt or "Mind-Blowing Space Discoveries That Will Stun You"
    safe_print(f"\n[CLI] Starting Optimized AI Reel Generation for: '{prompt}'...")
    
    bg_music = None
    if args.music.lower() != "none":
        music_file = config.MUSIC_DIR / f"{args.music.lower()}.mp3"
        if music_file.exists():
            bg_music = music_file

    pipeline = ReelPipeline(voice=args.voice)
    result = pipeline.generate_full_reel(
        prompt=prompt,
        niche=args.niche,
        bg_music_path=bg_music,
        custom_tags=args.tags,
        custom_mentions=args.mention,
        audio_name=args.audio_name,
        share_to_feed=True,
        allow_remixing=True,
        auto_publish=args.publish
    )

    safe_print("\n==========================================")
    safe_print("[SUCCESS] REEL GENERATION COMPLETE!")
    safe_print(f"Video File  : {result['video_path']}")
    safe_print(f"Cover Frame : {result['cover_path']}")
    safe_print(f"Time Taken  : {result['elapsed_seconds']}s")
    safe_print(f"Hook Title  : {result['title']}")
    safe_print(f"Hashtags    : {' '.join(result['hashtags'])}")
    safe_print(f"\nOptimized Caption:\n{result['caption']}")
    safe_print("==========================================\n")


if __name__ == "__main__":
    main()
