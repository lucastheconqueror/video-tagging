# Specification: Local Video Processing Mode

## Goal
Build a video processing pipeline that extracts frames from local video files and sends them to a Qwen3-VL model (via vLLM OpenAI-compatible API) to generate structured JSON metadata for tagging.

## User Stories
- As a developer, I want to process a local video file so that I can test the tagging pipeline without needing Synology/S3 infrastructure.
- As a developer, I want the LLM to return structured JSON so that I can store it directly in Airtable.

## Specific Requirements

**Video Frame Extraction**
- Create `src/videotagger/video.py` module
- Use OpenCV (`cv2`) to extract frames from video
- Extract N evenly-spaced frames (default: 8 frames)
- Convert frames to base64 for API transmission
- Support common video formats: mp4, mov, avi

**LLM Client Module**
- Create `src/videotagger/llm.py` module
- Use OpenAI-compatible API for vLLM endpoint
- Support vision model input (images + text)
- Parse JSON response from model output
- Handle connection errors gracefully

**System and User Prompts**
- System prompt: "You are a video content tagger. Your job is to extract metadata from video frames. You must output ONLY valid JSON text. Do not use Markdown code blocks. Do not explain your answer."
- User prompt requests: location, brand_objects, visual_text, mood, excitement
- Output schema: `{"location": str, "brand_objects": [str], "visual_text": [str], "mood": str, "excitement": str}`

**Processing Pipeline**
- Create `process_video(video_path: str)` function
- Extract frames → encode to base64 → send to LLM → parse JSON
- Return validated tag dictionary
- Add CLI command: `python -m videotagger process <video_path>`

**Configuration Extension**
- Add LLM config to settings: endpoint URL, model name, API key (optional)
- Default endpoint for local testing: RunPod vLLM instance
- Support configurable frame count

**Error Handling**
- `VideoProcessingError` for frame extraction failures
- `LLMError` for API/parsing failures
- Validate JSON structure matches expected schema
- Retry logic for transient API failures

## Visual Design
No visual assets provided.

## Existing Code to Leverage

**src/videotagger/config.py**
- Extend Settings with LLM configuration
- Pattern for Pydantic models with env loading

**src/videotagger/exceptions.py**
- Add new exception types following existing pattern

## Out of Scope
- Video preprocessing (resizing, cropping)
- Audio analysis
- Batch video processing (handled in later feature)
- Caching LLM responses
- Alternative LLM providers (only vLLM/OpenAI-compatible)
