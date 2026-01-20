"""Main TUI application for VideoTagger."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from videotagger.tui.screens.main_menu import MainMenuScreen


class VideoTaggerApp(App):
    """VideoTagger Terminal User Interface."""

    TITLE = "VideoTagger"
    SUB_TITLE = "Video Content Tagging Pipeline"

    CSS = """
    Screen {
        align: center middle;
    }

    #main-container {
        width: 90%;
        height: auto;
        max-width: 120;
        padding: 1 2;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1 0;
    }

    .subtitle {
        text-align: center;
        color: $text-muted;
        padding: 0 0 1 0;
    }

    .help-text {
        text-align: center;
        color: $text-muted;
        padding: 1 0;
    }

    #menu-list {
        width: 100%;
        height: auto;
        max-height: 20;
        border: solid $primary;
        padding: 0;
    }

    #menu-list > .option-list--option {
        padding: 0 2;
    }

    #json-preview {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }

    #video-info {
        height: 3;
        padding: 1;
        background: $surface;
        border: solid $primary;
    }

    #input-container {
        width: 100%;
        height: auto;
        padding: 1 0;
    }

    #video-path-input {
        width: 100%;
    }

    .keybind {
        color: $accent;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("escape", "back", "Back", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Handle app mount."""
        self.push_screen(MainMenuScreen())

    def action_back(self) -> None:
        """Go back to previous screen."""
        if len(self.screen_stack) > 1:
            self.pop_screen()


def run_tui() -> None:
    """Run the TUI application."""
    app = VideoTaggerApp()
    app.run()
