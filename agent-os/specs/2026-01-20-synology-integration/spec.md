# Specification: Synology NAS Integration

## Goal
Implement SSH/SFTP connection to Synology NAS to list and download videos matching the pattern `V - *a{id}.mp4` for processing.

## User Stories
- As a user, I want to browse videos on my Synology NAS so that I can select which ones to process.
- As a user, I want to download selected videos locally for processing without manually copying files.

## Specific Requirements

**Synology Client Module**
- Create `src/videotagger/synology.py` module
- Use `paramiko` for SSH/SFTP connections
- Connect using credentials from SynologyConfig
- Handle connection errors gracefully with retries

**List Videos**
- Implement `list_videos()` function
- Connect to NAS via SFTP
- List files in configured video path
- Filter by pattern: files starting with "V - " and ending with `a{digits}.mp4`
- Return list of video file info (name, size, modified date)

**Download Video**
- Implement `download_video(filename, local_path)` function
- Download single video file via SFTP
- Show progress during download
- Support resuming interrupted downloads (optional)

**Video Pattern Matching**
- Pattern: `V - *.mp4` where filename contains Art ID like `a1433`
- Extract Art ID from filename for Airtable matching
- Skip files that don't match pattern

**TUI Integration**
- Add "Browse Synology" option to main menu
- Show list of videos with selection (checkboxes)
- Download selected videos to temp directory
- Process downloaded videos through existing pipeline

**Error Handling**
- `SynologyConnectionError` for connection failures
- `SynologyFileError` for file operation failures
- Retry logic for transient network errors
- Clear error messages for auth failures

## Visual Design
No mockups - use existing TUI patterns with OptionList for video selection.

## Existing Code to Leverage

**src/videotagger/config.py**
- `SynologyConfig` with host, user, password, video_path

**src/videotagger/airtable.py**
- `extract_art_id()` function for parsing filenames

**src/videotagger/tui/screens/**
- Existing screen patterns for navigation

## Out of Scope
- Uploading files to Synology
- Modifying files on Synology
- Browsing directories other than configured path
- Video streaming (must download first)
