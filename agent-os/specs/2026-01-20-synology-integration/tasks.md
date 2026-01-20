# Task Breakdown: Synology NAS Integration

## Overview
Total Tasks: 10

## Task List

### Setup

#### Task Group 1: Dependencies & Exceptions
**Dependencies:** None

- [ ] 1.0 Complete setup
  - [ ] 1.1 Add paramiko to requirements.txt
  - [ ] 1.2 Add Synology exceptions to exceptions.py

**Acceptance Criteria:**
- paramiko is installable
- Custom exceptions defined

### Synology Client

#### Task Group 2: Core Synology Functions
**Dependencies:** Task Group 1

- [ ] 2.0 Complete Synology client
  - [ ] 2.1 Write 4-5 tests for Synology functions (mocked)
  - [ ] 2.2 Create `src/videotagger/synology.py` module
  - [ ] 2.3 Implement `connect()` function with SFTP
  - [ ] 2.4 Implement `list_videos()` function with pattern filtering
  - [ ] 2.5 Implement `download_video()` function
  - [ ] 2.6 Ensure tests pass

**Acceptance Criteria:**
- Can connect to Synology via SFTP
- Lists only matching video files
- Downloads files correctly

### TUI Integration

#### Task Group 3: Synology Browser Screen
**Dependencies:** Task Group 2

- [ ] 3.0 Complete TUI integration
  - [ ] 3.1 Add "Browse Synology" to main menu
  - [ ] 3.2 Create SynologyBrowserScreen with video list
  - [ ] 3.3 Implement video selection and download
  - [ ] 3.4 Connect to existing processing pipeline

**Acceptance Criteria:**
- Can browse Synology from TUI
- Can select and download videos
- Downloads process through existing pipeline

## Execution Order

1. Setup (Task Group 1)
2. Synology Client (Task Group 2)
3. TUI Integration (Task Group 3)
