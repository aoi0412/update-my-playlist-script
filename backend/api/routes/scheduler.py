from fastapi import APIRouter
from backend.scheduler.jobs import (
    get_scheduler_status,
    pause_scheduler,
    resume_scheduler,
)

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/status")
def get_status():
    """Get scheduler status"""
    return get_scheduler_status()


@router.post("/pause")
def pause():
    """Pause the scheduler"""
    pause_scheduler()
    return {"message": "Scheduler paused"}


@router.post("/resume")
def resume():
    """Resume the scheduler"""
    resume_scheduler()
    return {"message": "Scheduler resumed"}
