# Specification: Dynamic Visual Hook Tagging

## Goal

Create a dynamic video tagging system that emphasizes the first 3 seconds of video content (the "Visual Hook"), fetches Airtable ART Grid context to generate customized LLM prompts, and classifies audio transcripts into copywriting framework structures.

## User Stories

- As a content manager, I want the AI to focus analysis on the first 3 seconds of video so that the Visual Hook (action, subject, environment) is accurately captured for searchability.
- As a video team member, I want the tagging prompt to be dynamically populated from Airtable context (Product, Template, etc.) so that tags are relevant to the specific video's category.
- As a content analyst, I want the audio transcript classified into copywriting frameworks (PAS, AIDA, etc.) so that I can analyze Copy Structure patterns across videos.

## Specific Requirements

**First-3-Seconds Weighted Frame Extraction**
- Extract 3 frames at 0.5s intervals (0.0s, 0.5s, 1.0s) from the first 1.5 seconds for dense Visual Hook analysis
- Extract 1 frame every 2 seconds for the remainder of the video
- For videos shorter than 3 seconds, sample all available frames densely
- Add new function `extract_weighted_frames()` in `video.py` that returns both hook frames and context frames
- Hook frames should be clearly labeled/separated from context frames for prompt construction

**Airtable Context Fetching**
- Extend `airtable.py` to fetch full record context, not just find by ID
- New function `get_art_context(art_id)` returns dict with: Product, Testing Concept, Visual Category, Copy Category, Perspective, Angle, Copy Hook, Pitch
- Handle missing fields gracefully (return None for absent columns)
- Testing Concept values include: "Hand medal", "Medal Name Distance", "Earn Medal", "Unveil"
- Cache record context to avoid redundant API calls during batch processing

**Dynamic Prompt Builder**
- Create `prompt_builder.py` module with `build_dynamic_prompt(art_context, transcript)` function
- Inject Airtable context into system/user prompts to guide LLM analysis
- Template should reference Testing Concept to focus model on relevant visual patterns
- Support optional transcript parameter for Copy Structure analysis
- Maintain backward compatibility: if no context provided, fall back to existing static prompt

**Visual Hook Output Schema**
- Extend LLM output to include structured `visual_hook` object with: action, subject, environment
- Action examples: Walk, Run, Medal Handling, Speaking, Talking, Podcast
- Subject examples: Hands + Medal - POV, Neck + Medal - 3rd Person, Person Speaking
- Environment examples: Living Room, Home, Gym, Bed, Bathroom Mirror
- All tags must be in English regardless of video content language
- Add `visual_hook` to required fields validation in `parse_tags_response()`

**Speech-to-Text Integration**
- Add `transcribe.py` module using OpenAI Whisper (via `openai-whisper` package)
- Function `transcribe_audio(audio_path) -> str` returns full transcript
- Use "base" model for balance of speed and accuracy
- Integrate with existing `audio_extract.py` for extracting audio from video
- Handle videos with no speech gracefully (return empty string)

**Copy Structure Classification**
- LLM analyzes transcript and classifies into framework: PAS, BAB, AIDA, PPPP, OCR
- Output includes both framework name and stage breakdown
- PAS: Problem, Agitate, Solution
- BAB: Before, After, Bridge
- AIDA: Attention, Interest, Desire, Action
- PPPP: Picture, Promise, Prove, Push
- OCR: One-time-offer, Call-to-action, Result
- If transcript is empty or no clear structure, return `"framework": "unknown"`

**Updated TagsKG Output Schema**
- Final JSON output combines all analysis into single TagsKG structure
- Includes: existing fields (setting, branded_items, etc.) + visual_hook + copy_structure
- All Airtable context fields are INPUT only (never written back)
- Only TagsKG column is updated with ML-generated tags

## Existing Code to Leverage

**`src/videotagger/video.py` - Frame Extraction**
- Reuse `extract_frames()` logic for frame index calculation
- Extend with weighted sampling strategy (dense first 1.5s, sparse rest)
- Maintain `frame_to_base64()` and `extract_frames_as_base64()` interfaces

**`src/videotagger/llm.py` - Prompt Structure**
- Extend `SYSTEM_PROMPT` and `USER_PROMPT` to support dynamic context injection
- Reuse `build_vision_messages()` pattern for constructing API calls
- Extend `parse_tags_response()` to validate new visual_hook and copy_structure fields

**`src/videotagger/airtable.py` - Record Access**
- Build on `find_by_art_id()` to fetch additional columns
- Reuse `get_airtable_table()` and `get_airtable_client()` patterns
- Follow existing error handling with custom exceptions

**`src/videotagger/audio_extract.py` - Audio Extraction**
- Reuse for extracting audio before transcription
- Leverage existing temp file handling and cleanup patterns

**`src/videotagger/pipeline.py` - Processing Flow**
- Extend `process_video()` to include context fetching and transcript analysis
- Maintain existing interface for backward compatibility

## Out of Scope

- Modifying any Airtable columns other than TagsKG
- Multi-language tag output (English only)
- Training or fine-tuning custom ML models
- Real-time video streaming analysis
- Video editing or frame manipulation
- Batch transcription optimization (process one video at a time)
- Caching transcripts to disk
- TUI changes for new fields (future spec)
- RunPod-specific transcription (local Whisper only for now)
