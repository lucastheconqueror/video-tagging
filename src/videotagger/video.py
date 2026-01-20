"""Video processing for frame extraction."""

import base64
import logging
from pathlib import Path

import cv2
import numpy as np

from videotagger.exceptions import VideoProcessingError

logger = logging.getLogger(__name__)


def extract_frames(video_path: str | Path, num_frames: int = 8) -> list[np.ndarray]:
    """Extract evenly-spaced frames from a video file.

    Args:
        video_path: Path to the video file.
        num_frames: Number of frames to extract (default: 8).

    Returns:
        List of frames as numpy arrays (BGR format).

    Raises:
        VideoProcessingError: If video cannot be opened or read.
    """
    video_path = Path(video_path)
    logger.info(f"Extracting {num_frames} frames from: {video_path}")

    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        raise VideoProcessingError(f"Video file not found: {video_path}", str(video_path))

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        logger.error(f"Could not open video: {video_path}")
        raise VideoProcessingError(f"Could not open video: {video_path}", str(video_path))

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0

        logger.info(
            f"Video info: {total_frames} frames, {fps:.1f} fps, {width}x{height}, {duration:.1f}s"
        )

        if total_frames < 1:
            logger.error(f"Video has no frames: {video_path}")
            raise VideoProcessingError(f"Video has no frames: {video_path}", str(video_path))

        # Calculate frame indices to extract (evenly spaced)
        if num_frames >= total_frames:
            frame_indices = list(range(total_frames))
        else:
            step = total_frames / num_frames
            frame_indices = [int(i * step) for i in range(num_frames)]

        frames = []
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()

            if not ret:
                continue  # Skip frames that can't be read

            frames.append(frame)

        if not frames:
            logger.error(f"Could not extract any frames from video: {video_path}")
            raise VideoProcessingError(
                f"Could not extract any frames from video: {video_path}",
                str(video_path),
            )

        logger.info(f"Successfully extracted {len(frames)} frames")
        return frames

    finally:
        cap.release()


def frame_to_base64(frame: np.ndarray, format: str = "jpg") -> str:
    """Convert a frame to base64-encoded string.

    Args:
        frame: Frame as numpy array (BGR format from OpenCV).
        format: Image format for encoding ('jpg' or 'png').

    Returns:
        Base64-encoded string of the image.

    Raises:
        VideoProcessingError: If encoding fails.
    """
    if format.lower() == "jpg":
        ext = ".jpg"
        params = [cv2.IMWRITE_JPEG_QUALITY, 85]
    else:
        ext = ".png"
        params = []

    success, buffer = cv2.imencode(ext, frame, params)

    if not success:
        raise VideoProcessingError("Failed to encode frame to image")

    return base64.b64encode(buffer).decode("utf-8")


def extract_frames_as_base64(
    video_path: str | Path,
    num_frames: int = 8,
) -> list[str]:
    """Extract frames from video and return as base64-encoded strings.

    Args:
        video_path: Path to the video file.
        num_frames: Number of frames to extract.

    Returns:
        List of base64-encoded JPEG images.

    Raises:
        VideoProcessingError: If extraction or encoding fails.
    """
    frames = extract_frames(video_path, num_frames)
    return [frame_to_base64(frame) for frame in frames]
