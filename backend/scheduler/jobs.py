import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from backend.db import SessionLocal, Playlist
from backend.db.models import DownloadHistory
from backend.services import PlaylistService, DownloadService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _sync_check_playlist_updates(playlist_id: int):
    """Synchronous worker — runs in a thread pool to avoid blocking the event loop."""
    db = SessionLocal()
    try:
        playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
        if not playlist or not playlist.is_active:
            logger.info(f"Playlist {playlist_id} not found or inactive, skipping")
            return

        playlist_service = PlaylistService(db)
        new_tracks = playlist_service.check_for_updates(playlist)

        if new_tracks:
            logger.info(f"Found {len(new_tracks)} new tracks in playlist {playlist_id}")
            download_service = DownloadService(db)
            download_service.download_new_tracks(new_tracks)
        else:
            logger.info(f"No new tracks in playlist {playlist_id}")

    except Exception as e:
        logger.error(f"Error checking playlist {playlist_id}: {e}")
    finally:
        db.close()


async def check_playlist_updates_job(playlist_id: int):
    """Check a playlist for updates and download new tracks."""
    logger.info(f"Running scheduled check for playlist {playlist_id}")
    await asyncio.to_thread(_sync_check_playlist_updates, playlist_id)


def _sync_check_incomplete_downloads():
    """Synchronous worker — runs in a thread pool to avoid blocking the event loop."""
    db = SessionLocal()
    try:
        download_service = DownloadService(db)
        incomplete = download_service.get_incomplete_downloads()

        failed_count = len(incomplete["failed"])
        missing_count = len(incomplete["file_missing"])
        never_count = len(incomplete["never_downloaded"])
        total = failed_count + missing_count + never_count

        logger.info(
            f"Incomplete downloads found: failed={failed_count}, "
            f"file_missing={missing_count}, never_downloaded={never_count}"
        )

        if total == 0:
            logger.info("No incomplete downloads found")
            return

        result = download_service.redownload_incomplete()
        retried = (
            len(result["retried_failed"])
            + len(result["retried_file_missing"])
            + len(result["retried_never_downloaded"])
        )
        logger.info(f"Re-download complete: {retried} tracks retried")

    except Exception as e:
        logger.error(f"Error during incomplete downloads check: {e}")
    finally:
        db.close()


async def check_incomplete_downloads_job():
    """Check for incomplete downloads across all playlists and re-download them."""
    logger.info("Running scheduled check for incomplete downloads")
    await asyncio.to_thread(_sync_check_incomplete_downloads)


def schedule_playlist_check(playlist: Playlist):
    """Schedule periodic check for a playlist"""
    job_id = f"playlist_check_{playlist.id}"

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    if not playlist.is_active:
        return

    scheduler.add_job(
        check_playlist_updates_job,
        trigger=IntervalTrigger(hours=playlist.check_interval_hours),
        args=[playlist.id],
        id=job_id,
        name=f"Check playlist: {playlist.name}",
        replace_existing=True,
    )
    logger.info(
        f"Scheduled check for playlist {playlist.id} "
        f"every {playlist.check_interval_hours} hours"
    )


def setup_scheduler(app):
    """Setup scheduler with FastAPI lifecycle"""

    @app.on_event("startup")
    async def start_scheduler():
        """Initialize scheduler and load existing playlist jobs"""
        db = SessionLocal()
        try:
            # Reset any downloads stuck in "downloading" from before a restart
            stuck = (
                db.query(DownloadHistory)
                .filter(DownloadHistory.status == "downloading")
                .all()
            )
            if stuck:
                for h in stuck:
                    h.status = "failed"
                    h.error_message = "Interrupted by container restart"
                db.commit()
                logger.info(f"Reset {len(stuck)} stuck 'downloading' records to 'failed'")

            playlists = db.query(Playlist).filter(Playlist.is_active == True).all()
            for playlist in playlists:
                schedule_playlist_check(playlist)

            scheduler.add_job(
                check_incomplete_downloads_job,
                trigger=IntervalTrigger(hours=6),
                id="check_incomplete_downloads",
                name="Check incomplete downloads",
                replace_existing=True,
            )
            logger.info("Scheduled incomplete downloads check every 6 hours")

            scheduler.start()
            logger.info(f"Scheduler started with {len(playlists)} playlist jobs")
        finally:
            db.close()

    @app.on_event("shutdown")
    async def shutdown_scheduler():
        """Shutdown scheduler gracefully"""
        scheduler.shutdown()
        logger.info("Scheduler shutdown complete")


def get_scheduler_status() -> dict:
    """Get current scheduler status"""
    jobs = scheduler.get_jobs()
    return {
        "running": scheduler.running,
        "job_count": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in jobs
        ],
    }


def pause_scheduler():
    """Pause the scheduler"""
    scheduler.pause()


def resume_scheduler():
    """Resume the scheduler"""
    scheduler.resume()
