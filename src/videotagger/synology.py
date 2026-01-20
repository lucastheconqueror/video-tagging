"""Synology NAS integration for VideoTagger.

Provides SFTP connection to list and download videos from Synology NAS.
"""

import logging
import stat
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import paramiko

from videotagger.config import SynologyConfig, get_settings
from videotagger.exceptions import SynologyConnectionError, SynologyFileError

logger = logging.getLogger(__name__)


@dataclass
class VideoFileInfo:
    """Information about a video file on Synology."""

    filename: str
    size: int
    modified: datetime
    full_path: str

    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        return self.size / (1024 * 1024)

    @property
    def size_display(self) -> str:
        """Human-readable size."""
        if self.size_mb >= 1000:
            return f"{self.size_mb / 1024:.1f} GB"
        return f"{self.size_mb:.1f} MB"


class SynologyClient:
    """Client for connecting to Synology NAS via SFTP."""

    def __init__(self, config: SynologyConfig | None = None) -> None:
        """Initialize the Synology client.

        Args:
            config: Optional SynologyConfig. If None, loads from Settings.
        """
        if config is None:
            config = get_settings().synology
        self.config = config
        self._ssh: paramiko.SSHClient | None = None
        self._sftp: paramiko.SFTPClient | None = None

    def connect(self) -> None:
        """Establish SSH/SFTP connection to Synology.

        Raises:
            SynologyConnectionError: If connection fails.
        """
        if self._sftp is not None:
            return  # Already connected

        logger.info(f"Connecting to Synology: {self.config.host}")

        try:
            self._ssh = paramiko.SSHClient()
            self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self._ssh.connect(
                hostname=self.config.host,
                username=self.config.user,
                password=self.config.password,
                timeout=30,
            )

            self._sftp = self._ssh.open_sftp()
            logger.info("Connected to Synology successfully")

        except paramiko.AuthenticationException as e:
            logger.error(f"Authentication failed: {e}")
            raise SynologyConnectionError(
                f"Authentication failed for {self.config.user}@{self.config.host}", e
            ) from e

        except paramiko.SSHException as e:
            logger.error(f"SSH connection failed: {e}")
            raise SynologyConnectionError(f"SSH connection failed: {e}", e) from e

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise SynologyConnectionError(f"Failed to connect to Synology: {e}", e) from e

    def disconnect(self) -> None:
        """Close the SFTP/SSH connection."""
        if self._sftp:
            self._sftp.close()
            self._sftp = None

        if self._ssh:
            self._ssh.close()
            self._ssh = None

        logger.info("Disconnected from Synology")

    def __enter__(self) -> "SynologyClient":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()

    def list_videos(
        self,
        recursive: bool = True,
        max_depth: int = 5,
        progress_callback: Callable[[str, int], None] | None = None,
    ) -> list[VideoFileInfo]:
        """List video files in the configured directory.

        Searches for files matching pattern: V - *.mp4

        Args:
            recursive: If True, search subdirectories recursively.
            max_depth: Maximum directory depth to search (default 5).
            progress_callback: Optional callback(current_dir, videos_found) for progress updates.

        Returns:
            List of VideoFileInfo objects for matching files.

        Raises:
            SynologyConnectionError: If not connected.
            SynologyFileError: If listing fails.
        """
        if self._sftp is None:
            raise SynologyConnectionError("Not connected to Synology")

        video_path = self.config.video_path
        logger.info(f"Searching for videos in: {video_path} (recursive={recursive})")

        self._scan_stats = {"dirs": 0, "videos": 0}
        videos = self._scan_directory(video_path, recursive, max_depth, 0, progress_callback)

        # Sort by modification time (newest first)
        videos.sort(key=lambda v: v.modified, reverse=True)

        dirs_scanned = self._scan_stats["dirs"]
        logger.info(f"Found {len(videos)} matching videos in {dirs_scanned} directories")
        return videos

    def _scan_directory(
        self,
        path: str,
        recursive: bool,
        max_depth: int,
        current_depth: int,
        progress_callback: Callable[[str, int], None] | None = None,
    ) -> list[VideoFileInfo]:
        """Recursively scan directory for V - *.mp4 files."""
        videos = []

        if current_depth > max_depth:
            return videos

        self._scan_stats["dirs"] += 1

        # Get short path for display
        short_path = path.split("/")[-1] if "/" in path else path
        if progress_callback:
            progress_callback(short_path, self._scan_stats["videos"])

        try:
            files = self._sftp.listdir_attr(path)
        except FileNotFoundError:
            logger.warning(f"Directory not found: {path}")
            return videos
        except Exception as e:
            logger.warning(f"Failed to list {path}: {e}")
            return videos

        for file_attr in files:
            filename = file_attr.filename

            # Skip hidden files/directories
            if filename.startswith("."):
                continue

            full_path = f"{path}/{filename}"

            # Check if directory
            if file_attr.st_mode and stat.S_ISDIR(file_attr.st_mode):
                if recursive:
                    videos.extend(
                        self._scan_directory(
                            full_path, recursive, max_depth, current_depth + 1, progress_callback
                        )
                    )
                continue

            # Check if matches V - *.mp4 pattern
            if not (filename.lower().startswith("v -") and filename.lower().endswith(".mp4")):
                continue

            # Get modification time
            mtime = datetime.fromtimestamp(file_attr.st_mtime or 0)

            videos.append(
                VideoFileInfo(
                    filename=filename,
                    size=file_attr.st_size or 0,
                    modified=mtime,
                    full_path=full_path,
                )
            )
            self._scan_stats["videos"] += 1

        return videos

    def download_video(
        self,
        video: VideoFileInfo | str,
        local_path: str | Path | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Path:
        """Download a video file from Synology.

        Args:
            video: VideoFileInfo object or remote path.
            local_path: Local path to save to. If None, uses temp directory.
            progress_callback: Optional callback(bytes_transferred, total_bytes).

        Returns:
            Path to the downloaded file.

        Raises:
            SynologyConnectionError: If not connected.
            SynologyFileError: If download fails.
        """
        if self._sftp is None:
            raise SynologyConnectionError("Not connected to Synology")

        if isinstance(video, VideoFileInfo):
            remote_path = video.full_path
            filename = video.filename
        else:
            remote_path = video
            filename = Path(video).name

        # Determine local path
        if local_path is None:
            local_path = Path(tempfile.gettempdir()) / filename
        else:
            local_path = Path(local_path)

        logger.info(f"Downloading: {filename} -> {local_path}")

        try:
            self._sftp.get(
                remote_path,
                str(local_path),
                callback=progress_callback,
            )

            logger.info(f"Downloaded: {local_path}")
            return local_path

        except FileNotFoundError as e:
            raise SynologyFileError(f"File not found: {remote_path}", remote_path) from e

        except Exception as e:
            raise SynologyFileError(f"Download failed: {e}", remote_path) from e


def get_synology_client() -> SynologyClient:
    """Get a new Synology client instance.

    Returns:
        Configured SynologyClient (not yet connected).
    """
    return SynologyClient()
