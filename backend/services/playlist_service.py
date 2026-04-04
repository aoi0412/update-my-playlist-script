import logging
from datetime import datetime
from sqlalchemy.orm import Session
from backend.db.models import Playlist, Track
from backend.services.ytdlp_service import YtDlpService

logger = logging.getLogger(__name__)


class PlaylistService:
    """Service for managing playlists and detecting updates"""

    def __init__(self, db: Session):
        self.db = db
        self.ytdlp = YtDlpService()

    def create_playlist(self, url: str, name: str | None = None, check_interval_hours: int = 24, download_dir: str | None = None) -> Playlist | None:
        """Create a new playlist from URL"""
        platform = YtDlpService.detect_platform(url)
        if not platform:
            logger.error(f"Unsupported platform for URL: {url}")
            return None

        # Extract playlist info
        info = self.ytdlp.extract_playlist_info(url)
        if not info:
            logger.error(f"Failed to extract playlist info: {url}")
            return None

        playlist_name = name or info.get("title", "Unknown Playlist")

        # Create playlist record
        playlist = Playlist(
            url=url,
            name=playlist_name,
            platform=platform,
            download_dir=download_dir,
            check_interval_hours=check_interval_hours,
            is_active=True,
            last_checked_at=datetime.utcnow(),
        )
        self.db.add(playlist)
        self.db.flush()

        # Add tracks
        entries = info.get("entries", [])
        for entry in entries:
            if not entry:
                continue
            self._add_track_from_entry(playlist, entry)

        self.db.commit()
        self.db.refresh(playlist)
        return playlist

    def check_for_updates(self, playlist: Playlist) -> list[Track]:
        """Check playlist for new tracks and return newly added tracks"""
        info = self.ytdlp.extract_playlist_info(playlist.url)
        if not info:
            logger.error(f"Failed to fetch playlist info: {playlist.url}")
            return []

        entries = info.get("entries", [])
        existing_ids = {t.external_id for t in playlist.tracks}
        new_tracks = []

        for entry in entries:
            if not entry:
                continue

            external_id = self._get_external_id(entry, playlist.platform)
            if external_id and external_id not in existing_ids:
                track = self._add_track_from_entry(playlist, entry)
                if track:
                    new_tracks.append(track)
                    existing_ids.add(external_id)

        if new_tracks:
            self.db.commit()

        # Update last checked timestamp
        playlist.last_checked_at = datetime.utcnow()
        self.db.commit()

        return new_tracks

    def _add_track_from_entry(self, playlist: Playlist, entry: dict) -> Track | None:
        """Add a track from yt-dlp entry data"""
        external_id = self._get_external_id(entry, playlist.platform)
        if not external_id:
            return None

        track = Track(
            playlist_id=playlist.id,
            external_id=external_id,
            title=entry.get("title", "Unknown Track"),
            artist=entry.get("uploader") or entry.get("artist"),
            duration_seconds=entry.get("duration"),
            thumbnail_url=entry.get("thumbnail"),
        )
        self.db.add(track)
        return track

    def _get_external_id(self, entry: dict, platform: str) -> str | None:
        """Extract external ID from entry based on platform"""
        if platform == "youtube_music":
            return entry.get("id")
        elif platform == "soundcloud":
            # For SoundCloud, use URL as ID since track IDs aren't always available
            return entry.get("url") or entry.get("id")
        return entry.get("id")

    def get_all_active_playlists(self) -> list[Playlist]:
        """Get all active playlists"""
        return self.db.query(Playlist).filter(Playlist.is_active == True).all()

    def get_playlist_by_id(self, playlist_id: int) -> Playlist | None:
        """Get playlist by ID"""
        return self.db.query(Playlist).filter(Playlist.id == playlist_id).first()

    def delete_playlist(self, playlist_id: int) -> bool:
        """Delete a playlist"""
        playlist = self.get_playlist_by_id(playlist_id)
        if not playlist:
            return False
        self.db.delete(playlist)
        self.db.commit()
        return True
