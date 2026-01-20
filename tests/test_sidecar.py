"""Tests for sidecar file management."""

import tempfile
from pathlib import Path

from videotagger.sidecar import (
    get_sidecar_info,
    get_sidecar_path,
    has_sidecar,
    read_sidecar,
    write_sidecar,
)


class TestGetSidecarPath:
    """Tests for sidecar path generation."""

    def test_replaces_video_extension_with_json(self) -> None:
        """Test that video extension is replaced with .json."""
        result = get_sidecar_path("/path/to/video.mp4")
        assert result == Path("/path/to/video.json")

    def test_handles_different_extensions(self) -> None:
        """Test with various video extensions."""
        assert get_sidecar_path("video.mov") == Path("video.json")
        assert get_sidecar_path("video.avi") == Path("video.json")
        assert get_sidecar_path("video.mkv") == Path("video.json")


class TestHasSidecar:
    """Tests for sidecar existence check."""

    def test_returns_false_when_no_sidecar(self) -> None:
        """Test with non-existent sidecar."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "video.mp4"
            video_path.touch()

            assert has_sidecar(video_path) is False

    def test_returns_true_when_sidecar_exists(self) -> None:
        """Test with existing sidecar."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "video.mp4"
            sidecar_path = Path(tmpdir) / "video.json"
            video_path.touch()
            sidecar_path.write_text("{}")

            assert has_sidecar(video_path) is True


class TestWriteAndReadSidecar:
    """Tests for writing and reading sidecar files."""

    def test_write_creates_sidecar_file(self) -> None:
        """Test that write_sidecar creates a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test_video.mp4"
            video_path.touch()

            tags = {"setting": "Gym", "content_type": "tutorial"}
            sidecar_path = write_sidecar(video_path, tags)

            assert sidecar_path.exists()
            assert sidecar_path.suffix == ".json"

    def test_read_returns_written_data(self) -> None:
        """Test that read returns the written data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test_video.mp4"
            video_path.touch()

            tags = {"setting": "Office", "key_text": ["test", "data"]}
            write_sidecar(video_path, tags, airtable_updated=True)

            data = read_sidecar(video_path)

            assert data is not None
            assert data["tags"] == tags
            assert data["airtable_updated"] is True
            assert "processed_at" in data
            assert data["video_file"] == "test_video.mp4"

    def test_read_returns_none_for_missing_sidecar(self) -> None:
        """Test that read returns None when no sidecar exists."""
        result = read_sidecar("/nonexistent/video.mp4")
        assert result is None


class TestGetSidecarInfo:
    """Tests for sidecar info display."""

    def test_returns_formatted_info(self) -> None:
        """Test that info is formatted correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "video.mp4"
            video_path.touch()

            write_sidecar(video_path, {"test": "data"}, airtable_updated=True)

            info = get_sidecar_info(video_path)

            assert info is not None
            assert "Processed:" in info
            assert "Airtable updated: yes" in info

    def test_returns_none_for_missing_sidecar(self) -> None:
        """Test that None is returned when no sidecar exists."""
        info = get_sidecar_info("/nonexistent/video.mp4")
        assert info is None
