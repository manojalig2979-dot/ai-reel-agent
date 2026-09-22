import time
from typing import List, Optional
from datetime import datetime
import config
from core.pipeline import ReelPipeline

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
except ImportError:
    BackgroundScheduler = None
    CronTrigger = None


class ReelScheduler:
    """
    Automated Daily Scheduler for generating and publishing reels on a recurring timer.
    """
    DEFAULT_TOPIC_ROTATION = [
        ("Mind-Blowing Space Secrets", "Science & Space"),
        ("Unstoppable Morning Mindset & Success Principles", "Motivation"),
        ("Future Technology & AI Breakthroughs You Didn't Know About", "Technology"),
        ("Untold Dark Mysteries of Ancient History", "History"),
        ("Psychological Tricks That Work Every Time", "Psychology & Life Hacks"),
        ("Millionaire Habits That Changed Everything", "Finance & Wealth"),
        ("Earth's Most Mysterious Unexplained Locations", "Nature & Wonders")
    ]

    def __init__(self, voice: str = config.DEFAULT_VOICE):
        self.pipeline = ReelPipeline(voice=voice)
        self.scheduler = BackgroundScheduler() if BackgroundScheduler else None
        self.topic_index = 0

    def run_daily_job(self) -> None:
        """Executes the daily automated reel generation."""
        topic, niche = self.DEFAULT_TOPIC_ROTATION[self.topic_index % len(self.DEFAULT_TOPIC_ROTATION)]
        self.topic_index += 1
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n==========================================")
        print(f"[Scheduler] Triggering daily Reel job at {now_str}")
        print(f"[Scheduler] Topic: '{topic}' | Niche: '{niche}'")
        print(f"==========================================\n")

        try:
            result = self.pipeline.generate_full_reel(
                prompt=topic,
                niche=niche,
                auto_publish=True
            )
            print(f"[Scheduler] [SUCCESS] Daily reel completed! Saved to {result['video_path']}")
        except Exception as e:
            print(f"[Scheduler] [ERROR] Error in daily job: {e}")

    def start_schedule(self, hour: int = 9, minute: int = 0) -> None:
        """Starts background daily scheduler at specified hour and minute."""
        if not self.scheduler:
            raise ImportError("APScheduler is not installed.")

        trigger = CronTrigger(hour=hour, minute=minute)
        self.scheduler.add_job(self.run_daily_job, trigger, id="daily_reel_job", replace_existing=True)
        self.scheduler.start()
        print(f"[Scheduler] Daily Reel Agent is active! Scheduled daily at {hour:02d}:{minute:02d}.")

    def stop(self) -> None:
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            print("[Scheduler] Stopped scheduler.")


if __name__ == "__main__":
    scheduler = ReelScheduler()
    print("Testing manual run of daily job...")
    scheduler.run_daily_job()
