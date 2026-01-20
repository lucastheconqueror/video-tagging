"""Synology NAS browser screen."""

from datetime import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import LoadingIndicator, OptionList, Static
from textual.widgets.option_list import Option


class SynologyBrowserScreen(Screen):
    """Screen for browsing and selecting videos from Synology NAS."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("enter", "select", "Download & Process", show=True),
        Binding("space", "toggle", "Toggle Select", show=True),
        Binding("a", "select_all", "Select All", show=True),
        Binding("escape", "back", "Back", show=True),
        Binding("r", "refresh", "Refresh (clear cache)", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.videos: list = []
        self.selected: set[int] = set()

    def compose(self) -> ComposeResult:
        """Compose the browser screen."""
        with Container(id="main-container"):
            yield Static("Synology NAS Browser", classes="title")
            yield Static("Connecting...", id="status", classes="subtitle")
            yield LoadingIndicator(id="loader")
            yield OptionList(id="video-list")
            yield Static(
                "[j/k] Navigate | [Space] Toggle | [a] All | [Enter] Process | [r] Refresh",
                classes="help-text",
            )

    def on_mount(self) -> None:
        """Load videos when mounted."""
        self.query_one("#video-list", OptionList).display = False
        self._use_cache = True
        # Use thread=True for blocking I/O
        self.run_worker(self._load_videos_sync, thread=True, exclusive=True)

    def _load_videos_sync(self) -> list | str:
        """Load video list from Synology (runs in thread)."""
        from videotagger.cache import clear_cache, get_cached_videos, set_cached_videos
        from videotagger.exceptions import SynologyConnectionError, SynologyFileError
        from videotagger.synology import get_synology_client

        # Try cache first
        if self._use_cache:
            cached = get_cached_videos()
            if cached:
                return ("cached", cached)
        else:
            clear_cache()

        try:
            with get_synology_client() as client:
                videos = client.list_videos()

            # Cache the results
            cache_data = [
                {
                    "filename": v.filename,
                    "size": v.size,
                    "modified": v.modified.isoformat(),
                    "full_path": v.full_path,
                }
                for v in videos
            ]
            set_cached_videos(cache_data)

            return ("fresh", cache_data)

        except (SynologyConnectionError, SynologyFileError) as e:
            return ("error", str(e))

    def on_worker_state_changed(self, event) -> None:
        """Handle worker completion."""
        from videotagger.synology import VideoFileInfo

        if event.worker.name != "_load_videos_sync":
            return

        if event.worker.state.name != "SUCCESS":
            return

        result = event.worker.result
        if result is None:
            return

        status = self.query_one("#status", Static)
        loader = self.query_one("#loader", LoadingIndicator)
        video_list = self.query_one("#video-list", OptionList)

        result_type, data = result

        if result_type == "error":
            loader.display = False
            status.update(f"Error: {data}")
            self.app.notify(data, severity="error")
            return

        # Convert cache data to VideoFileInfo objects
        self.videos = [
            VideoFileInfo(
                filename=v["filename"],
                size=v["size"],
                modified=datetime.fromisoformat(v["modified"]),
                full_path=v["full_path"],
            )
            for v in data
        ]

        from_cache = result_type == "cached"
        self._populate_list(status, loader, video_list, from_cache=from_cache)

    def _populate_list(
        self, status: Static, loader: LoadingIndicator, video_list: OptionList, from_cache: bool
    ) -> None:
        """Populate the video list widget."""
        loader.display = False
        video_list.display = True

        if not self.videos:
            status.update("No matching videos found")
            return

        cache_note = " (cached)" if from_cache else ""
        status.update(f"Found {len(self.videos)} videos{cache_note}")

        # Populate the list
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
        """Toggle selection of current item."""
        video_list = self.query_one("#video-list", OptionList)
        if video_list.highlighted is None:
            return

        idx = video_list.highlighted

        if idx in self.selected:
            self.selected.discard(idx)
        else:
            self.selected.add(idx)

        self._update_option_label(idx)
        video_list.action_cursor_down()

    def action_select_all(self) -> None:
        """Toggle select all."""
        if len(self.selected) == len(self.videos):
            # Deselect all
            self.selected.clear()
        else:
            # Select all
            self.selected = set(range(len(self.videos)))

        for i in range(len(self.videos)):
            self._update_option_label(i)

        self.app.notify(f"Selected {len(self.selected)} videos")

    def _update_option_label(self, idx: int) -> None:
        """Update the option label to show selection state."""
        video_list = self.query_one("#video-list", OptionList)
        video = self.videos[idx]
        marker = "[x]" if idx in self.selected else "[ ]"
        label = f"{marker} {video.filename} ({video.size_display})"

        # Replace the option
        video_list.replace_option_prompt_at_index(idx, label)

    def action_select(self) -> None:
        """Process selected videos."""
        if not self.selected:
            # If nothing selected, use highlighted
            video_list = self.query_one("#video-list", OptionList)
            if video_list.highlighted is not None:
                self.selected.add(video_list.highlighted)

        if not self.selected:
            self.app.notify("No videos selected", severity="warning")
            return

        # Get selected videos
        selected_videos = [self.videos[i] for i in sorted(self.selected)]
        self.app.push_screen(SynologyDownloadScreen(selected_videos))

    def action_back(self) -> None:
        """Go back to menu."""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Refresh the video list (clears cache)."""
        self.selected.clear()
        self.query_one("#loader", LoadingIndicator).display = True
        self.query_one("#video-list", OptionList).display = False
        self.query_one("#status", Static).update("Refreshing (scanning ~40s)...")
        self._use_cache = False
        self.run_worker(self._load_videos_sync, thread=True, exclusive=True)


class SynologyDownloadScreen(Screen):
    """Screen for downloading and processing selected videos."""

    BINDINGS = [
        Binding("ctrl+c", "cancel", "Cancel", show=True),
    ]

    def __init__(self, videos: list) -> None:
        super().__init__()
        self.videos = videos
        self.current_index = 0
        self._cancelled = False

    def compose(self) -> ComposeResult:
        """Compose the download screen."""
        with Container(id="main-container"):
            yield Static("Downloading Videos", classes="title")
            yield Static(
                f"Processing 0/{len(self.videos)}...",
                id="progress",
                classes="subtitle",
            )
            yield LoadingIndicator()
            yield Static("", id="current-file", classes="help-text")
            yield Static("[Ctrl+C] Cancel", classes="help-text")

    def on_mount(self) -> None:
        """Start downloading."""
        self.run_worker(self._download_and_process(), exclusive=True)

    def action_cancel(self) -> None:
        """Cancel the operation."""
        self._cancelled = True
        self.app.notify("Cancelled", severity="warning")
        self.app.pop_screen()

    async def _download_and_process(self) -> None:
        """Download and process each video."""
        from videotagger.exceptions import SynologyConnectionError, SynologyFileError
        from videotagger.synology import get_synology_client

        progress = self.query_one("#progress", Static)
        current = self.query_one("#current-file", Static)

        try:
            with get_synology_client() as client:
                for i, video in enumerate(self.videos):
                    if self._cancelled:
                        return

                    self.current_index = i
                    progress.update(f"Processing {i + 1}/{len(self.videos)}...")
                    current.update(f"Downloading: {video.filename}")

                    # Download to temp
                    local_path = client.download_video(video)

                    if self._cancelled:
                        return

                    current.update(f"Analyzing: {video.filename}")

                    # Process video
                    from videotagger.exceptions import LLMError, VideoProcessingError
                    from videotagger.pipeline import process_video

                    try:
                        tags = process_video(str(local_path))

                        # For batch, we'll just save sidecars automatically
                        from videotagger.sidecar import write_sidecar

                        write_sidecar(local_path, tags, airtable_updated=False)
                        self.app.notify(f"Processed: {video.filename}", severity="information")

                    except (VideoProcessingError, LLMError) as e:
                        self.app.notify(f"Error: {video.filename}: {e}", severity="error")

            # Done
            self.app.notify(f"Completed {len(self.videos)} videos", severity="information")
            self.app.pop_screen()

        except SynologyConnectionError as e:
            self.app.notify(f"Connection error: {e}", severity="error")
            self.app.pop_screen()

        except SynologyFileError as e:
            self.app.notify(f"File error: {e}", severity="error")
            self.app.pop_screen()
