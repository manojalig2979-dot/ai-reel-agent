import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import config

SCHEDULE_FILE = config.BASE_DIR / "weekly_schedule.json"

DEFAULT_WEEKLY_PLAN = {
    "Monday": {
        "niche": "Motivation & Mindset",
        "topic": "3 stoic rules to become emotionally untouchable and laser-focused throughout the week",
        "music": "motivation",
        "voice": "en-US-ChristopherNeural"
    },
    "Tuesday": {
        "niche": "Science & Space",
        "topic": "The terrifying cosmic mystery of what happens inside a supermassive black hole event horizon",
        "music": "suspense",
        "voice": "en-US-ChristopherNeural"
    },
    "Wednesday": {
        "niche": "AI & Future Tech",
        "topic": "How humanoid AI robots and neural interfaces will reshape daily human life by 2030",
        "music": "cyberpunk",
        "voice": "en-US-GuyNeural"
    },
    "Thursday": {
        "niche": "Dark History & Mysteries",
        "topic": "The ancient underground city of Derinkuyu that housed 20,000 people deep beneath the earth",
        "music": "suspense",
        "voice": "en-US-ChristopherNeural"
    },
    "Friday": {
        "niche": "Psychology Facts",
        "topic": "5 subtle psychological tricks that instantly reveal if someone is lying right to your face",
        "music": "lofi",
        "voice": "en-US-JennyNeural"
    },
    "Saturday": {
        "niche": "Business & Wealth",
        "topic": "How top billionaire investors use asymmetry to generate massive wealth while risking almost nothing",
        "music": "motivation",
        "voice": "en-US-ChristopherNeural"
    },
    "Sunday": {
        "niche": "Science & Space",
        "topic": "The deepest unexplored ocean trenches that are more terrifying and mysterious than outer space",
        "music": "suspense",
        "voice": "en-US-ChristopherNeural"
    }
}


class WeeklyPlanner:
    """
    Manages and provides 7-day scheduled prompts, niches, and audio settings.
    """
    @classmethod
    def load_schedule(cls) -> Dict[str, Dict[str, str]]:
        if SCHEDULE_FILE.exists():
            try:
                with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_WEEKLY_PLAN.copy()

    @classmethod
    def save_schedule(cls, schedule_data: Dict[str, Dict[str, str]]) -> None:
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(schedule_data, f, indent=2, ensure_ascii=False)
        print(f"[WeeklyPlanner] Saved weekly schedule to {SCHEDULE_FILE}")

    @classmethod
    def get_todays_prompt(cls, day_name: Optional[str] = None) -> Dict[str, Any]:
        """Returns the configured prompt and settings for today (e.g. Tuesday)."""
        if not day_name:
            day_name = datetime.now().strftime("%A")

        schedule = cls.load_schedule()
        today_data = schedule.get(day_name, DEFAULT_WEEKLY_PLAN.get(day_name, {
            "niche": "General",
            "topic": "Mind-blowing daily discovery you never knew",
            "music": "motivation",
            "voice": config.DEFAULT_VOICE
        }))

        return {
            "day": day_name,
            "topic": today_data.get("topic"),
            "niche": today_data.get("niche", "General"),
            "music": today_data.get("music", "motivation"),
            "voice": today_data.get("voice", config.DEFAULT_VOICE)
        }


if __name__ == "__main__":
    plan = WeeklyPlanner.get_todays_prompt()
    print("Today's Scheduled Prompt Plan:", plan)
