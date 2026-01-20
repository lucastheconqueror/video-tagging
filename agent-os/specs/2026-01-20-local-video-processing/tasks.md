# Task Breakdown: Local Video Processing Mode

## Overview
Total Tasks: 14

## Task List

### Setup

#### Task Group 1: Dependencies & Config
**Dependencies:** None

- [ ] 1.0 Complete setup
  - [ ] 1.1 Add opencv-python and openai to requirements.txt
  - [ ] 1.2 Add LLM config to Settings (endpoint, model, api_key, frame_count)
  - [ ] 1.3 Add new exceptions: VideoProcessingError, LLMError
  - [ ] 1.4 Update .env.example with LLM settings

**Acceptance Criteria:**
- Dependencies installable
- LLM config loads from environment

### Video Processing

#### Task Group 2: Frame Extraction
**Dependencies:** Task Group 1

- [ ] 2.0 Complete frame extraction
  - [ ] 2.1 Write 3-4 tests for frame extraction
    - Test extracts correct number of frames
    - Test returns base64 encoded strings
    - Test raises error for invalid video path
  - [ ] 2.2 Create `src/videotagger/video.py` module
  - [ ] 2.3 Implement `extract_frames(video_path, num_frames)` function
  - [ ] 2.4 Implement `frame_to_base64(frame)` helper
  - [ ] 2.5 Ensure tests pass

**Acceptance Criteria:**
- Frames extracted evenly across video duration
- Base64 encoding works correctly

### LLM Integration

#### Task Group 3: LLM Client
**Dependencies:** Task Group 1

- [ ] 3.0 Complete LLM client
  - [ ] 3.1 Write 3-4 tests for LLM client (mocked)
    - Test sends correct prompt structure
    - Test parses valid JSON response
    - Test handles invalid JSON gracefully
  - [ ] 3.2 Create `src/videotagger/llm.py` module
  - [ ] 3.3 Implement `analyze_frames(frames: list[str])` function
  - [ ] 3.4 Implement JSON parsing and validation
  - [ ] 3.5 Ensure tests pass

**Acceptance Criteria:**
- LLM client sends vision request correctly
- JSON response parsed and validated

### Pipeline & CLI

#### Task Group 4: Processing Pipeline
**Dependencies:** Task Groups 2, 3

- [ ] 4.0 Complete processing pipeline
  - [ ] 4.1 Implement `process_video(video_path)` function
  - [ ] 4.2 Add CLI command `process <video_path>`
  - [ ] 4.3 Run all tests and verify

**Acceptance Criteria:**
- Full pipeline works end-to-end
- CLI command processes video and outputs JSON

## Execution Order

1. Setup (Task Group 1)
2. Frame Extraction (Task Group 2) 
3. LLM Client (Task Group 3) - can run in parallel with 2
4. Processing Pipeline (Task Group 4)
