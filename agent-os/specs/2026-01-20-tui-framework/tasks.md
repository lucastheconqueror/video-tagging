# Task Breakdown: TUI Framework Setup

## Overview
Total Tasks: 12

## Task List

### Setup

#### Task Group 1: Dependencies & Structure
**Dependencies:** None

- [ ] 1.0 Complete setup
  - [ ] 1.1 Add textual to requirements.txt
  - [ ] 1.2 Create `src/videotagger/tui/` package structure
  - [ ] 1.3 Create base TUI app class

**Acceptance Criteria:**
- Textual is installable
- TUI package structure exists

### Core Screens

#### Task Group 2: Main Menu & Navigation
**Dependencies:** Task Group 1

- [ ] 2.0 Complete main menu
  - [ ] 2.1 Create MainMenu screen with options
  - [ ] 2.2 Implement keyboard navigation
  - [ ] 2.3 Add screen transitions

**Acceptance Criteria:**
- Menu displays with options
- Arrow keys and Enter work
- Can navigate between screens

#### Task Group 3: Local Video Processing Screen
**Dependencies:** Task Group 2

- [ ] 3.0 Complete local processing flow
  - [ ] 3.1 Create file input dialog for video path
  - [ ] 3.2 Create ProcessingView with spinner
  - [ ] 3.3 Create JSONPreview screen
  - [ ] 3.4 Implement confirm/skip actions

**Acceptance Criteria:**
- Can enter video path
- Processing shows loading state
- JSON result displayed for review
- Can confirm or skip

### Integration

#### Task Group 4: CLI & Polish
**Dependencies:** Task Groups 2, 3

- [ ] 4.0 Complete integration
  - [ ] 4.1 Add `tui` command to CLI
  - [ ] 4.2 Make TUI default when no command given
  - [ ] 4.3 Add error handling and notifications
  - [ ] 4.4 Test full workflow

**Acceptance Criteria:**
- `python -m videotagger tui` launches TUI
- `python -m videotagger` (no args) launches TUI
- Errors display as notifications

## Execution Order

1. Setup (Task Group 1)
2. Main Menu (Task Group 2)
3. Processing Screens (Task Group 3)
4. CLI Integration (Task Group 4)
