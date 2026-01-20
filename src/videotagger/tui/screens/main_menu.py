"""Main menu screen for VideoTagger TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option


class MainMenuScreen(Screen):
    """Main menu screen with vim-style navigation."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("enter", "select", "Select", show=False),
        Binding("l", "select", "Select", show=False),
        Binding("p", "process_local", "Local", show=False),
        Binding("s", "browse_synology", "Synology", show=False),
        Binding("r", "runpod_process", "RunPod", show=False),
        Binding("v", "validate_config", "Config", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose the main menu layout."""
        with Container(id="main-container"):
            yield Static("VideoTagger", classes="title")
            yield Static("Video Content Tagging Pipeline", classes="subtitle")

            yield OptionList(
                Option("(p) Process Local Video", id="local-video"),
                Option("(s) Browse Synology NAS", id="synology"),
                Option("(r) Process on RunPod S3", id="runpod"),
                Option("(v) Validate Configuration", id="validate-config"),
                Option("(q) Quit", id="quit"),
                id="menu-list",
            )

            yield Static(
                "j/k Navigate | p Local | s Synology | r RunPod | v Config | q Quit",
                classes="help-text",
            )

    def on_mount(self) -> None:
        """Focus the menu on mount."""
        self.query_one(OptionList).focus()

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        option_list = self.query_one(OptionList)
        option_list.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        option_list = self.query_one(OptionList)
        option_list.action_cursor_up()

    def action_select(self) -> None:
        """Select current option."""
        option_list = self.query_one(OptionList)
        if option_list.highlighted is not None:
            self._handle_selection(option_list.get_option_at_index(option_list.highlighted).id)

    def action_process_local(self) -> None:
        """Direct shortcut to process local video."""
        self._handle_selection("local-video")

    def action_validate_config(self) -> None:
        """Direct shortcut to validate config."""
        self._handle_selection("validate-config")

    def action_browse_synology(self) -> None:
        """Direct shortcut to browse Synology."""
        self._handle_selection("synology")

    def action_runpod_process(self) -> None:
        """Direct shortcut to RunPod processing."""
        self._handle_selection("runpod")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection."""
        self._handle_selection(event.option.id)

    def _handle_selection(self, option_id: str | None) -> None:
        """Handle menu selection."""
        if option_id == "local-video":
            from videotagger.tui.screens.local_video import LocalVideoScreen

            self.app.push_screen(LocalVideoScreen())

        elif option_id == "synology":
            from videotagger.tui.screens.synology_browser import SynologyBrowserScreen

            self.app.push_screen(SynologyBrowserScreen())

        elif option_id == "runpod":
            from videotagger.tui.screens.runpod_process import RunPodProcessScreen

            self.app.push_screen(RunPodProcessScreen())

        elif option_id == "validate-config":
            self._validate_config()

        elif option_id == "quit":
            self.app.exit()

    def _validate_config(self) -> None:
        """Validate configuration and show result."""
        from pydantic import ValidationError

        from videotagger.config import Settings

        try:
            Settings()
            self.app.notify("Configuration is valid!", severity="information")
        except ValidationError as e:
            error_msgs = []
            for err in e.errors():
                field = ".".join(str(loc) for loc in err["loc"])
                error_msgs.append(f"{field}: {err['msg']}")
            self.app.notify(f"Config errors: {', '.join(error_msgs[:3])}", severity="error")
