import time
from typing import List, Optional, Dict, Any
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
    Publishes to Facebook, Instagram, and YouTube Shorts according to configured daily times.
    """
    def __init__(self, voice: str = config.DEFAULT_VOICE):
        self.voice = voice
        self.pipeline = ReelPipeline(voice=voice)
        self.scheduler = BackgroundScheduler() if BackgroundScheduler else None

    def run_daily_job(self, day_name: Optional[str] = None) -> None:
        """Executes the daily automated reel generation matching today's weekly plan."""
        now = datetime.now()
        target_day = day_name or now.strftime("%A")
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        today_plan = WeeklyPlanner.get_todays_prompt(target_day)
        topic = today_plan["topic"]
        niche = today_plan["niche"]
        style = today_plan.get("style", "3D Pixar / Disney Animation (Kids & Family)")
        music_name = today_plan.get("music", "motivation")
        voice_id = today_plan.get("voice", config.DEFAULT_VOICE)
        scheduled_time = today_plan.get("time", "21:00")
        audience = today_plan.get("audience", "All")
        is_kids = (str(audience).strip().lower() == "kids only")

        music_file = config.MUSIC_DIR / f"{music_name}.mp3" if music_name != "none" else None

        print(f"\n==========================================")
        print(f"[Scheduler] Triggering scheduled Reel job at {now_str}")
        print(f"[Scheduler] Day            : {target_day}")
        print(f"[Scheduler] Scheduled Time : {scheduled_time}")
        print(f"[Scheduler] Audience       : {audience} (Made for Kids: {is_kids})")
        print(f"[Scheduler] Niche          : {niche}")
        print(f"[Scheduler] Style          : {style}")
        print(f"[Scheduler] Topic          : '{topic}'")
        print(f"==========================================\n")

        try:
            result = self.pipeline.generate_full_reel(
                prompt=topic,
                niche=niche,
                style=style,
                voice=voice_id,
                bg_music_path=music_file,
                auto_publish=True,
                auto_publish_youtube=True,
                made_for_kids=is_kids
            )
            print(f"[Scheduler] [SUCCESS] Daily reel completed! Saved to {result['video_path']}")
        except Exception as e:
            print(f"[Scheduler] [ERROR] Error in daily job: {e}")

    def start_weekly_schedule(self) -> None:
        """
        Schedules a dedicated daily job for each of the 7 days based on the exact
        configured schedule time in weekly_schedule.json.
        """
        if not self.scheduler:
            raise ImportError("APScheduler is not installed.")

        # Ensure scheduler is initialized
        if self.scheduler.running:
            self.scheduler.remove_all_jobs()
        else:
            self.scheduler.start()

        schedule = WeeklyPlanner.load_schedule()
        day_abbrs = {
            "Monday": "mon",
            "Tuesday": "tue",
            "Wednesday": "wed",
            "Thursday": "thu",
            "Friday": "fri",
            "Saturday": "sat",
            "Sunday": "sun"
        }

        registered = 0
        for day_name, day_data in schedule.items():
            time_str = day_data.get("time", "21:00")
            try:
                hour, minute = map(int, time_str.split(":"))
            except Exception:
                hour, minute = 21, 0

            day_code = day_abbrs.get(day_name, day_name[:3].lower())
            trigger = CronTrigger(day_of_week=day_code, hour=hour, minute=minute)

            self.scheduler.add_job(
                self.run_daily_job,
                trigger,
                args=[day_name],
                id=f"job_{day_name.lower()}",
                replace_existing=True
            )
            registered += 1
            print(f"[Scheduler] Registered {day_name} job at {hour:02d}:{minute:02d} ({day_code})")

        print(f"[Scheduler] [ACTIVE] 7-Day Weekly Scheduler started with {registered} scheduled day triggers.")

    def start_schedule(self, hour: int = 21, minute: int = 0) -> None:
        """Starts background daily scheduler at specified hour and minute (default 21:00 / 9:00 PM)."""
        if not self.scheduler:
            raise ImportError("APScheduler is not installed.")

        if not self.scheduler.running:
            self.scheduler.start()

        trigger = CronTrigger(hour=hour, minute=minute)
        self.scheduler.add_job(self.run_daily_job, trigger, id="daily_reel_job", replace_existing=True)
        print(f"[Scheduler] Daily Reel Agent is active! Scheduled daily at {hour:02d}:{minute:02d}.")

    def stop(self) -> None:
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self.scheduler = BackgroundScheduler() if BackgroundScheduler else None
            print("[Scheduler] Stopped scheduler.")

    def get_status(self) -> Dict[str, Any]:
        """Returns the current scheduler execution state and upcoming jobs."""
        if not self.scheduler:
            return {"available": False, "running": False, "jobs": []}

        is_running = self.scheduler.running
        jobs_info = []

        if is_running:
            for job in self.scheduler.get_jobs():
                next_time_str = job.next_run_time.strftime("%A, %b %d at %I:%M %p") if job.next_run_time else "N/A"
                jobs_info.append({
                    "id": job.id,
                    "next_run": next_time_str,
                    "raw_next_run": job.next_run_time
                })

            jobs_info.sort(key=lambda x: x["raw_next_run"] if x["raw_next_run"] else datetime.max)

        return {
            "available": True,
            "running": is_running,
            "jobs_count": len(jobs_info),
            "jobs": jobs_info,
            "next_job": jobs_info[0] if jobs_info else None
        }


# Singleton instance for in-process background scheduling
_global_scheduler_instance: Optional[ReelScheduler] = None


def get_global_scheduler() -> ReelScheduler:
    global _global_scheduler_instance
    if _global_scheduler_instance is None:
        _global_scheduler_instance = ReelScheduler()
    return _global_scheduler_instance


if __name__ == "__main__":
    scheduler = ReelScheduler()
    print("Testing manual run of daily job with today's weekly planner prompt...")
    scheduler.run_daily_job()
