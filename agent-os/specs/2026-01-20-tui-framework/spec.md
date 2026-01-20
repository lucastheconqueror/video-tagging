# Specification: TUI Framework Setup

## Goal
Create a Textual-based TUI application with main menu, video list selection, JSON preview panel, and confirmation dialogs to provide an interactive workflow for video tagging.

## User Stories
- As a user, I want to see a menu of actions so that I can choose what to do next.
- As a user, I want to select videos from a list so that I can process specific files.
- As a user, I want to preview extracted JSON before updating Airtable so that I can verify the results.

## Specific Requirements

**TUI Application Structure**
- Create `src/videotagger/tui/` package
- Main app class extending `textual.app.App`
- Multiple screens: MainMenu, VideoList, ProcessingView, JSONPreview
- Consistent styling and keybindings

**Main Menu Screen**
- Display application title and version
- Menu options:
  - Process local video (for testing)
  - Connect to Synology (future)
  - Validate configuration
  - Exit
- Keyboard navigation with arrow keys and Enter

**Video Selection Screen**
- Display list of videos (from local path or Synology)
- Checkbox selection for multiple videos
- Select all / Deselect all buttons
- Continue button to process selected videos
- Back button to return to menu

**JSON Preview Screen**
- Display extracted tags in formatted JSON
- Side-by-side: video filename and JSON result
- Confirm button to update Airtable
- Skip button to move to next video
- Edit button (stretch goal - manual JSON editing)

**Confirmation Dialogs**
- Modal dialogs for destructive actions
- "Are you sure?" before Airtable updates
- Success/error notifications after operations

**Progress Indicators**
- Loading spinner during video processing
- Progress bar for batch operations
- Status messages in footer

**CLI Integration**
- New command: `python -m videotagger tui`
- Launch TUI as default when no command specified

## Visual Design
No mockups provided - use Textual's default styling with sensible layouts.

## Existing Code to Leverage

**src/videotagger/pipeline.py**
- `process_video()` function for video analysis

**src/videotagger/airtable.py**
- `update_tags()` function for Airtable updates
- `extract_art_id()` for filename parsing

**src/videotagger/config.py**
- Settings loading for configuration validation

## Out of Scope
- Custom color themes
- Mouse-only interactions (keyboard must work)
- Video preview/playback
- Drag and drop
