"""RunPod remote video processing.

Processes videos that are stored on RunPod S3/network volume using the GPU pod.
Combines vision analysis (Qwen3-VL) with local audio analysis pipeline.
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


def process_remote_video(video: RemoteVideo | str, include_audio: bool = True) -> dict:
    """Process a video stored on RunPod S3.

    Combines:
    1. Vision analysis via Qwen3-VL on RunPod (frames → visual tags)
    2. Audio analysis locally (voice detection, mood, music genre)

    The audio pipeline runs entirely on local CPU while waiting for
    the vision model response, maximizing efficiency.

    Args:
        video: RemoteVideo object or S3 key string.
        include_audio: Whether to run audio analysis (default True).

    Returns:
        Merged tags dict with both vision and audio analysis.
    """
    import tempfile
    from concurrent.futures import ThreadPoolExecutor, as_completed

    import boto3

    if isinstance(video, str):
        key = video
        filename = Path(video).name
    else:
        key = video.key
        filename = video.filename

    settings = get_settings()
    config = settings.runpod_s3
    llm_config = settings.llm
    audio_config = settings.audio

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

        # Run vision and audio analysis in parallel
        vision_result = None
        audio_result = None
        errors = []

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}

            # Submit vision analysis (sends frames to RunPod vLLM)
            def run_vision():
                # Get dynamic endpoint from RunPod API
                from videotagger.runpod_api import ensure_pod_running

                success, message, vllm_endpoint = ensure_pod_running()
                if not success or not vllm_endpoint:
                    raise RuntimeError(f"Pod not ready: {message}")

                logger.info(f"Using vLLM endpoint: {vllm_endpoint}")
                logger.debug(f"Extracting {llm_config.frame_count} frames")
                frames = extract_frames_as_base64(
                    str(tmp_path), 
                    num_frames=llm_config.frame_count,
                    max_size=llm_config.frame_max_size,
                )
                logger.debug("Analyzing with vLLM")
                return analyze_frames(frames, endpoint_override=vllm_endpoint)

            futures[executor.submit(run_vision)] = "vision"

            # Submit audio analysis (runs locally on CPU)
            if include_audio and audio_config.enabled:

                def run_audio():
                    from videotagger.audio_analysis import analyze_video_audio

                    logger.debug("Running local audio analysis")
                    return analyze_video_audio(tmp_path)

                futures[executor.submit(run_audio)] = "audio"

            # Collect results
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    if task_name == "vision":
                        vision_result = future.result()
                    elif task_name == "audio":
                        audio_result = future.result()
                except Exception as e:
                    logger.error(f"{task_name} analysis failed: {e}")
                    errors.append(f"{task_name}: {e}")

        # Merge results
        tags = vision_result or {}

        if audio_result:
            tags["audio_analysis"] = audio_result.to_dict()
        elif include_audio and audio_config.enabled:
            # Audio was requested but failed
            tags["audio_analysis"] = {"error": "Audio analysis failed", "errors": errors}

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
