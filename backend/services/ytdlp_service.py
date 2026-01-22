import yt_dlp
import logging
from pathlib import Path
from typing import Callable
from backend.config import settings

logger = logging.getLogger(__name__)


class YtDlpService:
    """Wrapper class for yt-dlp library"""

    def __init__(self, download_dir: str | None = None):
        self.download_dir = download_dir or settings.download_dir
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)

        self.base_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": settings.audio_format,
                    "preferredquality": settings.audio_quality,
                }
            ],
            "outtmpl": f"{self.download_dir}/%(title)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
        }

        if settings.youtube_cookies_file:
            self.base_opts["cookiefile"] = settings.youtube_cookies_file

    def extract_playlist_info(self, url: str) -> dict | None:
        """Extract playlist metadata without downloading"""
        opts = {
            **self.base_opts,
            "extract_flat": "in_playlist",
            "skip_download": True,
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            logger.error(f"Failed to extract playlist info: {e}")
            return None

    def extract_track_info(self, url: str) -> dict | None:
        """Extract single track metadata without downloading"""
        opts = {
            **self.base_opts,
            "skip_download": True,
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            logger.error(f"Failed to extract track info: {e}")
            return None

    def download_track(
        self, url: str, progress_hook: Callable | None = None
    ) -> dict | None:
        """Download track as MP3"""
        opts = {**self.base_opts}
        if progress_hook:
            opts["progress_hooks"] = [progress_hook]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info
        except Exception as e:
            logger.error(f"Failed to download track: {e}")
            return None

    def get_downloaded_file_path(self, info: dict) -> str | None:
        """Get the path of the downloaded file from yt-dlp info"""
        if not info:
            return None

        title = info.get("title", "unknown")
        # yt-dlp sanitizes filenames, so we need to do the same
        safe_title = yt_dlp.utils.sanitize_filename(title)
        file_path = Path(self.download_dir) / f"{safe_title}.{settings.audio_format}"

        if file_path.exists():
            return str(file_path)

        # Try to find the file with original title
        file_path = Path(self.download_dir) / f"{title}.{settings.audio_format}"
        if file_path.exists():
            return str(file_path)

        return None

    @staticmethod
    def detect_platform(url: str) -> str | None:
        """Detect platform from URL"""
        url = url.lower()
        if "youtube.com" in url or "music.youtube.com" in url or "youtu.be" in url:
            return "youtube_music"
        elif "soundcloud.com" in url:
            return "soundcloud"
        return None

    @staticmethod
    def build_track_url(platform: str, external_id: str) -> str:
        """Build track URL from platform and external ID"""
        if platform == "youtube_music":
            return f"https://www.youtube.com/watch?v={external_id}"
        elif platform == "soundcloud":
            # SoundCloud URLs are stored as full URLs in external_id
            return external_id
        return external_id
