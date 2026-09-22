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
    parser = argparse.ArgumentParser(description="Automated AI Reel Generator (100% Free)")
    parser.add_argument("--prompt", "-p", type=str, help="Topic or prompt for the reel")
    parser.add_argument("--niche", "-n", type=str, default="General", help="Niche/category")
    parser.add_argument("--voice", "-v", type=str, default=config.DEFAULT_VOICE, help="Voice identifier (e.g. en-US-ChristopherNeural)")
    parser.add_argument("--publish", action="store_true", help="Auto-publish to Meta Graph API")
    parser.add_argument("--schedule", action="store_true", help="Start background daily scheduler")
    parser.add_argument("--time", type=str, default="09:00", help="Daily schedule time in HH:MM format (default: 09:00)")

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
    safe_print(f"\n[CLI] Starting AI Reel Generation for: '{prompt}'...")
    pipeline = ReelPipeline(voice=args.voice)
    result = pipeline.generate_full_reel(
        prompt=prompt,
        niche=args.niche,
        auto_publish=args.publish
    )

    safe_print("\n==========================================")
    safe_print("[SUCCESS] REEL GENERATION COMPLETE!")
    safe_print(f"Video File: {result['video_path']}")
    safe_print(f"Time Taken: {result['elapsed_seconds']}s")
    safe_print(f"Title: {result['title']}")
    safe_print(f"Caption:\n{result['caption']}")
    safe_print("==========================================\n")


if __name__ == "__main__":
    main()
