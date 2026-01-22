from .playlists import router as playlists_router
from .downloads import router as downloads_router
from .scheduler import router as scheduler_router

__all__ = ["playlists_router", "downloads_router", "scheduler_router"]
