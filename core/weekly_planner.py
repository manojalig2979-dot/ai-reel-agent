import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import config
from core.llm_engine import LLMEngine

SCHEDULE_FILE = config.BASE_DIR / "weekly_schedule.json"

DEFAULT_WEEKLY_PLAN = {
    "Monday": {
        "niche": "Kids & Animated Mythology",
        "topic": "Bal Hanuman and the Golden Sun — How young Hanuman leaped to catch the sun thinking it was a sweet fruit!",
        "style": "3D Pixar / Disney Animation (Kids & Family)",
        "music": "motivation",
        "voice": "hi-IN-MadhurNeural",
        "audience": "All",
        "time": "21:00"
    },
    "Tuesday": {
        "niche": "Kids & Animated Mythology",
        "topic": "Hanuman's Mighty Ocean Leap — Crossing the turbulent sea with fearless courage and devotion to Shri Ram!",
        "style": "3D Pixar / Disney Animation (Kids & Family)",
        "music": "motivation",
        "voice": "hi-IN-MadhurNeural",
        "audience": "All",
        "time": "21:00"
    },
    "Wednesday": {
        "niche": "Kids & Animated Mythology",
        "topic": "Lifting Mount Dronagiri — When Hanuman brought the entire Sanjeevani mountain to save Lakshman!",
        "style": "3D Pixar / Disney Animation (Kids & Family)",
        "music": "motivation",
        "voice": "hi-IN-SwaraNeural",
        "audience": "All",
        "time": "21:00"
    },
    "Thursday": {
        "niche": "Kids & Animated Mythology",
        "topic": "The Golden Lanka & Ring of Faith — How Hanuman met Mother Sita in Ashok Vatika and gave her hope!",
        "style": "3D Pixar / Disney Animation (Kids & Family)",
        "music": "lofi",
        "voice": "hi-IN-SwaraNeural",
        "audience": "All",
        "time": "21:00"
    },
    "Friday": {
        "niche": "Kids & Animated Mythology",
        "topic": "Hanuman's Heart of Devotion — The divine moment Hanuman showed Sita-Ram in his glowing heart!",
        "style": "3D Pixar / Disney Animation (Kids & Family)",
        "music": "motivation",
        "voice": "hi-IN-SwaraNeural",
        "audience": "All",
        "time": "21:00"
    },
    "Saturday": {
        "niche": "Kids & Animated Mythology",
        "topic": "Shani Dev and Hanuman's Protection — Why Hanuman protects everyone from fear and negativity!",
        "style": "3D Pixar / Disney Animation (Kids & Family)",
        "music": "suspense",
        "voice": "hi-IN-MadhurNeural",
        "audience": "All",
        "time": "21:00"
    },
    "Sunday": {
        "niche": "Kids & Animated Mythology",
        "topic": "The Superpower of Hanuman Chalisa for Kids — 3 lessons of strength, focus, and kindness for young champions!",
        "style": "3D Pixar / Disney Animation (Kids & Family)",
        "music": "motivation",
        "voice": "hi-IN-SwaraNeural",
        "audience": "All",
        "time": "21:00"
    }
}


class WeeklyPlanner:
    """
    Manages, schedules, and generates 7-day automated prompts, niches, visual styles, and audio settings.
    """

    @classmethod
    def load_schedule(cls) -> Dict[str, Dict[str, Any]]:
        plan = DEFAULT_WEEKLY_PLAN.copy()
        if SCHEDULE_FILE.exists():
            try:
                with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "Monday" in data:
                        for d, details in data.items():
                            if isinstance(details, dict):
                                details.setdefault("time", "21:00")
                                details.setdefault("audience", "All")
                        return data
            except Exception:
                pass
        return plan

    @classmethod
    def save_schedule(cls, schedule_data: Dict[str, Dict[str, Any]]) -> None:
        for day, details in schedule_data.items():
            if isinstance(details, dict):
                details.setdefault("time", "21:00")
                details.setdefault("audience", "All")
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(schedule_data, f, indent=2, ensure_ascii=False)
        print(f"[WeeklyPlanner] Saved weekly schedule to {SCHEDULE_FILE}")

    @classmethod
    def generate_ai_schedule(cls, prompt_instruction: str) -> Dict[str, Dict[str, Any]]:
        """
        Uses LLMEngine to generate a themed 7-day schedule based on user's instruction and saves it.
        """
        llm = LLMEngine()
        new_plan = llm.generate_custom_weekly_schedule(prompt_instruction)
        for day, details in new_plan.items():
            if isinstance(details, dict):
                details.setdefault("time", "21:00")
                details.setdefault("audience", "All")
        cls.save_schedule(new_plan)
        return new_plan

    @classmethod
    def get_todays_prompt(cls, day_name: Optional[str] = None) -> Dict[str, Any]:
        """Returns the configured prompt, visual style, schedule time, and audio settings for today."""
        if not day_name:
            day_name = datetime.now().strftime("%A")

        schedule = cls.load_schedule()
        today_data = schedule.get(day_name, DEFAULT_WEEKLY_PLAN.get(day_name, {
            "niche": "Kids & Animated Mythology",
            "topic": "Bal Hanuman adventure story for kids",
            "style": "3D Pixar / Disney Animation (Kids & Family)",
            "music": "motivation",
            "voice": config.DEFAULT_VOICE,
            "audience": "All",
            "time": "21:00"
        }))

        return {
            "day": day_name,
            "topic": today_data.get("topic"),
            "niche": today_data.get("niche", "Kids & Animated Mythology"),
            "style": today_data.get("style", "3D Pixar / Disney Animation (Kids & Family)"),
            "music": today_data.get("music", "motivation"),
            "voice": today_data.get("voice", config.DEFAULT_VOICE),
            "audience": today_data.get("audience", "Kids & Families"),
            "time": today_data.get("time", "21:00")
        }


if __name__ == "__main__":
    plan = WeeklyPlanner.get_todays_prompt()
    print("Today's Scheduled Prompt Plan:", plan)
