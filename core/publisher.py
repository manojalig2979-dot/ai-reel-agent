import os
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
import requests
import config


class MetaPublisher:
    """
    Automated Publisher for Instagram Reels and Facebook Pages via Meta Graph API.
    Supports official Graph API (Free) and local export queue mode.
    """
    def __init__(
        self,
        access_token: Optional[str] = None,
        instagram_account_id: Optional[str] = None,
        facebook_page_id: Optional[str] = None,
        api_version: str = "v19.0"
    ):
        self.access_token = access_token or config.META_ACCESS_TOKEN
        self.ig_account_id = instagram_account_id or config.INSTAGRAM_ACCOUNT_ID
        self.fb_page_id = facebook_page_id or config.FACEBOOK_PAGE_ID
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def is_configured(self) -> Dict[str, bool]:
        """Check which platforms are ready for direct publishing."""
        return {
            "instagram": bool(self.access_token and self.ig_account_id),
            "facebook": bool(self.access_token and self.fb_page_id)
        }

    def publish_instagram_reel(
        self,
        video_url: str,
        caption: str,
        cover_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publishes a vertical Reel to Instagram via Graph API.
        Note: Meta API requires video to be hosted on a public HTTPS URL (e.g. S3, Supabase, Cloudinary, or ngrok).
        """
        if not self.access_token or not self.ig_account_id:
            return {
                "success": False,
                "error": "Missing Instagram Account ID or Meta Access Token. Configure them in .env"
            }

        print(f"[MetaPublisher] Initializing Instagram Reel container on account: {self.ig_account_id}...")
        
        # 1. Create Media Container
        init_url = f"{self.base_url}/{self.ig_account_id}/media"
        params = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": self.access_token
        }
        if cover_url:
            params["cover_url"] = cover_url

        try:
            res = requests.post(init_url, data=params, timeout=30)
            res_json = res.json()
            if "id" not in res_json:
                return {"success": False, "error": f"Failed to create media container: {res_json}"}

            container_id = res_json["id"]
            print(f"[MetaPublisher] Container created ID: {container_id}. Waiting for processing...")

            # 2. Poll container status until ready
            status_url = f"{self.base_url}/{container_id}"
            max_attempts = 30
            for attempt in range(max_attempts):
                time.sleep(5)
                check_res = requests.get(
                    status_url,
                    params={"fields": "status_code", "access_token": self.access_token},
                    timeout=15
                ).json()
                
                status_code = check_res.get("status_code")
                print(f"[MetaPublisher] Status check {attempt+1}/{max_attempts}: {status_code}")

                if status_code == "FINISHED":
                    break
                elif status_code == "ERROR":
                    return {"success": False, "error": f"Instagram container processing failed: {check_res}"}
            else:
                return {"success": False, "error": "Instagram container processing timed out."}

            # 3. Publish Media Container
            publish_url = f"{self.base_url}/{self.ig_account_id}/media_publish"
            pub_res = requests.post(
                publish_url,
                data={"creation_id": container_id, "access_token": self.access_token},
                timeout=30
            ).json()

            if "id" in pub_res:
                print(f"[MetaPublisher] Successfully published Instagram Reel! Post ID: {pub_res['id']}")
                return {"success": True, "platform": "instagram", "post_id": pub_res["id"]}
            else:
                return {"success": False, "error": f"Publishing failed: {pub_res}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def publish_facebook_reel(
        self,
        video_path: Path,
        caption: str
    ) -> Dict[str, Any]:
        """
        Publishes a Reel directly to a Facebook Page.
        """
        if not self.access_token or not self.fb_page_id:
            return {
                "success": False,
                "error": "Missing Facebook Page ID or Meta Access Token."
            }

        print(f"[MetaPublisher] Starting Facebook Page Reel upload to Page: {self.fb_page_id}...")

        # 1. Initialize Reel Upload Session
        init_url = f"{self.base_url}/{self.fb_page_id}/video_reels"
        try:
            init_res = requests.post(
                init_url,
                data={"upload_phase": "start", "access_token": self.access_token},
                timeout=30
            ).json()

            if "video_id" not in init_res:
                return {"success": False, "error": f"Failed to start Facebook Reel upload: {init_res}"}

            video_id = init_res["video_id"]
            upload_url = init_res.get("upload_url")

            # 2. Binary upload of video file
            with open(video_path, "rb") as f:
                video_data = f.read()

            headers = {
                "Authorization": f"OAuth {self.access_token}",
                "offset": "0",
                "file_size": str(len(video_data))
            }
            upload_res = requests.post(upload_url, headers=headers, data=video_data, timeout=120)
            if upload_res.status_code not in (200, 201):
                return {"success": False, "error": f"Video upload phase failed: {upload_res.text}"}

            # 3. Finish and Publish Reel
            finish_url = f"{self.base_url}/{self.fb_page_id}/video_reels"
            finish_data = {
                "upload_phase": "finish",
                "access_token": self.access_token,
                "video_id": video_id,
                "video_state": "PUBLISHED",
                "description": caption
            }
            finish_res = requests.post(finish_url, data=finish_data, timeout=30).json()

            if finish_res.get("success"):
                print(f"[MetaPublisher] Successfully published Facebook Reel! Video ID: {video_id}")
                return {"success": True, "platform": "facebook", "post_id": video_id}
            else:
                return {"success": False, "error": f"Failed to finalize Facebook Reel: {finish_res}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_to_publish_queue(
        self,
        video_path: Path,
        title: str,
        caption: str,
        hashtags: list
    ) -> Path:
        """Saves reel details to local metadata queue for tracking or scheduled publishing."""
        queue_file = config.OUTPUT_DIR / "publish_queue.json"
        
        queue_data = []
        if queue_file.exists():
            try:
                with open(queue_file, "r", encoding="utf-8") as f:
                    queue_data = json.load(f)
            except Exception:
                queue_data = []

        item = {
            "id": f"reel_{int(time.time())}",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "video_path": str(video_path),
            "title": title,
            "caption": caption,
            "hashtags": hashtags,
            "status": "ready_for_posting"
        }
        queue_data.insert(0, item)

        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(queue_data, f, indent=2, ensure_ascii=False)

        print(f"[MetaPublisher] Reel saved to publishing queue: {item['id']}")
        return queue_file
