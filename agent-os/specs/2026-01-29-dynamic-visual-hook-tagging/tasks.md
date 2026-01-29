# Task Breakdown: Dynamic Visual Hook Tagging

## Overview
Total Tasks: 6 Task Groups, ~24 subtasks

## Task List

### Video Processing Layer

#### Task Group 1: Weighted Frame Extraction
**Dependencies:** None

- [ ] 1.0 Complete weighted frame extraction
  - [ ] 1.1 Write 4 focused tests for weighted frame extraction
    - Test dense extraction for first 1.5 seconds (3 frames at 0.5s intervals)
    - Test sparse extraction for remainder (1 frame per 2 seconds)
    - Test short video handling (<3 seconds)
    - Test frame labeling (hook vs context frames)
  - [ ] 1.2 Create `extract_weighted_frames()` function in `video.py`
    - Parameters: `video_path`, `hook_interval=0.5`, `hook_duration=1.5`, `context_interval=2.0`
    - Returns: `dict` with `hook_frames: list[np.ndarray]` and `context_frames: list[np.ndarray]`
    - Calculate frame indices based on video FPS and duration
  - [ ] 1.3 Create `extract_weighted_frames_as_base64()` wrapper
    - Converts both hook and context frames to base64
    - Returns: `dict` with `hook_frames: list[str]` and `context_frames: list[str]`
  - [ ] 1.4 Ensure frame extraction tests pass
    - Run only the 4 tests from 1.1
    - Verify with sample video files

**Acceptance Criteria:**
- Dense frames extracted at 0.0s, 0.5s, 1.0s for videos >= 1.5s
- Sparse frames extracted every 2s after 1.5s mark
- Short videos handled correctly
- Tests pass

---

### Airtable Integration Layer

#### Task Group 2: Context Fetching
**Dependencies:** None (can run parallel with Task Group 1)

- [ ] 2.0 Complete Airtable context fetching
  - [ ] 2.1 Write 3 focused tests for context fetching
    - Test `get_art_context()` returns expected fields
    - Test missing fields return None gracefully
    - Test caching behavior for repeated calls
  - [ ] 2.2 Create `get_art_context(art_id)` function in `airtable.py`
    - Fetch record and extract: Product, Testing Concept, Visual Category, Copy Category, Perspective, Angle, Copy Hook, Pitch
    - Return `ArtContext` dataclass with optional fields
    - Handle missing columns gracefully (return None)
  - [ ] 2.3 Create `ArtContext` dataclass in `airtable.py`
    - Fields: product, testing_concept, visual_category, copy_category, perspective, angle, copy_hook, pitch
    - All fields Optional[str] except pitch which is Optional[list[str]]
    - Add `to_prompt_context()` method for prompt injection
  - [ ] 2.4 Add simple caching with `@lru_cache` decorator
    - Cache by art_id to avoid redundant API calls
    - Add `clear_context_cache()` function for batch processing resets
  - [ ] 2.5 Ensure context fetching tests pass
    - Run only the 3 tests from 2.1

**Acceptance Criteria:**
- Context fields fetched correctly from Airtable
- Missing fields handled without errors
- Caching reduces API calls
- Tests pass

---

### Speech-to-Text Layer

#### Task Group 3: Audio Transcription
**Dependencies:** None (can run parallel with Task Groups 1-2)

- [ ] 3.0 Complete audio transcription
  - [ ] 3.1 Write 3 focused tests for transcription
    - Test `transcribe_audio()` returns string transcript
    - Test empty/silent audio returns empty string
    - Test integration with `extract_audio()` from audio_extract.py
  - [ ] 3.2 Add `openai-whisper` to requirements.txt
    - Pin version for reproducibility
    - Note: requires ffmpeg system dependency
  - [ ] 3.3 Create `transcribe.py` module
    - Function: `transcribe_audio(audio_path: Path) -> str`
    - Use Whisper "base" model for speed/accuracy balance
    - Lazy-load model to avoid startup cost
    - Handle missing audio gracefully (return empty string)
  - [ ] 3.4 Create `transcribe_video(video_path: Path) -> str` convenience function
    - Extract audio using existing `extract_audio()`
    - Transcribe and return transcript
    - Clean up temp audio file after transcription
  - [ ] 3.5 Ensure transcription tests pass
    - Run only the 3 tests from 3.1
    - May need to mock Whisper model for fast tests

**Acceptance Criteria:**
- Whisper model loads and transcribes audio
- Empty audio handled gracefully
- Temp files cleaned up
- Tests pass

---

### LLM Integration Layer

#### Task Group 4: Dynamic Prompt Builder
**Dependencies:** Task Groups 1, 2, 3

- [ ] 4.0 Complete dynamic prompt builder
  - [ ] 4.1 Write 4 focused tests for prompt builder
    - Test prompt includes Airtable context when provided
    - Test prompt works without context (backward compatible)
    - Test visual_hook fields in output schema
    - Test copy_structure fields in output schema
  - [ ] 4.2 Create `prompt_builder.py` module
    - Function: `build_dynamic_prompt(art_context: ArtContext | None, transcript: str | None) -> tuple[str, str]`
    - Returns: `(system_prompt, user_prompt)`
    - Inject Testing Concept, Product, etc. into prompt text
  - [ ] 4.3 Update prompt to request Visual Hook structure
    - Add to USER_PROMPT: visual_hook with action, subject, environment
    - Provide examples: "Medal Handling", "Hands + Medal - POV", "Living Room"
    - Emphasize first 3 seconds analysis
  - [ ] 4.4 Update prompt to request Copy Structure analysis
    - Add framework classification: PAS, BAB, AIDA, PPPP, OCR
    - Request stage breakdown in output
    - Include transcript in prompt when available
  - [ ] 4.5 Update `build_vision_messages()` in `llm.py`
    - Accept optional `system_prompt` and `user_prompt` overrides
    - Default to existing static prompts for backward compatibility
  - [ ] 4.6 Ensure prompt builder tests pass
    - Run only the 4 tests from 4.1

**Acceptance Criteria:**
- Dynamic prompts include Airtable context
- Backward compatible with no context
- New output schema includes visual_hook and copy_structure
- Tests pass

---

### Response Parsing Layer

#### Task Group 5: Extended Response Parsing
**Dependencies:** Task Group 4

- [ ] 5.0 Complete extended response parsing
  - [ ] 5.1 Write 4 focused tests for parsing
    - Test parsing visual_hook structure
    - Test parsing copy_structure with breakdown
    - Test handling missing visual_hook (graceful default)
    - Test handling unknown copy_structure framework
  - [ ] 5.2 Update `parse_tags_response()` in `llm.py`
    - Add visual_hook to expected fields (optional for backward compat)
    - Add copy_structure to expected fields (optional)
    - Validate nested structure when present
  - [ ] 5.3 Create default schemas for new fields
    - Default visual_hook: `{"action": "unknown", "subject": "unknown", "environment": "unknown"}`
    - Default copy_structure: `{"framework": "unknown", "breakdown": {}}`
  - [ ] 5.4 Ensure parsing tests pass
    - Run only the 4 tests from 5.1

**Acceptance Criteria:**
- New fields parsed correctly when present
- Missing fields get sensible defaults
- Backward compatible with old responses
- Tests pass

---

### Pipeline Integration Layer

#### Task Group 6: End-to-End Pipeline
**Dependencies:** Task Groups 1-5

- [ ] 6.0 Complete pipeline integration
  - [ ] 6.1 Write 3 focused tests for pipeline
    - Test `process_video_with_context()` integrates all components
    - Test pipeline works without Airtable context (local mode)
    - Test final TagsKG output contains all expected fields
  - [ ] 6.2 Create `process_video_with_context()` in `pipeline.py`
    - Parameters: `video_path`, `art_id: str | None`, `include_transcript: bool`
    - Fetch Airtable context if art_id provided
    - Extract weighted frames
    - Transcribe audio if include_transcript=True
    - Build dynamic prompt
    - Call LLM and parse response
    - Return combined tags dict
  - [ ] 6.3 Update existing `process_video()` for backward compatibility
    - Keep existing signature and behavior
    - Optionally call new function internally
  - [ ] 6.4 Ensure pipeline tests pass
    - Run only the 3 tests from 6.1

**Acceptance Criteria:**
- Full pipeline processes video with context
- Works in local mode without Airtable
- Output includes visual_hook and copy_structure
- Backward compatible
- Tests pass

---

## Execution Order

Recommended implementation sequence:

1. **Task Groups 1, 2, 3 (Parallel)** - Frame extraction, Airtable context, Transcription
   - These have no dependencies and can be developed simultaneously
2. **Task Group 4** - Dynamic Prompt Builder (depends on 1, 2, 3)
3. **Task Group 5** - Response Parsing (depends on 4)
4. **Task Group 6** - Pipeline Integration (depends on all above)

## Files to Create/Modify

**New Files:**
- `src/videotagger/transcribe.py` - Whisper speech-to-text
- `src/videotagger/prompt_builder.py` - Dynamic prompt construction

**Modified Files:**
- `src/videotagger/video.py` - Add weighted frame extraction
- `src/videotagger/airtable.py` - Add context fetching and ArtContext dataclass
- `src/videotagger/llm.py` - Update build_vision_messages and parse_tags_response
- `src/videotagger/pipeline.py` - Add process_video_with_context
- `requirements.txt` - Add openai-whisper

**New Test Files:**
- `tests/test_transcribe.py`
- `tests/test_prompt_builder.py`
