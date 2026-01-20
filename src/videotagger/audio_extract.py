"""Audio extraction from video files using FFmpeg."""

import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_audio(
    video_path: str | Path,
    output_path: str | Path | None = None,
    sample_rate: int = 16000,
    mono: bool = True,
) -> Path:
    """Extract audio from video file using FFmpeg.

    Args:
        video_path: Path to the input video file.
        output_path: Optional output path. If None, creates a temp file.
        sample_rate: Audio sample rate in Hz (default 16000 for speech models).
        mono: If True, convert to mono (required for most speech models).

    Returns:
        Path to the extracted audio WAV file.

    Raises:
        RuntimeError: If FFmpeg fails to extract audio.
        FileNotFoundError: If video file doesn't exist.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Create output path if not provided
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_path = Path(tmp.name)
        tmp.close()
    else:
        output_path = Path(output_path)

    # Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",  # No video
        "-acodec", "pcm_s16le",  # 16-bit PCM
        "-ar", str(sample_rate),  # Sample rate
    ]

    if mono:
        cmd.extend(["-ac", "1"])  # Mono

    cmd.extend([
        "-y",  # Overwrite output
        str(output_path),
    ])

    logger.debug(f"Running FFmpeg: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        logger.debug(f"FFmpeg stdout: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed: {e.stderr}")
        raise RuntimeError(f"Failed to extract audio: {e.stderr}") from e
    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg not found. Please install FFmpeg: brew install ffmpeg"
        )

    if not output_path.exists():
        raise RuntimeError(f"FFmpeg did not create output file: {output_path}")

    logger.info(f"Extracted audio: {output_path} ({output_path.stat().st_size} bytes)")
    return output_path


def get_audio_duration(audio_path: str | Path) -> float:
    """Get duration of audio file in seconds using FFprobe.

    Args:
        audio_path: Path to audio file.

    Returns:
        Duration in seconds.
    """
    audio_path = Path(audio_path)

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        logger.warning(f"Could not get audio duration: {e}")
        return 0.0
