"""Batch review screen for reviewing processed videos before Airtable update."""

import json
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option


class BatchReviewScreen(Screen):
    """Screen for reviewing batch processing results before updating Airtable."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("enter", "view_detail", "View", show=False),
        Binding("space", "toggle", "Toggle", show=False),
        Binding("a", "select_all", "All", show=False),
        Binding("u", "update_airtable", "Update Airtable", show=False),
        Binding("s", "save_sidecars", "Save Sidecars", show=False),
        Binding("escape", "back", "Back", show=False),
    ]

    def __init__(self, results: list[tuple[Any, dict | None, str | None]]) -> None:
        """Initialize with processing results.

        Args:
            results: List of (video, tags, error) tuples.
        """
        super().__init__()
        self.results = results
        self.selected: set[int] = set()

        # Pre-select successful results
        for i, (video, tags, error) in enumerate(results):
            if tags is not None:
                self.selected.add(i)

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        success = sum(1 for _, tags, _ in self.results if tags is not None)
        failed = len(self.results) - success

        with Container(id="main-container"):
            yield Static("Batch Processing Complete", classes="title")
            yield Static(
                f"{success} succeeded, {failed} failed",
                id="status",
                classes="subtitle",
            )
            yield OptionList(id="result-list")
            yield Static(
                "Space Toggle | a All | Enter View | u Airtable | s Sidecars | Esc Back",
                classes="help-text",
            )

    def on_mount(self) -> None:
        """Populate results list."""
        result_list = self.query_one("#result-list", OptionList)

        for i, (video, tags, error) in enumerate(self.results):
            if tags is not None:
                mark = "(x)" if i in self.selected else "( )"
                label = f"{mark} {video.filename} - OK"
            else:
                label = f"[!] {video.filename} - {error[:30]}..."

            result_list.add_option(Option(label, id=str(i)))

        result_list.focus()

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        self.query_one("#result-list", OptionList).action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        self.query_one("#result-list", OptionList).action_cursor_up()

    def action_toggle(self) -> None:
        """Toggle selection."""
        result_list = self.query_one("#result-list", OptionList)
        if result_list.highlighted is None:
            return

        idx = result_list.highlighted
        video, tags, error = self.results[idx]

        # Can only select successful results
        if tags is None:
            self.app.notify("Cannot select failed items", severity="warning")
            return

        if idx in self.selected:
            self.selected.discard(idx)
        else:
            self.selected.add(idx)

        self._update_label(idx)
        result_list.action_cursor_down()

    def action_select_all(self) -> None:
        """Toggle select all successful."""
        successful = {i for i, (_, tags, _) in enumerate(self.results) if tags is not None}

        if self.selected == successful:
            self.selected.clear()
        else:
            self.selected = successful

        for i in range(len(self.results)):
            self._update_label(i)

    def _update_label(self, idx: int) -> None:
        """Update option label."""
        result_list = self.query_one("#result-list", OptionList)
        video, tags, error = self.results[idx]

        if tags is not None:
            mark = "(x)" if idx in self.selected else "( )"
            label = f"{mark} {video.filename} - OK"
        else:
            label = f"[!] {video.filename} - {error[:30]}..."

        result_list.replace_option_prompt_at_index(idx, label)

    def action_view_detail(self) -> None:
        """View detail of selected item."""
        result_list = self.query_one("#result-list", OptionList)
        if result_list.highlighted is None:
            return

        idx = result_list.highlighted
        video, tags, error = self.results[idx]

        if tags is not None:
            self.app.push_screen(BatchItemDetailScreen(video, tags))
        else:
            self.app.notify(f"Error: {error}", severity="error")

    def action_update_airtable(self) -> None:
        """Update Airtable for selected items."""
        if not self.selected:
            self.app.notify("No items selected", severity="warning")
            return

        selected_results = [(self.results[i][0], self.results[i][1]) for i in self.selected]
        self.app.push_screen(BatchUpdateScreen(selected_results))

    def action_save_sidecars(self) -> None:
        """Save sidecar files for selected items."""
        if not self.selected:
            self.app.notify("No items selected", severity="warning")
            return


        saved = 0
        for idx in self.selected:
            video, tags, _ = self.results[idx]
            if tags:
                try:
                    # For remote videos, we'd need to determine local path
                    # For now, just notify
                    saved += 1
                except Exception:
                    pass

        self.app.notify("Sidecar saving not available for remote videos", severity="warning")

    def action_back(self) -> None:
        """Go back to main menu."""
        from videotagger.tui.screens.main_menu import MainMenuScreen

        # Clear screen stack and go to menu
        while len(self.app.screen_stack) > 1:
            self.app.pop_screen()

        if not isinstance(self.app.screen, MainMenuScreen):
            self.app.push_screen(MainMenuScreen())


class BatchItemDetailScreen(Screen):
    """Screen showing detail of a single processed item."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=False),
        Binding("q", "back", "Back", show=False),
    ]

    def __init__(self, video: Any, tags: dict) -> None:
        super().__init__()
        self.video = video
        self.tags = tags

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        tags_json = json.dumps(self.tags, indent=2, ensure_ascii=False)

        with Container(id="main-container"):
            yield Static("Processing Result", classes="title")
            yield Static(f"File: {self.video.filename}", classes="subtitle")
            yield Static(tags_json, id="json-preview")
            yield Static("Esc/q Back", classes="help-text")

    def action_back(self) -> None:
        """Go back."""
        self.app.pop_screen()


class BatchUpdateScreen(Screen):
    """Screen for updating Airtable in batch."""

    BINDINGS = [
        Binding("ctrl+c", "cancel", "Cancel", show=False),
    ]

    def __init__(self, items: list[tuple[Any, dict]]) -> None:
        """Initialize with items to update.

        Args:
            items: List of (video, tags) tuples.
        """
        super().__init__()
        self.items = items
        self._cancelled = False

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        with Container(id="main-container"):
            yield Static("Updating Airtable", classes="title")
            yield Static(f"0/{len(self.items)}", id="progress-text", classes="subtitle")
            yield Static("", id="current-file", classes="help-text")
            yield Static("Ctrl+C Cancel", classes="help-text")

    def on_mount(self) -> None:
        """Start updating."""
        self.run_worker(self._update_all, thread=True, exclusive=True)

    def action_cancel(self) -> None:
        """Cancel."""
        self._cancelled = True
        self.app.notify("Cancelled", severity="warning")
        self.app.pop_screen()

    def _update_all(self) -> tuple[int, int]:
        """Update all items (runs in thread)."""
        from videotagger.airtable import extract_art_id, update_tags
        from videotagger.exceptions import ArtIdExtractionError, RecordNotFoundError

        success = 0
        failed = 0

        for i, (video, tags) in enumerate(self.items):
            if self._cancelled:
                break

            self.app.call_from_thread(
                self._update_progress,
                i,
                video.filename,
            )

            try:
                art_id = extract_art_id(video.filename)
                update_tags(art_id, tags)
                success += 1
            except ArtIdExtractionError:
                self.app.call_from_thread(
                    self.app.notify,
                    f"No Art ID: {video.filename}",
                    severity="warning",
                )
                failed += 1
            except RecordNotFoundError as e:
                self.app.call_from_thread(
                    self.app.notify,
                    str(e),
                    severity="warning",
                )
                failed += 1
            except Exception as e:
                self.app.call_from_thread(
                    self.app.notify,
                    f"Error: {e}",
                    severity="error",
                )
                failed += 1

        # Done
        self.app.call_from_thread(self._finish, success, failed)
        return success, failed

    def _update_progress(self, index: int, filename: str) -> None:
        """Update progress display."""
        self.query_one("#progress-text", Static).update(f"{index + 1}/{len(self.items)}")
        self.query_one("#current-file", Static).update(f"Updating: {filename}")

    def _finish(self, success: int, failed: int) -> None:
        """Finish and go back."""
        if failed == 0:
            self.app.notify(f"Updated {success} records", severity="information")
        else:
            self.app.notify(f"Updated {success}, failed {failed}", severity="warning")

        # Go back to review screen
        self.app.pop_screen()
