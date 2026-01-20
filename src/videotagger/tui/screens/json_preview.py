"""JSON preview screen for reviewing extracted tags."""

import json
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Static

from videotagger.airtable import extract_art_id, update_tags
from videotagger.exceptions import ArtIdExtractionError, RecordNotFoundError


class JSONPreviewScreen(Screen):
    """Screen for previewing and confirming extracted tags."""

    BINDINGS = [
        Binding("y", "confirm", "Confirm Update", show=True),
        Binding("n", "skip", "Skip", show=True),
        Binding("s", "skip", "Skip", show=False),
        Binding("escape", "menu", "Back to Menu", show=True),
        Binding("q", "menu", "Back to Menu", show=False),
        Binding("e", "edit", "Edit (TODO)", show=False),
    ]

    def __init__(self, video_path: str, tags: dict[str, Any]) -> None:
        super().__init__()
        self.video_path = video_path
        self.tags = tags

    def compose(self) -> ComposeResult:
        """Compose the JSON preview screen."""
        filename = Path(self.video_path).name
        tags_json = json.dumps(self.tags, indent=2, ensure_ascii=False)

        # Try to extract Art ID
        try:
            art_id = extract_art_id(filename)
            art_id_display = f"Art ID: {art_id}"
        except ArtIdExtractionError:
            art_id_display = "Art ID: Not found in filename"

        with Container(id="main-container"):
            yield Static("Review Extracted Tags", classes="title")

            with Vertical(id="video-info"):
                yield Static(f"File: {filename}")
                yield Static(art_id_display)

            yield Static(tags_json, id="json-preview")

            yield Static(
                "[y] Update Airtable | [n/s] Skip | [Escape/q] Back to Menu",
                classes="help-text",
            )

    def action_confirm(self) -> None:
        """Confirm and update Airtable."""
        self._update_airtable()

    def action_skip(self) -> None:
        """Skip without updating."""
        self.app.notify("Skipped - no changes made", severity="information")
        self._go_to_menu()

    def action_menu(self) -> None:
        """Return to main menu."""
        self._go_to_menu()

    def action_edit(self) -> None:
        """Edit JSON (placeholder for future)."""
        self.app.notify("Edit mode not yet implemented", severity="warning")

    def _update_airtable(self) -> None:
        """Update Airtable with the tags."""
        filename = Path(self.video_path).name

        try:
            art_id = extract_art_id(filename)
        except ArtIdExtractionError:
            self.app.notify("Cannot update: No Art ID in filename", severity="error")
            return

        try:
            update_tags(art_id, self.tags)
            self.app.notify(f"Updated Airtable for {art_id}", severity="information")
            self._go_to_menu()

        except RecordNotFoundError:
            self.app.notify(f"Record not found: {art_id}", severity="error")

        except Exception as e:
            self.app.notify(f"Airtable error: {e}", severity="error")

    def _go_to_menu(self) -> None:
        """Return to main menu."""
        from videotagger.tui.screens.main_menu import MainMenuScreen

        # Clear screen stack and go to menu
        while len(self.app.screen_stack) > 1:
            self.app.pop_screen()

        if not isinstance(self.app.screen, MainMenuScreen):
            self.app.push_screen(MainMenuScreen())
