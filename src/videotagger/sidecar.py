"""Sidecar file management for tracking processed videos.

A sidecar file is a JSON file stored alongside the video with the same name
but .json extension, containing the extracted tags and processing metadata.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def get_sidecar_path(video_path: str | Path) -> Path:
    """Get the sidecar JSON file path for a video.

    Args:
        video_path: Path to the video file.

    Returns:
        Path to the sidecar JSON file (same name, .json extension).
    """
    video_path = Path(video_path)
    return video_path.with_suffix(".json")


def has_sidecar(video_path: str | Path) -> bool:
    """Check if a video has an existing sidecar file.

    Args:
        video_path: Path to the video file.

    Returns:
        True if sidecar exists, False otherwise.
    """
    sidecar_path = get_sidecar_path(video_path)
    return sidecar_path.exists()


def read_sidecar(video_path: str | Path) -> dict[str, Any] | None:
    """Read the sidecar file for a video.

    Args:
        video_path: Path to the video file.

    Returns:
        Sidecar data as dict, or None if not found.
    """
    sidecar_path = get_sidecar_path(video_path)

    if not sidecar_path.exists():
        return None

    try:
        with open(sidecar_path, encoding="utf-8") as f:
            data = json.load(f)
            logger.debug(f"Read sidecar: {sidecar_path}")
            return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to read sidecar {sidecar_path}: {e}")
        return None


def write_sidecar(
    video_path: str | Path,
    tags: dict[str, Any],
    airtable_updated: bool = False,
) -> Path:
    """Write a sidecar file for a video.

    Args:
        video_path: Path to the video file.
        tags: Extracted tags from LLM analysis.
        airtable_updated: Whether Airtable was updated with these tags.

    Returns:
        Path to the written sidecar file.
    """
    video_path = Path(video_path)
    sidecar_path = get_sidecar_path(video_path)

    sidecar_data = {
        "video_file": video_path.name,
        "processed_at": datetime.now().isoformat(),
        "airtable_updated": airtable_updated,
        "tags": tags,
    }

    with open(sidecar_path, "w", encoding="utf-8") as f:
        json.dump(sidecar_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Wrote sidecar: {sidecar_path}")
    return sidecar_path


def get_sidecar_info(video_path: str | Path) -> str | None:
    """Get a human-readable summary of existing sidecar.

    Args:
        video_path: Path to the video file.

    Returns:
        Summary string, or None if no sidecar exists.
    """
    data = read_sidecar(video_path)
    if data is None:
        return None

    processed_at = data.get("processed_at", "unknown time")
    airtable = "yes" if data.get("airtable_updated") else "no"

    # Parse and format the date
    try:
        dt = datetime.fromisoformat(processed_at)
        processed_at = dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        pass

    return f"Processed: {processed_at}, Airtable updated: {airtable}"
