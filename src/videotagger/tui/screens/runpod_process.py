"""RunPod remote processing screen."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import LoadingIndicator, OptionList, ProgressBar, Static
from textual.widgets.option_list import Option


class RunPodProcessScreen(Screen):
    """Screen for processing videos stored on RunPod S3."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("space", "toggle", "Toggle", show=False),
        Binding("a", "select_all", "All", show=False),
        Binding("enter", "process", "Process", show=False),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("escape", "back", "Back", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.videos: list = []
        self.selected: set[int] = set()

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        with Container(id="main-container"):
            yield Static("RunPod S3 Videos", classes="title")
            yield Static("Loading...", id="status", classes="subtitle")
            yield LoadingIndicator(id="loader")
            yield OptionList(id="video-list")
            yield Static(
                "Space Toggle | a All | Enter Process | r Refresh | Esc Back",
                classes="help-text",
            )

    def on_mount(self) -> None:
        """Load videos on mount."""
        self.query_one("#video-list", OptionList).display = False
        self.run_worker(self._load_videos, thread=True, exclusive=True)

    def _load_videos(self) -> list:
        """Load videos from S3 (runs in thread)."""
        from videotagger.runpod_processor import list_remote_videos

        try:
            return list_remote_videos()
        except Exception:
            return []

    def on_worker_state_changed(self, event) -> None:
        """Handle worker completion."""
        if event.worker.name == "_load_videos" and event.worker.state.name == "SUCCESS":
            self.videos = event.worker.result or []
            self._populate_list()

        elif event.worker.name == "_process_selected" and event.worker.state.name == "SUCCESS":
            results = event.worker.result or []
            success = sum(1 for _, tags, err in results if tags is not None)
            failed = sum(1 for _, tags, err in results if err is not None)

            if failed == 0:
                self.app.notify(f"Processed {success} videos", severity="information")
            else:
                self.app.notify(f"Processed {success}, failed {failed}", severity="warning")

    def _populate_list(self) -> None:
        """Populate the video list."""
        status = self.query_one("#status", Static)
        loader = self.query_one("#loader", LoadingIndicator)
        video_list = self.query_one("#video-list", OptionList)

        loader.display = False
        video_list.display = True

        if not self.videos:
            status.update("No videos on S3. Upload from Synology first.")
            return

        status.update(f"{len(self.videos)} videos on RunPod S3")

        video_list.clear_options()
        for i, video in enumerate(self.videos):
            label = f"[ ] {video.filename} ({video.size_display})"
            video_list.add_option(Option(label, id=str(i)))

        video_list.focus()

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        self.query_one("#video-list", OptionList).action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        self.query_one("#video-list", OptionList).action_cursor_up()

    def action_toggle(self) -> None:
        """Toggle selection."""
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

    def action_select_all(self) -> None:
        """Toggle select all."""
        if len(self.selected) == len(self.videos):
            self.selected.clear()
        else:
            self.selected = set(range(len(self.videos)))

        for i in range(len(self.videos)):
            self._update_label(i)

    def _update_label(self, idx: int) -> None:
        """Update option label."""
        video_list = self.query_one("#video-list", OptionList)
        video = self.videos[idx]
        mark = "[x]" if idx in self.selected else "[ ]"
        label = f"{mark} {video.filename} ({video.size_display})"
        video_list.replace_option_prompt_at_index(idx, label)

    def action_process(self) -> None:
        """Process selected videos."""
        if not self.selected:
            video_list = self.query_one("#video-list", OptionList)
            if video_list.highlighted is not None:
                self.selected.add(video_list.highlighted)

        if not self.selected:
            self.app.notify("No videos selected", severity="warning")
            return

        selected_videos = [self.videos[i] for i in sorted(self.selected)]
        self.app.push_screen(RunPodProcessingScreen(selected_videos))

    def action_refresh(self) -> None:
        """Refresh video list."""
        self.selected.clear()
        self.query_one("#loader", LoadingIndicator).display = True
        self.query_one("#video-list", OptionList).display = False
        self.query_one("#status", Static).update("Refreshing...")
        self.run_worker(self._load_videos, thread=True, exclusive=True)

    def action_back(self) -> None:
        """Go back."""
        self.app.pop_screen()


class RunPodProcessingScreen(Screen):
    """Screen showing processing progress."""

    BINDINGS = [
        Binding("ctrl+c", "cancel", "Cancel", show=False),
    ]

    def __init__(self, videos: list) -> None:
        super().__init__()
        self.videos = videos
        self._cancelled = False
        self._results: list = []

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        with Container(id="main-container"):
            yield Static("Processing on RunPod", classes="title")
            yield Static(f"0/{len(self.videos)}", id="progress-text", classes="subtitle")
            yield ProgressBar(total=100, show_eta=True, id="progress-bar")
            yield Static("", id="current-file", classes="help-text")
            yield LoadingIndicator()
            yield Static("Ctrl+C Cancel", classes="help-text")

    def on_mount(self) -> None:
        """Start processing."""
        self.run_worker(self._process_all, thread=True, exclusive=True)

    def action_cancel(self) -> None:
        """Cancel processing."""
        self._cancelled = True
        self.app.notify("Cancelled", severity="warning")
        self.app.pop_screen()

    def _process_all(self) -> list:
        """Process all videos (runs in thread)."""
        from videotagger.runpod_processor import process_remote_video

        results = []

        for i, video in enumerate(self.videos):
            if self._cancelled:
                break

            # Update UI
            self.app.call_from_thread(
                self._update_progress,
                i,
                f"Processing: {video.filename}",
            )

            try:
                tags = process_remote_video(video)
                results.append((video, tags, None))

            except Exception as e:
                self.app.call_from_thread(
                    self.app.notify,
                    f"Error: {video.filename}: {e}",
                    severity="error",
                )
                results.append((video, None, str(e)))

        # Show review screen
        self.app.call_from_thread(self._show_review, results)
        return results

    def _update_progress(self, index: int, status: str) -> None:
        """Update progress display."""
        self.query_one("#progress-text", Static).update(f"{index + 1}/{len(self.videos)}")
        self.query_one("#current-file", Static).update(status)
        self.query_one("#progress-bar", ProgressBar).update(
            progress=((index + 1) / len(self.videos)) * 100
        )

    def _show_review(self, results: list) -> None:
        """Show the batch review screen."""
        from videotagger.tui.screens.batch_review import BatchReviewScreen

        self.app.switch_screen(BatchReviewScreen(results))
