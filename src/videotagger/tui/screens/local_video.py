"""Local video processing screen."""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Input, LoadingIndicator, Static

from videotagger.sidecar import get_sidecar_info, has_sidecar


class LocalVideoScreen(Screen):
    """Screen for processing a local video file."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=False),
        Binding("enter", "submit", "Process", show=False),
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

        # Check for existing sidecar
        if has_sidecar(path):
            self.app.push_screen(SidecarWarningScreen(str(path)))
        else:
            self.app.push_screen(ProcessingScreen(str(path)))


class SidecarWarningScreen(Screen):
    """Warning screen when video has already been processed."""

    BINDINGS = [
        Binding("y", "proceed", "Proceed & Overwrite", show=False),
        Binding("n", "cancel", "Cancel", show=False),
        Binding("v", "view", "View Existing", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, video_path: str) -> None:
        super().__init__()
        self.video_path = video_path

    def compose(self) -> ComposeResult:
        """Compose the warning screen."""
        info = get_sidecar_info(self.video_path) or "Unknown"

        with Container(id="main-container"):
            yield Static("Video Already Processed", classes="title")
            yield Static(f"File: {Path(self.video_path).name}", classes="subtitle")
            yield Static(f"\n{info}\n", classes="help-text")
            yield Static(
                "A sidecar JSON file exists for this video.\n"
                "Processing again will overwrite the existing results.",
                classes="help-text",
            )
            yield Static(
                "\n[y] Proceed & Overwrite | [n] Cancel | [v] View Existing JSON",
                classes="help-text",
            )

    def action_proceed(self) -> None:
        """Proceed with processing."""
        self.app.switch_screen(ProcessingScreen(self.video_path))

    def action_cancel(self) -> None:
        """Cancel and go back."""
        self.app.pop_screen()

    def action_view(self) -> None:
        """View existing sidecar data."""
        from videotagger.sidecar import read_sidecar

        data = read_sidecar(self.video_path)
        if data and "tags" in data:
            from videotagger.tui.screens.json_preview import JSONPreviewScreen

            self.app.push_screen(
                JSONPreviewScreen(self.video_path, data["tags"], from_sidecar=True)
            )
        else:
            self.app.notify("Could not read existing sidecar", severity="error")


class ProcessingScreen(Screen):
    """Screen shown while processing video."""

    BINDINGS = [
        Binding("ctrl+c", "cancel", "Cancel", show=False),
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
