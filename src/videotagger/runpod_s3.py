"""RunPod S3-compatible storage client for uploading videos.

Uploads videos to RunPod network volume via S3 API for processing on GPU pods.
"""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from videotagger.config import RunPodS3Config, get_settings

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """Result of an S3 upload operation."""

    success: bool
    local_path: str
    remote_key: str
    error: str | None = None
    bytes_uploaded: int = 0


class RunPodS3Client:
    """Client for uploading files to RunPod network volume via S3."""

    def __init__(self, config: RunPodS3Config | None = None) -> None:
        """Initialize the S3 client.

        Args:
            config: Optional RunPodS3Config. If None, loads from Settings.
        """
        if config is None:
            config = get_settings().runpod_s3
        self.config = config
        self._client = None

        # Extract region from endpoint URL (e.g., eu-ro-1 from s3api-eu-ro-1.runpod.io)
        match = re.search(r"s3api-([^.]+)\.runpod\.io", config.endpoint)
        self.region = match.group(1).upper() if match else "EU-RO-1"

    def _get_client(self):
        """Get or create boto3 S3 client."""
        if self._client is None:
            self._client = boto3.client(
                "s3",
                aws_access_key_id=self.config.access_key,
                aws_secret_access_key=self.config.secret_key,
                region_name=self.region,
                endpoint_url=self.config.endpoint,
                config=BotoConfig(
                    signature_version="s3v4",
                    retries={"max_attempts": 3, "mode": "adaptive"},
                ),
            )
            logger.info(f"Created S3 client for {self.config.endpoint}")
        return self._client

    def upload_file(
        self,
        local_path: str | Path,
        remote_key: str | None = None,
        progress_callback: Callable[[int], None] | None = None,
    ) -> UploadResult:
        """Upload a file to RunPod network volume.

        Args:
            local_path: Path to local file.
            remote_key: S3 object key (path on volume). If None, uses filename.
            progress_callback: Optional callback(bytes_transferred) for progress.

        Returns:
            UploadResult with success status and details.
        """
        local_path = Path(local_path)

        if not local_path.exists():
            return UploadResult(
                success=False,
                local_path=str(local_path),
                remote_key=remote_key or "",
                error=f"File not found: {local_path}",
            )

        if remote_key is None:
            remote_key = f"videos/{local_path.name}"

        file_size = local_path.stat().st_size
        size_mb = file_size / 1024 / 1024
        logger.info(f"Uploading {local_path.name} ({size_mb:.1f} MB) to {remote_key}")

        try:
            client = self._get_client()

            # Create callback wrapper for boto3
            callback = None
            if progress_callback:

                class ProgressTracker:
                    def __init__(self, cb):
                        self.bytes_transferred = 0
                        self.cb = cb

                    def __call__(self, bytes_amount):
                        self.bytes_transferred += bytes_amount
                        self.cb(self.bytes_transferred)

                callback = ProgressTracker(progress_callback)

            client.upload_file(
                str(local_path),
                self.config.bucket,
                remote_key,
                Callback=callback,
            )

            logger.info(f"Uploaded: {remote_key}")
            return UploadResult(
                success=True,
                local_path=str(local_path),
                remote_key=remote_key,
                bytes_uploaded=file_size,
            )

        except ClientError as e:
            error_msg = str(e)
            logger.error(f"Upload failed: {error_msg}")
            return UploadResult(
                success=False,
                local_path=str(local_path),
                remote_key=remote_key,
                error=error_msg,
            )

    def list_files(self, prefix: str = "videos/") -> list[dict]:
        """List files in the network volume.

        Args:
            prefix: S3 prefix to filter objects.

        Returns:
            List of dicts with 'key', 'size', 'last_modified'.
        """
        try:
            client = self._get_client()
            response = client.list_objects_v2(
                Bucket=self.config.bucket,
                Prefix=prefix,
            )

            files = []
            for obj in response.get("Contents", []):
                files.append(
                    {
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"],
                    }
                )

            logger.info(f"Listed {len(files)} files with prefix '{prefix}'")
            return files

        except ClientError as e:
            logger.error(f"List failed: {e}")
            return []

    def file_exists(self, remote_key: str) -> bool:
        """Check if a file exists on the network volume.

        Args:
            remote_key: S3 object key to check.

        Returns:
            True if file exists, False otherwise.
        """
        try:
            client = self._get_client()
            client.head_object(Bucket=self.config.bucket, Key=remote_key)
            return True
        except ClientError:
            return False

    def delete_file(self, remote_key: str) -> bool:
        """Delete a file from the network volume.

        Args:
            remote_key: S3 object key to delete.

        Returns:
            True if deleted successfully, False otherwise.
        """
        try:
            client = self._get_client()
            client.delete_object(Bucket=self.config.bucket, Key=remote_key)
            logger.info(f"Deleted: {remote_key}")
            return True
        except ClientError as e:
            logger.error(f"Delete failed: {e}")
            return False


def get_runpod_s3_client() -> RunPodS3Client:
    """Get a new RunPod S3 client instance.

    Returns:
        Configured RunPodS3Client.
    """
    return RunPodS3Client()
