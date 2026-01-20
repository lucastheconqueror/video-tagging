"""Local video processing screen."""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Input, LoadingIndicator, Static


class LocalVideoScreen(Screen):
    """Screen for processing a local video file."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("enter", "submit", "Process", show=True),
        Binding("ctrl+c", "back", "Cancel", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose the local video screen."""
        with Container(id="main-container"):
            yield Static("Process Local Video", classes="title")
            yield Static("Enter path to video file (Tab to autocomplete)", classes="subtitle")

            with Container(id="input-container"):
                yield Input(
                    placeholder="/path/to/video.mp4",
                    id="video-path-input",
                )

            yield Static(
                "[Enter] Process | [Escape] Back | Supports: .mp4 .mov .avi .mkv",
                classes="help-text",
            )

    def on_mount(self) -> None:
        """Focus input on mount."""
        self.query_one(Input).focus()

    def action_back(self) -> None:
        """Go back to menu."""
        self.app.pop_screen()

    def action_submit(self) -> None:
        """Submit the video path."""
        self._process_video()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input."""
        self._process_video()

    def _process_video(self) -> None:
        """Process the video file."""
        input_widget = self.query_one("#video-path-input", Input)
        video_path = input_widget.value.strip()

        if not video_path:
            self.app.notify("Please enter a video path", severity="warning")
            return

        path = Path(video_path).expanduser()
        if not path.exists():
            self.app.notify(f"File not found: {path}", severity="error")
            return

        if path.suffix.lower() not in [".mp4", ".mov", ".avi", ".mkv"]:
            self.app.notify("Unsupported video format", severity="warning")
            return

        # Show processing screen
        self.app.push_screen(ProcessingScreen(str(path)))


class ProcessingScreen(Screen):
    """Screen shown while processing video."""

    BINDINGS = [
        Binding("ctrl+c", "cancel", "Cancel", show=True),
    ]

    def __init__(self, video_path: str) -> None:
        super().__init__()
        self.video_path = video_path
        self._cancelled = False

    def compose(self) -> ComposeResult:
        """Compose the processing screen."""
        with Container(id="main-container"):
            yield Static("Processing Video...", classes="title")
            yield Static(f"File: {Path(self.video_path).name}", classes="subtitle")
            yield LoadingIndicator()
            yield Static(
                "Extracting frames and analyzing with AI...",
                id="status-text",
                classes="help-text",
            )
            yield Static("[Ctrl+C] Cancel", classes="help-text")

    def on_mount(self) -> None:
        """Start processing when screen mounts."""
        self.run_worker(self._process(), exclusive=True)

    def action_cancel(self) -> None:
        """Cancel processing."""
        self._cancelled = True
        self.app.notify("Cancelled", severity="warning")
        self.app.pop_screen()

    async def _process(self) -> None:
        """Process the video in background."""
        from videotagger.exceptions import LLMError, VideoProcessingError
        from videotagger.pipeline import process_video

        if self._cancelled:
            return

        try:
            tags = process_video(self.video_path)

            if self._cancelled:
                return

            # Show JSON preview screen
            from videotagger.tui.screens.json_preview import JSONPreviewScreen

            self.app.switch_screen(JSONPreviewScreen(self.video_path, tags))

        except VideoProcessingError as e:
            self.app.notify(f"Video error: {e}", severity="error")
            self.app.pop_screen()

        except LLMError as e:
            self.app.notify(f"LLM error: {e}", severity="error")
            self.app.pop_screen()

        except Exception as e:
            self.app.notify(f"Error: {e}", severity="error")
            self.app.pop_screen()
