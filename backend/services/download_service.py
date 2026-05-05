import logging
import os
import subprocess
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.db.models import Track, DownloadHistory, Playlist
from backend.services.ytdlp_service import YtDlpService

logger = logging.getLogger(__name__)

# Threshold for flagging a file as truncated:
# actual duration must be shorter than expected by more than this ratio AND more than MIN_TRUNCATION_SECONDS
TRUNCATION_RATIO_THRESHOLD = 0.10   # 10% shorter than expected
TRUNCATION_MIN_SECONDS = 10         # at least 10 seconds missing


def get_audio_duration(file_path: str) -> float | None:
    """
    Use ffprobe to get the actual duration of an audio file in seconds.
    Returns None if ffprobe is unavailable or the file cannot be read.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        if output:
            return float(output)
    except FileNotFoundError:
        logger.warning("ffprobe not found; skipping audio duration check")
    except (ValueError, subprocess.TimeoutExpired) as e:
        logger.warning(f"Failed to get audio duration for {file_path}: {e}")
    return None


def is_audio_truncated(file_path: str, expected_seconds: int) -> tuple[bool, float | None]:
    """
    Check whether an audio file is truncated compared to the expected duration.
    Returns (is_truncated, actual_duration_seconds).
    """
    actual = get_audio_duration(file_path)
    if actual is None:
        return False, None

    shortfall = expected_seconds - actual
    if shortfall > TRUNCATION_MIN_SECONDS and shortfall / expected_seconds > TRUNCATION_RATIO_THRESHOLD:
        return True, actual

    return False, actual


class DownloadService:
    """Service for managing downloads"""

    def __init__(self, db: Session):
        self.db = db
        self.ytdlp = YtDlpService()

    def download_track(self, track: Track) -> DownloadHistory:
        """Download a single track and create download history record"""
        # Create download history record
        history = DownloadHistory(
            track_id=track.id,
            status="downloading",
            started_at=datetime.utcnow(),
        )
        self.db.add(history)
        self.db.commit()

        try:
            # Get track URL
            playlist = self.db.query(Playlist).filter(Playlist.id == track.playlist_id).first()
            if not playlist:
                raise ValueError("Playlist not found")

            track_url = YtDlpService.build_track_url(playlist.platform, track.external_id)

            ytdlp = YtDlpService(download_dir=playlist.download_dir) if playlist.download_dir else self.ytdlp

            # Download
            info = ytdlp.download_track(track_url)
            if not info:
                raise Exception("Download returned no info")

            # Get file path and size
            file_path = ytdlp.get_downloaded_file_path(info)
            file_size = os.path.getsize(file_path) if file_path and os.path.exists(file_path) else None

            # Update history
            history.status = "completed"
            history.file_path = file_path
            history.file_size_bytes = file_size
            history.completed_at = datetime.utcnow()

            logger.info(f"Downloaded track: {track.title}")

        except Exception as e:
            logger.error(f"Failed to download track {track.title}: {e}")
            history.status = "failed"
            history.error_message = str(e)
            history.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(history)
        return history

    def download_new_tracks(self, tracks: list[Track]) -> list[DownloadHistory]:
        """Download multiple tracks"""
        results = []
        for track in tracks:
            history = self.download_track(track)
            results.append(history)
        return results

    def get_download_history(
        self,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        playlist_id: int | None = None,
    ) -> list[DownloadHistory]:
        """Get download history with optional filters (only returns records with valid tracks)"""
        query = self.db.query(DownloadHistory).join(Track)

        if status:
            query = query.filter(DownloadHistory.status == status)

        if playlist_id:
            query = query.join(Track).filter(Track.playlist_id == playlist_id)

        return (
            query.order_by(DownloadHistory.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_download_stats(self) -> dict:
        """Get download statistics"""
        from sqlalchemy import func

        total = self.db.query(func.count(DownloadHistory.id)).scalar() or 0
        completed = (
            self.db.query(func.count(DownloadHistory.id))
            .filter(DownloadHistory.status == "completed")
            .scalar() or 0
        )
        failed = (
            self.db.query(func.count(DownloadHistory.id))
            .filter(DownloadHistory.status == "failed")
            .scalar() or 0
        )
        pending = (
            self.db.query(func.count(DownloadHistory.id))
            .filter(DownloadHistory.status == "pending")
            .scalar() or 0
        )
        total_size = (
            self.db.query(func.sum(DownloadHistory.file_size_bytes))
            .filter(DownloadHistory.status == "completed")
            .scalar() or 0
        )

        return {
            "total_downloads": total,
            "completed_downloads": completed,
            "failed_downloads": failed,
            "pending_downloads": pending,
            "total_file_size_bytes": total_size,
        }

    def retry_failed_download(self, history_id: int) -> DownloadHistory | None:
        """Retry a failed download"""
        history = (
            self.db.query(DownloadHistory)
            .filter(DownloadHistory.id == history_id)
            .first()
        )
        if not history or history.status != "failed":
            return None

        track = self.db.query(Track).filter(Track.id == history.track_id).first()
        if not track:
            return None

        return self.download_track(track)

    def get_incomplete_downloads(self) -> dict:
        """
        Identify tracks with incomplete downloads:
        - truncated: file exists but audio is cut off (actual duration << expected)
        - failed: download failed with an error
        - file_missing: marked completed but file no longer exists on disk
        - never_downloaded: tracks that have no download history at all
        Returns a dict with categorized results.
        """
        # 1. Truncated files: completed downloads whose audio is shorter than expected
        completed_histories = (
            self.db.query(DownloadHistory)
            .filter(DownloadHistory.status == "completed")
            .all()
        )

        truncated = []
        file_missing_histories = []

        for history in completed_histories:
            if not history.file_path or not os.path.exists(history.file_path):
                file_missing_histories.append(history)
                continue

            # Check for audio truncation when expected duration is known
            track = self.db.query(Track).filter(Track.id == history.track_id).first()
            if track and track.duration_seconds:
                truncated_flag, actual_duration = is_audio_truncated(
                    history.file_path, track.duration_seconds
                )
                if truncated_flag:
                    logger.info(
                        f"Truncated audio detected: '{track.title}' "
                        f"expected={track.duration_seconds}s actual={actual_duration:.1f}s"
                    )
                    truncated.append({
                        "history": history,
                        "track": track,
                        "expected_duration_seconds": track.duration_seconds,
                        "actual_duration_seconds": actual_duration,
                    })

        # 2. Failed downloads
        failed_histories = (
            self.db.query(DownloadHistory)
            .filter(DownloadHistory.status == "failed")
            .order_by(DownloadHistory.created_at.desc())
            .all()
        )

        # 3. Tracks with no download history at all
        downloaded_track_ids = (
            self.db.query(DownloadHistory.track_id)
            .distinct()
            .subquery()
        )
        never_downloaded_tracks = (
            self.db.query(Track)
            .filter(Track.id.notin_(downloaded_track_ids))
            .all()
        )

        return {
            "truncated": truncated,
            "failed": failed_histories,
            "file_missing": file_missing_histories,
            "never_downloaded": never_downloaded_tracks,
        }

    def get_tracks_to_redownload(self, playlist_id: int | None = None) -> dict:
        """
        Returns de-duplicated Track objects per incomplete category, optionally filtered by playlist_id.
        Priority order ensures a track appears in only the first matching category.
        """
        incomplete = self.get_incomplete_downloads()
        seen_ids: set[int] = set()

        def collect(track: Track) -> bool:
            if track.id in seen_ids:
                return False
            if playlist_id is not None and track.playlist_id != playlist_id:
                return False
            seen_ids.add(track.id)
            return True

        truncated = [item["track"] for item in incomplete["truncated"] if collect(item["track"])]

        failed = []
        for history in incomplete["failed"]:
            track = self.db.query(Track).filter(Track.id == history.track_id).first()
            if track and collect(track):
                failed.append(track)

        file_missing = []
        for history in incomplete["file_missing"]:
            track = self.db.query(Track).filter(Track.id == history.track_id).first()
            if track and collect(track):
                file_missing.append(track)

        never_downloaded = [t for t in incomplete["never_downloaded"] if collect(t)]

        return {
            "truncated": truncated,
            "failed": failed,
            "file_missing": file_missing,
            "never_downloaded": never_downloaded,
        }

    def redownload_incomplete(self, playlist_id: int | None = None) -> dict:
        """
        Re-download all incomplete tracks.
        Optionally filter by playlist_id.
        Returns lists of new DownloadHistory records per category.
        """
        incomplete = self.get_incomplete_downloads()

        retried_truncated = []
        for item in incomplete["truncated"]:
            track = item["track"]
            if playlist_id and track.playlist_id != playlist_id:
                continue
            new_history = self.download_track(track)
            retried_truncated.append(new_history)

        retried_failed = []
        for history in incomplete["failed"]:
            track = self.db.query(Track).filter(Track.id == history.track_id).first()
            if not track:
                continue
            if playlist_id and track.playlist_id != playlist_id:
                continue
            new_history = self.download_track(track)
            retried_failed.append(new_history)

        retried_missing = []
        for history in incomplete["file_missing"]:
            track = self.db.query(Track).filter(Track.id == history.track_id).first()
            if not track:
                continue
            if playlist_id and track.playlist_id != playlist_id:
                continue
            new_history = self.download_track(track)
            retried_missing.append(new_history)

        retried_never = []
        for track in incomplete["never_downloaded"]:
            if playlist_id and track.playlist_id != playlist_id:
                continue
            new_history = self.download_track(track)
            retried_never.append(new_history)

        logger.info(
            f"Redownload incomplete: truncated={len(retried_truncated)}, "
            f"failed={len(retried_failed)}, file_missing={len(retried_missing)}, "
            f"never_downloaded={len(retried_never)}"
        )

        return {
            "retried_truncated": retried_truncated,
            "retried_failed": retried_failed,
            "retried_file_missing": retried_missing,
            "retried_never_downloaded": retried_never,
        }
