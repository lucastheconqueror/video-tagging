"""Tests for video processing."""

import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from videotagger.exceptions import VideoProcessingError
from videotagger.video import extract_frames, extract_frames_as_base64, frame_to_base64


def create_test_video(path: Path, num_frames: int = 30, fps: int = 30) -> None:
    """Create a simple test video file."""
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(path), fourcc, fps, (width, height))

    for i in range(num_frames):
        # Create a frame with varying color
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :, 0] = (i * 8) % 256  # Blue channel varies
        frame[:, :, 1] = 128  # Green channel constant
        frame[:, :, 2] = 64  # Red channel constant
        out.write(frame)

    out.release()


class TestExtractFrames:
    """Tests for frame extraction."""

    def test_extracts_correct_number_of_frames(self) -> None:
        """Test that correct number of frames is extracted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            create_test_video(video_path, num_frames=100)

            frames = extract_frames(video_path, num_frames=8)

            assert len(frames) == 8

    def test_frames_are_numpy_arrays(self) -> None:
        """Test that frames are numpy arrays."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            create_test_video(video_path, num_frames=30)

            frames = extract_frames(video_path, num_frames=4)

            assert all(isinstance(f, np.ndarray) for f in frames)
            assert all(f.shape[2] == 3 for f in frames)  # 3 color channels

    def test_raises_error_for_nonexistent_file(self) -> None:
        """Test that VideoProcessingError is raised for missing file."""
        with pytest.raises(VideoProcessingError) as exc_info:
            extract_frames("/nonexistent/video.mp4")

        assert "not found" in str(exc_info.value)

    def test_handles_short_video(self) -> None:
        """Test extraction from video with fewer frames than requested."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "short.mp4"
            create_test_video(video_path, num_frames=5)

            frames = extract_frames(video_path, num_frames=10)

            # Should return all available frames
            assert len(frames) <= 5


class TestFrameToBase64:
    """Tests for base64 encoding."""

    def test_returns_base64_string(self) -> None:
        """Test that output is a base64 string."""
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = frame_to_base64(frame)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_can_decode_result(self) -> None:
        """Test that result can be decoded back."""
        import base64

        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[:, :, 1] = 255  # Green image

        result = frame_to_base64(frame)
        decoded = base64.b64decode(result)

        assert len(decoded) > 0


class TestExtractFramesAsBase64:
    """Tests for combined extraction and encoding."""

    def test_returns_base64_strings(self) -> None:
        """Test that output is list of base64 strings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            create_test_video(video_path, num_frames=30)

            results = extract_frames_as_base64(video_path, num_frames=4)

            assert len(results) == 4
            assert all(isinstance(r, str) for r in results)
