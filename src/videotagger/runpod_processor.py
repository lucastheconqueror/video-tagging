"""RunPod remote video processing.

Processes videos that are stored on RunPod S3/network volume using the GPU pod.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from videotagger.config import get_settings
from videotagger.llm import analyze_frames
from videotagger.runpod_s3 import get_runpod_s3_client
from videotagger.video import extract_frames_as_base64

logger = logging.getLogger(__name__)


@dataclass
class RemoteVideo:
    """Video file on RunPod S3."""

    key: str  # S3 key e.g. "videos/V - TOMB - Teaser - a1234.mp4"
    size: int
    filename: str

    @property
    def size_mb(self) -> float:
        return self.size / (1024 * 1024)

    @property
    def size_display(self) -> str:
        if self.size_mb >= 1000:
            return f"{self.size_mb / 1024:.1f} GB"
        return f"{self.size_mb:.1f} MB"


def list_remote_videos(prefix: str = "videos/") -> list[RemoteVideo]:
    """List videos available on RunPod S3.

    Args:
        prefix: S3 prefix to filter videos.

    Returns:
        List of RemoteVideo objects.
    """
    client = get_runpod_s3_client()
    files = client.list_files(prefix=prefix)

    videos = []
    for f in files:
        key = f["key"]
        # Only include video files
        if key.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
            filename = Path(key).name
            videos.append(
                RemoteVideo(
                    key=key,
                    size=f["size"],
                    filename=filename,
                )
            )

    # Sort by filename
    videos.sort(key=lambda v: v.filename)
    logger.info(f"Found {len(videos)} videos on RunPod S3")
    return videos


def process_remote_video(video: RemoteVideo | str) -> dict:
    """Process a video stored on RunPod S3.

    Since vLLM runs on the same pod that has the S3 volume mounted,
    we can read the video directly from the mounted path.

    However, the current vLLM endpoint expects base64 frames, not file paths.
    So we need to either:
    1. Download the video locally, extract frames, send to vLLM (current approach)
    2. Have a custom endpoint on RunPod that reads from disk

    For now, we use approach 1 with the HTTP endpoint.

    Args:
        video: RemoteVideo object or S3 key string.

    Returns:
        Extracted tags dict.
    """
    import tempfile

    import boto3

    if isinstance(video, str):
        key = video
        filename = Path(video).name
    else:
        key = video.key
        filename = video.filename

    config = get_settings().runpod_s3
    llm_config = get_settings().llm

    logger.info(f"Processing remote video: {filename}")

    # Download from S3 to temp file
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        # Download
        logger.debug(f"Downloading {key} to {tmp_path}")
        client = boto3.client(
            "s3",
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            endpoint_url=config.endpoint,
        )
        client.download_file(config.bucket, key, str(tmp_path))

        # Extract frames
        logger.debug(f"Extracting {llm_config.frame_count} frames")
        frames = extract_frames_as_base64(str(tmp_path), num_frames=llm_config.frame_count)

        # Analyze with LLM
        logger.debug("Analyzing with vLLM")
        tags = analyze_frames(frames)

        logger.info(f"Processed: {filename}")
        return tags

    finally:
        # Clean up temp file
        if tmp_path.exists():
            tmp_path.unlink()


def process_remote_video_batch(
    videos: list[RemoteVideo],
    progress_callback=None,
) -> list[tuple[RemoteVideo, dict | None, str | None]]:
    """Process multiple remote videos.

    Args:
        videos: List of RemoteVideo objects.
        progress_callback: Optional callback(index, total, video, status).

    Returns:
        List of (video, tags, error) tuples.
    """
    results = []

    for i, video in enumerate(videos):
        if progress_callback:
            progress_callback(i, len(videos), video, "processing")

        try:
            tags = process_remote_video(video)
            results.append((video, tags, None))
        except Exception as e:
            logger.error(f"Failed to process {video.filename}: {e}")
            results.append((video, None, str(e)))

    return results
