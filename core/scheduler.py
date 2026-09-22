import time
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import config
from core.pipeline import ReelPipeline
from core.weekly_planner import WeeklyPlanner

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
except ImportError:
    BackgroundScheduler = None
    CronTrigger = None


class ReelScheduler:
    """
    Automated Daily Scheduler powered by the 7-Day Weekly Content Planner.
    """
    def __init__(self, voice: str = config.DEFAULT_VOICE):
        self.pipeline = ReelPipeline(voice=voice)
        self.scheduler = BackgroundScheduler() if BackgroundScheduler else None

    def run_daily_job(self) -> None:
        """Executes the daily automated reel generation matching today's weekly plan."""
        now = datetime.now()
        day_name = now.strftime("%A")
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        today_plan = WeeklyPlanner.get_todays_prompt(day_name)
        topic = today_plan["topic"]
        niche = today_plan["niche"]
        music_name = today_plan.get("music", "motivation")
        voice_id = today_plan.get("voice", config.DEFAULT_VOICE)

        music_file = config.MUSIC_DIR / f"{music_name}.mp3" if music_name != "none" else None

        print(f"\n==========================================")
        print(f"[Scheduler] Triggering daily Reel job at {now_str}")
        print(f"[Scheduler] Day   : {day_name}")
        print(f"[Scheduler] Niche : {niche}")
        print(f"[Scheduler] Topic : '{topic}'")
        print(f"==========================================\n")

        try:
            result = self.pipeline.generate_full_reel(
                prompt=topic,
                niche=niche,
                voice=voice_id,
                bg_music_path=music_file,
                auto_publish=True
            )
            print(f"[Scheduler] [SUCCESS] Daily reel completed! Saved to {result['video_path']}")
        except Exception as e:
            print(f"[Scheduler] [ERROR] Error in daily job: {e}")

    def start_schedule(self, hour: int = 21, minute: int = 0) -> None:
        """Starts background daily scheduler at specified hour and minute (default 21:00 / 9:00 PM)."""
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
    print("Testing manual run of daily job with today's weekly planner prompt...")
    scheduler.run_daily_job()
