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
            "outtmpl": f"{self.download_dir}/%(artist,uploader)s - %(title)s.%(ext)s",
            "writethumbnail": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": settings.audio_format,
                    "preferredquality": settings.audio_quality,
                },
                {"key": "EmbedThumbnail"},
                {"key": "FFmpegMetadata"},
            ],
            "sleep_interval": 5,
            "max_sleep_interval": 10,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
        }

        # Use setting if explicitly provided
        if settings.youtube_cookies_file:
            self.base_opts["cookiefile"] = settings.youtube_cookies_file
        # Otherwise, look for data/cookies.txt
        elif Path("./data/cookies.txt").exists():
            self.base_opts["cookiefile"] = "./data/cookies.txt"

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
        opts = {**self.base_opts, "ignoreerrors": False}
        if progress_hook:
            opts["progress_hooks"] = [progress_hook]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info
        except Exception as e:
            logger.error(f"Failed to download track: {e}")
            raise  # Let the download_service capture the actual error

    def get_downloaded_file_path(self, info: dict) -> str | None:
        """Get the path of the downloaded file from yt-dlp info"""
        if not info:
            return None

        # Sometimes yt-dlp provides the exact final file path in requested_downloads
        requested_downloads = info.get("requested_downloads")
        if requested_downloads and len(requested_downloads) > 0:
            filepath = requested_downloads[0].get("filepath")
            if filepath and Path(filepath).exists():
                return filepath

        # Fallback: re-construct file path from ydl.prepare_filename
        try:
            with yt_dlp.YoutubeDL(self.base_opts) as ydl:
                filename = ydl.prepare_filename(info)
                # Replace the original extension (like .webm or .m4a) with our audio_format
                import os
                base_name = os.path.splitext(filename)[0]
                expected_path = f"{base_name}.{settings.audio_format}"
                if Path(expected_path).exists():
                    return expected_path
        except Exception as e:
            logger.warning(f"Failed to cleanly determine file path via prepare_filename: {e}")

        # Final fallback using the original static logic just in case prepare_filename fails entirely
        title = info.get("title", "unknown")
        artist = info.get("artist") or info.get("uploader") or "NA"
        
        # This fallback is highly fragile with dynamic templates but kept for emergencies
        safe_title = yt_dlp.utils.sanitize_filename(title)
        safe_artist = yt_dlp.utils.sanitize_filename(artist)
        
        file_path = Path(self.download_dir) / f"{safe_artist} - {safe_title}.{settings.audio_format}"
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
