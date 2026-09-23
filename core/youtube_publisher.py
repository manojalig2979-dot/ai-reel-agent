import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
import config

# Fix UnicodeEncodeError on Windows terminals (cp1252) when printing Hindi/emoji characters
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _safe_print(msg: str) -> None:
    """Print safely on any platform, replacing unencodable characters instead of crashing."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))

TOKEN_CACHE_FILE = config.BASE_DIR / "token_youtube.json"


class YouTubePublisher:
    """
    YouTube Shorts & Channel Publisher.
    Supports uploading vertical 9:16 reels directly to YouTube Shorts with:
    - Automatic #Shorts tagging & algorithmic SEO
    - Custom title, chapters, and rich description
    - Targeted viral tags and category selection (Entertainment, Kids/Animation, Education)
    - Privacy settings: Public, Unlisted, Private
    - Child-directed content flag ('made_for_kids')
    """

    def __init__(
        self,
        client_secrets_file: Optional[str] = None,
        api_key: Optional[str] = None,
        channel_id: Optional[str] = None
    ):
        default_secrets = getattr(config, "YOUTUBE_CLIENT_SECRETS_FILE", str(getattr(config, "BASE_DIR", Path(__file__).resolve().parent.parent) / "client_secret.json"))
        self.client_secrets_file = Path(client_secrets_file or default_secrets)
        self.api_key = api_key or getattr(config, "YOUTUBE_API_KEY", "")
        self.channel_id = channel_id or getattr(config, "YOUTUBE_CHANNEL_ID", "")
        self.token_file = TOKEN_CACHE_FILE

        # Auto-detect client secrets file if default path wasn't found directly
        if not self.client_secrets_file.exists():
            base_d = getattr(config, "BASE_DIR", Path(__file__).resolve().parent.parent)
            for cand in [base_d / "client_secret.json", base_d / "client_secret.json.json"]:
                if cand.exists():
                    self.client_secrets_file = cand
                    break

    def is_configured(self) -> Dict[str, Any]:
        """Check if YouTube upload credentials or OAuth token are ready."""
        if not self.client_secrets_file.exists():
            base_d = getattr(config, "BASE_DIR", Path(__file__).resolve().parent.parent)
            for cand in [base_d / "client_secret.json", base_d / "client_secret.json.json"]:
                if cand.exists():
                    self.client_secrets_file = cand
                    break

        has_secrets = self.client_secrets_file.exists()
        has_token = self.token_file.exists()
        has_api_key = bool(self.api_key)
        
        return {
            "configured": has_token or has_secrets or has_api_key,
            "has_secrets_file": has_secrets,
            "has_token": has_token,
            "has_api_key": has_api_key,
            "channel_id": self.channel_id or "Default Channel"
        }

    def _get_authenticated_service(self):
        """Builds an authorized YouTube API client using google-api-python-client or cached OAuth2."""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]
            creds = None

            if self.token_file.exists():
                try:
                    creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
                except Exception:
                    creds = None

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        with open(self.token_file, "w", encoding="utf-8") as token:
                            token.write(creds.to_json())
                    except Exception:
                        creds = None

                if not creds:
                    if not self.client_secrets_file.exists():
                        raise FileNotFoundError(
                            f"YouTube client secrets file not found at: {self.client_secrets_file}. "
                            "Please download client_secret.json from Google Cloud Console."
                        )
                    flow = InstalledAppFlow.from_client_secrets_file(str(self.client_secrets_file), SCOPES)
                    creds = flow.run_local_server(port=0)
                    with open(self.token_file, "w", encoding="utf-8") as token:
                        token.write(creds.to_json())

            return build("youtube", "v3", credentials=creds)

        except ImportError:
            return None

    def upload_short(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        category_id: str = "24",  # 24 = Entertainment, 27 = Education, 1 = Film & Animation
        privacy_status: str = "public",  # public, unlisted, private
        made_for_kids: bool = False
    ) -> Dict[str, Any]:
        """
        Uploads a video to YouTube as a Shorts video.
        Ensures '#Shorts' is in title and description for YouTube algorithm discovery.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            return {"success": False, "error": f"Video file not found at: {video_path}"}

        # 1. Format title with #Shorts if not present
        clean_title = title.strip()
        if "#shorts" not in clean_title.lower() and "#short" not in clean_title.lower():
            if len(clean_title) <= 90:
                clean_title = f"{clean_title} #Shorts"
            else:
                clean_title = f"{clean_title[:82]}... #Shorts"

        # 2. Format description with hashtags & attribution
        clean_desc = description.strip()
        if "#Shorts" not in clean_desc:
            clean_desc = f"{clean_desc}\n\n#Shorts #YouTubeShorts #NDStudio #Trending"

        # 3. Compile tags
        all_tags = list(set(["Shorts", "YouTube Shorts", "Trending", "Viral"] + (tags or [])))

        _safe_print(f"[YouTubePublisher] Preparing to upload Short: '{clean_title}' to YouTube...")

        try:
            youtube = self._get_authenticated_service()

            if youtube is not None:
                from googleapiclient.http import MediaFileUpload

                body = {
                    "snippet": {
                        "title": clean_title,
                        "description": clean_desc,
                        "tags": all_tags,
                        "categoryId": category_id
                    },
                    "status": {
                        "privacyStatus": privacy_status,
                        "selfDeclaredMadeForKids": made_for_kids
                    }
                }

                media = MediaFileUpload(
                    str(video_path),
                    mimetype="video/mp4",
                    resumable=True,
                    chunksize=1024 * 1024 * 4
                )

                request = youtube.videos().insert(
                    part="snippet,status",
                    body=body,
                    media_body=media
                )

                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        _safe_print(f"[YouTubePublisher] Uploaded {int(status.progress() * 100)}%")

                if response and "id" in response:
                    video_id = response["id"]
                    video_url = f"https://youtube.com/shorts/{video_id}"
                    _safe_print(f"[YouTubePublisher] [SUCCESS] Short Published! URL: {video_url}")
                    return {
                        "success": True,
                        "platform": "youtube",
                        "video_id": video_id,
                        "url": video_url,
                        "title": clean_title
                    }
                else:
                    return {"success": False, "error": f"Upload failed: {response}"}

            else:
                # Direct queue registration fallback when packages are initializing
                return {
                    "success": False,
                    "error": (
                        "Google API client not initialized. Please ensure 'google-api-python-client' "
                        "and 'google-auth-oauthlib' are installed and client_secret.json is configured."
                    ),
                    "queued_details": {
                        "title": clean_title,
                        "video_path": str(video_path),
                        "tags": all_tags,
                        "made_for_kids": made_for_kids
                    }
                }

        except Exception as e:
            _safe_print(f"[YouTubePublisher] Upload error: {e}")
            return {"success": False, "error": str(e)}
