"""Simple file-based cache for video listings."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Cache location
CACHE_DIR = Path.home() / ".cache" / "videotagger"
SYNOLOGY_CACHE_FILE = CACHE_DIR / "synology_videos.json"

# Cache TTL in seconds (1 hour)
CACHE_TTL = 3600


def _ensure_cache_dir() -> None:
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_cached_videos() -> list[dict[str, Any]] | None:
    """Get cached video list if valid.

    Returns:
        List of video dicts, or None if cache is missing/expired.
    """
    if not SYNOLOGY_CACHE_FILE.exists():
        return None

    try:
        with open(SYNOLOGY_CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)

        # Check TTL
        cached_at = datetime.fromisoformat(data.get("cached_at", "2000-01-01"))
        age = (datetime.now() - cached_at).total_seconds()

        if age > CACHE_TTL:
            logger.debug(f"Cache expired (age={age:.0f}s)")
            return None

        videos = data.get("videos", [])
        logger.info(f"Using cached video list ({len(videos)} videos, age={age:.0f}s)")
        return videos

    except (json.JSONDecodeError, OSError, KeyError) as e:
        logger.warning(f"Failed to read cache: {e}")
        return None


def set_cached_videos(videos: list[dict[str, Any]]) -> None:
    """Cache video list.

    Args:
        videos: List of video dicts to cache.
    """
    _ensure_cache_dir()

    data = {
        "cached_at": datetime.now().isoformat(),
        "videos": videos,
    }

    try:
        with open(SYNOLOGY_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
        logger.info(f"Cached {len(videos)} videos")
    except OSError as e:
        logger.warning(f"Failed to write cache: {e}")


def clear_cache() -> None:
    """Clear the video cache."""
    if SYNOLOGY_CACHE_FILE.exists():
        SYNOLOGY_CACHE_FILE.unlink()
        logger.info("Cache cleared")
