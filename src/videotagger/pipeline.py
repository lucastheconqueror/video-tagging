"""Video processing pipeline."""

from pathlib import Path
from typing import Any

from videotagger.config import LLMConfig, get_settings
from videotagger.llm import analyze_frames
from videotagger.video import extract_frames_as_base64


def process_video(
    video_path: str | Path,
    config: LLMConfig | None = None,
) -> dict[str, Any]:
    """Process a video file and extract tags using vision-language model.

    Args:
        video_path: Path to the video file.
        config: Optional LLMConfig. If None, loads from Settings.

    Returns:
        Dictionary with extracted tags:
        - location: str
        - brand_objects: list[str]
        - visual_text: list[str]
        - mood: str
        - excitement: str

    Raises:
        VideoProcessingError: If frame extraction fails.
        LLMError: If LLM analysis fails.
    """
    if config is None:
        config = get_settings().llm

    # Extract frames as base64
    frames = extract_frames_as_base64(
        video_path, 
        num_frames=config.frame_count,
        max_size=config.frame_max_size,
    )

    # Analyze with LLM
    tags = analyze_frames(frames, config)

    return tags
