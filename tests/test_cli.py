"""Tests for CLI commands."""

import os
import tempfile
from unittest.mock import patch

from videotagger.__main__ import validate_config


class TestValidateConfigCommand:
    """Tests for validate-config CLI command."""

    def test_valid_config_returns_success(self) -> None:
        """Test that valid configuration returns exit code 0."""
        # Create a temporary file for SSH key
        with tempfile.NamedTemporaryFile(delete=False, suffix="_test_key") as f:
            temp_key_path = f.name

        try:
            env = {
                "SYNOLOGY_HOST": "nas.local",
                "SYNOLOGY_USER": "admin",
                "SYNOLOGY_PASSWORD": "secretpassword123",
                "SYNOLOGY_VIDEO_PATH": "/volume1/videos",
                "AIRTABLE_API_KEY": "patXXXXXXXXXXXXXX",
                "AIRTABLE_BASE_ID": "appXXXXXXXXXXXXXX",
                "AIRTABLE_TABLE_ID": "tblXXXXXXXXXXXXXX",
                "RUNPOD_S3_ENDPOINT": "https://s3.example.com",
                "RUNPOD_S3_BUCKET": "mybucket",
                "RUNPOD_S3_ACCESS_KEY": "access_key_12345678",
                "RUNPOD_S3_SECRET_KEY": "secret_key_12345678",
                "RUNPOD_SSH_HOST": "ssh.runpod.io",
                "RUNPOD_SSH_USER": "testuser",
                "RUNPOD_SSH_KEY_PATH": temp_key_path,
                "RUNPOD_SSH_POD_ID": "pod123",
            }
            with patch.dict(os.environ, env, clear=True):
                exit_code = validate_config()
                assert exit_code == 0
        finally:
            os.unlink(temp_key_path)

    def test_missing_config_returns_error(self) -> None:
        """Test that missing configuration returns exit code 1."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("videotagger.__main__.load_dotenv"),
        ):
            exit_code = validate_config()
            assert exit_code == 1

    def test_output_contains_masked_credentials(self, capsys) -> None:
        """Test that output shows masked credentials."""
        # Create a temporary file for SSH key
        with tempfile.NamedTemporaryFile(delete=False, suffix="_test_key") as f:
            temp_key_path = f.name

        try:
            env = {
                "SYNOLOGY_HOST": "nas.local",
                "SYNOLOGY_USER": "admin",
                "SYNOLOGY_PASSWORD": "secretpassword123",
                "SYNOLOGY_VIDEO_PATH": "/volume1/videos",
                "AIRTABLE_API_KEY": "patN8u1p9h0EhJZBr",
                "AIRTABLE_BASE_ID": "appXXXXXXXXXXXXXX",
                "AIRTABLE_TABLE_ID": "tblXXXXXXXXXXXXXX",
                "RUNPOD_S3_ENDPOINT": "https://s3.example.com",
                "RUNPOD_S3_BUCKET": "mybucket",
                "RUNPOD_S3_ACCESS_KEY": "access_key_12345678",
                "RUNPOD_S3_SECRET_KEY": "secret_key_12345678",
                "RUNPOD_SSH_HOST": "ssh.runpod.io",
                "RUNPOD_SSH_USER": "testuser",
                "RUNPOD_SSH_KEY_PATH": temp_key_path,
                "RUNPOD_SSH_POD_ID": "pod123",
            }
            with patch.dict(os.environ, env, clear=True):
                validate_config()
                captured = capsys.readouterr()
                # Check that API key is masked
                assert "patN...JZBr" in captured.out
                # Check that password is masked
                assert "secr...d123" in captured.out
        finally:
            os.unlink(temp_key_path)
