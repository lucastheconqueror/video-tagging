"""RunPod S3 sync screen for uploading videos."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import LoadingIndicator, OptionList, ProgressBar, Static
from textual.widgets.option_list import Option


class RunPodSyncScreen(Screen):
    """Screen for syncing videos from Synology to RunPod S3."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("space", "toggle", "Toggle", show=False),
        Binding("a", "select_all", "All", show=False),
        Binding("u", "upload", "Upload Selected", show=False),
        Binding("c", "check_existing", "Check Existing", show=False),
        Binding("escape", "back", "Back", show=False),
    ]

    def __init__(self, videos: list) -> None:
        """Initialize with list of VideoFileInfo from Synology."""
        super().__init__()
        self.videos = videos
        self.selected: set[int] = set()
        self.existing_on_s3: set[str] = set()

    def compose(self) -> ComposeResult:
        """Compose the sync screen."""
        with Container(id="main-container"):
            yield Static("Sync to RunPod S3", classes="title")
            yield Static(f"{len(self.videos)} videos selected", id="status", classes="subtitle")
            yield OptionList(id="video-list")
            yield Static(
                "Space Toggle | a All | u Upload | c Check S3 | Esc Back",
                classes="help-text",
            )

    def on_mount(self) -> None:
        """Populate list on mount."""
        video_list = self.query_one("#video-list", OptionList)

        for i, video in enumerate(self.videos):
            label = f"[ ] {video.filename} ({video.size_display})"
            video_list.add_option(Option(label, id=str(i)))
            self.selected.add(i)  # Select all by default

        self._update_all_labels()
        video_list.focus()

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        self.query_one("#video-list", OptionList).action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        self.query_one("#video-list", OptionList).action_cursor_up()

    def action_toggle(self) -> None:
        """Toggle selection of current item."""
        video_list = self.query_one("#video-list", OptionList)
        if video_list.highlighted is None:
            return

        idx = video_list.highlighted
        if idx in self.selected:
            self.selected.discard(idx)
        else:
            self.selected.add(idx)

        self._update_label(idx)
        video_list.action_cursor_down()
        self._update_status()

    def action_select_all(self) -> None:
        """Toggle select all."""
        if len(self.selected) == len(self.videos):
            self.selected.clear()
        else:
            self.selected = set(range(len(self.videos)))

        self._update_all_labels()
        self._update_status()

    def _update_label(self, idx: int) -> None:
        """Update single option label."""
        video_list = self.query_one("#video-list", OptionList)
        video = self.videos[idx]

        # Check mark
        mark = "[x]" if idx in self.selected else "[ ]"

        # S3 status indicator
        remote_key = f"videos/{video.filename}"
        if remote_key in self.existing_on_s3:
            s3_mark = " [S3]"
        else:
            s3_mark = ""

        label = f"{mark} {video.filename} ({video.size_display}){s3_mark}"
        video_list.replace_option_prompt_at_index(idx, label)

    def _update_all_labels(self) -> None:
        """Update all option labels."""
        for i in range(len(self.videos)):
            self._update_label(i)

    def _update_status(self) -> None:
        """Update status text."""
        status = self.query_one("#status", Static)
        total_size = sum(self.videos[i].size for i in self.selected) / (1024 * 1024 * 1024)
        status.update(f"{len(self.selected)} selected ({total_size:.1f} GB)")

    def action_check_existing(self) -> None:
        """Check which videos already exist on S3."""
        self.app.notify("Checking S3...", severity="information")
        self.run_worker(self._check_s3, thread=True, exclusive=True)

    def _check_s3(self) -> set[str]:
        """Check S3 for existing files (runs in thread)."""
        from videotagger.runpod_s3 import get_runpod_s3_client

        try:
            client = get_runpod_s3_client()
            files = client.list_files(prefix="videos/")
            return {f["key"] for f in files}
        except Exception:
            return set()

    def on_worker_state_changed(self, event) -> None:
        """Handle worker completion."""
        if event.worker.name == "_check_s3" and event.worker.state.name == "SUCCESS":
            self.existing_on_s3 = event.worker.result or set()
            self._update_all_labels()

            existing_count = sum(
                1
                for i in range(len(self.videos))
                if f"videos/{self.videos[i].filename}" in self.existing_on_s3
            )
            self.app.notify(f"{existing_count} videos already on S3", severity="information")

        elif event.worker.name == "_upload_selected" and event.worker.state.name == "SUCCESS":
            success, failed = event.worker.result
            if failed == 0:
                self.app.notify(f"Uploaded {success} videos", severity="information")
            else:
                self.app.notify(f"Uploaded {success}, failed {failed}", severity="warning")

            # Refresh S3 status
            self.run_worker(self._check_s3, thread=True, exclusive=True)

    def action_upload(self) -> None:
        """Upload selected videos."""
        if not self.selected:
            self.app.notify("No videos selected", severity="warning")
            return

        # Filter out already uploaded
        to_upload = []
        for idx in self.selected:
            video = self.videos[idx]
            remote_key = f"videos/{video.filename}"
            if remote_key not in self.existing_on_s3:
                to_upload.append(video)

        if not to_upload:
            self.app.notify("All selected videos already on S3", severity="information")
            return

        self.app.notify(f"Uploading {len(to_upload)} videos...", severity="information")
        self.app.push_screen(UploadProgressScreen(to_upload))

    def action_back(self) -> None:
        """Go back."""
        self.app.pop_screen()


class UploadProgressScreen(Screen):
    """Screen showing upload progress."""

    BINDINGS = [
        Binding("ctrl+c", "cancel", "Cancel", show=False),
    ]

    def __init__(self, videos: list) -> None:
        super().__init__()
        self.videos = videos
        self._cancelled = False
        self._current_idx = 0

    def compose(self) -> ComposeResult:
        """Compose the upload screen."""
        with Container(id="main-container"):
            yield Static("Uploading to RunPod S3", classes="title")
            yield Static(
                f"Uploading 0/{len(self.videos)}...",
                id="progress-text",
                classes="subtitle",
            )
            yield ProgressBar(total=100, show_eta=True, id="progress-bar")
            yield Static("", id="current-file", classes="help-text")
            yield LoadingIndicator()
            yield Static("Ctrl+C Cancel", classes="help-text")

    def on_mount(self) -> None:
        """Start upload."""
        self.run_worker(self._upload_all, thread=True, exclusive=True)

    def action_cancel(self) -> None:
        """Cancel upload."""
        self._cancelled = True
        self.app.notify("Cancelled", severity="warning")
        self.app.pop_screen()

    def _upload_all(self) -> tuple[int, int]:
        """Upload all videos (runs in thread)."""
        from videotagger.runpod_s3 import get_runpod_s3_client
        from videotagger.synology import get_synology_client

        success = 0
        failed = 0

        try:
            s3_client = get_runpod_s3_client()

            with get_synology_client() as synology:
                for i, video in enumerate(self.videos):
                    if self._cancelled:
                        break

                    self._current_idx = i

                    # Update UI from thread
                    self.app.call_from_thread(
                        self._update_progress,
                        i,
                        f"Downloading: {video.filename}",
                    )

                    # Download from Synology
                    local_path = synology.download_video(video)

                    if self._cancelled:
                        break

                    self.app.call_from_thread(
                        self._update_progress,
                        i,
                        f"Uploading: {video.filename}",
                    )

                    # Upload to S3
                    result = s3_client.upload_file(local_path)

                    if result.success:
                        success += 1
                    else:
                        failed += 1
                        self.app.call_from_thread(
                            self.app.notify,
                            f"Failed: {video.filename}",
                            severity="error",
                        )

                    # Clean up local file
                    try:
                        local_path.unlink()
                    except Exception:
                        pass

        except Exception as e:
            self.app.call_from_thread(
                self.app.notify,
                f"Error: {e}",
                severity="error",
            )

        # Done - go back
        self.app.call_from_thread(self.app.pop_screen)

        return success, failed

    def _update_progress(self, index: int, status: str) -> None:
        """Update progress display."""
        progress_text = self.query_one("#progress-text", Static)
        current_file = self.query_one("#current-file", Static)
        progress_bar = self.query_one("#progress-bar", ProgressBar)

        progress_text.update(f"Uploading {index + 1}/{len(self.videos)}...")
        current_file.update(status)
        progress_bar.update(progress=((index + 1) / len(self.videos)) * 100)
