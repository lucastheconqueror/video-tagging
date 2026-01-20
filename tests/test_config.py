"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from videotagger.config import (
    RunPodSSHConfig,
    Settings,
    SynologyConfig,
    mask_credential,
)


class TestSynologyConfig:
    """Tests for SynologyConfig model."""

    def test_valid_config_loads(self) -> None:
        """Test that valid config loads successfully."""
        with patch.dict(
            os.environ,
            {
                "SYNOLOGY_HOST": "nas.local",
                "SYNOLOGY_USER": "admin",
                "SYNOLOGY_PASSWORD": "secret123",
                "SYNOLOGY_VIDEO_PATH": "/volume1/videos",
            },
            clear=False,
        ):
            config = SynologyConfig()
            assert config.host == "nas.local"
            assert config.user == "admin"
            assert config.password == "secret123"
            assert config.video_path == "/volume1/videos"

    def test_missing_field_raises_error(self) -> None:
        """Test that missing required field raises ValidationError."""
        with patch.dict(
            os.environ,
            {
                "SYNOLOGY_HOST": "nas.local",
                # Missing other required fields
            },
            clear=True,
        ):
            with pytest.raises(ValidationError) as exc_info:
                SynologyConfig()
            errors = exc_info.value.errors()
            field_names = [e["loc"][0] for e in errors]
            assert "user" in field_names
            assert "password" in field_names


class TestRunPodSSHConfig:
    """Tests for RunPodSSHConfig model with path validation."""

    def test_path_expansion_works(self) -> None:
        """Test that ~ is expanded in SSH key path."""
        # Create a temporary file to use as the key
        with tempfile.NamedTemporaryFile(delete=False, suffix="_test_key") as f:
            temp_key_path = f.name

        try:
            with patch.dict(
                os.environ,
                {
                    "RUNPOD_SSH_HOST": "ssh.runpod.io",
                    "RUNPOD_SSH_USER": "testuser",
                    "RUNPOD_SSH_KEY_PATH": temp_key_path,
                    "RUNPOD_SSH_POD_ID": "pod123",
                },
                clear=False,
            ):
                config = RunPodSSHConfig()
                assert config.key_path == Path(temp_key_path)
                assert config.key_path.is_absolute()
        finally:
            os.unlink(temp_key_path)

    def test_invalid_key_path_raises_error(self) -> None:
        """Test that non-existent SSH key path raises ValidationError."""
        with patch.dict(
            os.environ,
            {
                "RUNPOD_SSH_HOST": "ssh.runpod.io",
                "RUNPOD_SSH_USER": "testuser",
                "RUNPOD_SSH_KEY_PATH": "/nonexistent/path/to/key",
                "RUNPOD_SSH_POD_ID": "pod123",
            },
            clear=False,
        ):
            with pytest.raises(ValidationError) as exc_info:
                RunPodSSHConfig()
            assert "SSH key file not found" in str(exc_info.value)


class TestMaskCredential:
    """Tests for credential masking utility."""

    def test_long_credential_is_masked(self) -> None:
        """Test that long credentials show first/last 4 chars."""
        result = mask_credential("patN8u1p9h0EhJZBr")
        assert result == "patN...JZBr"

    def test_short_credential_is_fully_masked(self) -> None:
        """Test that short credentials are fully masked."""
        result = mask_credential("abc123")
        assert result == "******"

    def test_exactly_8_chars_is_masked(self) -> None:
        """Test boundary case of exactly 8 characters."""
        result = mask_credential("12345678")
        assert result == "********"


class TestSettings:
    """Tests for root Settings class."""

    def test_missing_any_config_raises_error(self) -> None:
        """Test that missing any config group raises ValidationError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                Settings()
