# Spec Requirements: Dynamic Visual Hook Tagging

## Initial Description

In our ART Grid we have the following art columns: Product, Testing Concept (Template), Visual Hook, Visual Category, Copy Category, Perspective, Angle, Copy Hook, Pitch (that has multiple select). But for us to create a proper tagging system, we need to put emphasis on the first 3 seconds of the video, those are most important.

Example video tags:
- Visual hook: Medalie intra in cadru, rotate. (primele 3 sec)
- Tags: Indoor, Table, Arms holding medal, POV shot.

Visual hook breakdown:
- Action: Walk, Run, Medal Handling, Speaking, Talking, Podcast (face to face)
- Subject: Hands + Medal - POV / Neck + Medal - 3rd Person, Person Speaking
- Environment: Living Room, Home, Gym, Bed, Bathroom Mirror

Template from Airtable: ex: Podcast -> passed to ML for tagging

Copy Structure: PAS, BAB, AIDA, PPPP, OCR

Audio: Copy Storyline. We need to take the basic concepts from the airtable and create dynamic tags. Copy Structure detection: will need speech-to-text model that takes the audio and converts it into a Copy Structure classification.

Key insight: First step is to create a dynamic Prompt - when we fetch video from NAS, we find its art ID and search for it in the Airtable and populate the prompt.

Frame sampling strategy: Send most information in first three seconds, then maybe 1 frame every 2 seconds. Really need to dive into the visual hook.

## Requirements Discussion

### First Round Questions

**Q1:** I assume we should extract dense frames in the first 3 seconds (e.g., 6-8 frames at 0.5s intervals) and then sparse frames for the rest (1 frame every 2 seconds). Is that correct, or would you prefer a different ratio?
**Answer:** 3 frames at 0.5 intervals for the first 3 seconds.

**Q2:** For videos shorter than 3 seconds, I'm thinking we treat the entire video as the "hook" and sample all available frames densely. Does that sound right?
**Answer:** Yes.

**Q3:** For the Visual Hook breakdown (Action, Subject, Environment), should these be free-text descriptions, pre-defined tag lists, or a hybrid?
**Answer:** We have the Testing Concept that has tag lists.

**Q4:** I notice the examples use Romanian. Should the tags be generated in Romanian, English, or both?
**Answer:** All tags should be in English.

**Q5:** For the dynamic prompt, I assume we fetch Airtable columns (Product, Testing Concept, Visual Category, etc.) to contextualize the LLM prompt. Is that the intent?
**Answer:** Yes.

**Q6:** Which columns from Airtable should influence the prompt vs. which should be filled in by the ML model?
**Answer:** All tags should only be exported to TagsKG. Rest are input fields.

**Q7:** For Copy Structure classification (PAS, BAB, AIDA, PPPP, OCR), should we extract audio → speech-to-text → LLM classification?
**Answer:** Yes.

**Q8:** Is OCR in Copy Structure referring to "One-time-offer, Call-to-action, Result" or actual Optical Character Recognition?
**Answer:** One time offer (OCR = One-time-offer, Call-to-action, Result framework).

### Follow-up Questions

**Follow-up 1:** Could you share an example of the Testing Concept values/options in your Airtable?
**Answer:** Hand medal, Medal Name Distance, Earn Medal, Unveil.

**Follow-up 2:** For the Visual Hook output structure, should it follow the breakdown (action, subject, environment)?
**Answer:** All good (confirmed the structure).

**Follow-up 3:** For copywriting frameworks, should the model output just the framework name or also a breakdown of stages?
**Answer:** Do a breakdown and also provide the copy structure name.

### Existing Code to Reference

**Similar Features Identified:**
- Feature: LLM Prompt Builder - Path: `src/videotagger/llm.py`
  - Extend the existing `USER_PROMPT` and `build_vision_messages` functions
  - Add dynamic prompt construction based on Airtable context
- Feature: Airtable Integration - Path: `src/videotagger/airtable.py`
  - Use `find_by_art_id()` to fetch record context before processing
  - Extend to fetch additional columns (Product, Testing Concept, etc.)
- Feature: Video Frame Extraction - Path: `src/videotagger/video.py`
  - Modify `extract_frames()` to support weighted sampling (dense first 3s, sparse rest)
- Feature: Audio Pipeline - Path: `src/videotagger/audio_analysis.py`
  - Integrate speech-to-text for Copy Structure detection

## Visual Assets

### Files Provided:
No visual assets provided.

## Requirements Summary

### Functional Requirements

**1. First-3-Seconds Focused Frame Extraction**
- Extract 3 frames at 0.5s intervals (0s, 0.5s, 1.0s, 1.5s) from the first 3 seconds
- Extract 1 frame every 2 seconds for the remainder of the video
- For videos < 3 seconds, sample all available frames densely

**2. Dynamic Prompt Generation from Airtable Context**
- When processing a video, extract Art ID from filename
- Fetch Airtable record and retrieve context fields:
  - Product
  - Testing Concept (Template) - e.g., "Hand medal", "Medal Name Distance", "Earn Medal", "Unveil"
  - Visual Category
  - Copy Category
  - Perspective
  - Angle
  - Copy Hook
  - Pitch (multiple select)
- Inject these values into the LLM prompt to contextualize the analysis

**3. Visual Hook Analysis Output**
- Structured output format:
  ```json
  {
    "visual_hook": {
      "action": "Medal Handling",
      "subject": "Hands + Medal - POV",
      "environment": "Living Room"
    }
  }
  ```
- All tags in English
- Focus analysis on first 3 seconds of video

**4. Copy Structure Detection via Speech-to-Text**
- Extract audio from video
- Convert speech to text (transcript)
- Classify transcript into copywriting framework:
  - PAS (Problem, Agitate, Solution)
  - BAB (Before, After, Bridge)
  - AIDA (Attention, Interest, Desire, Action)
  - PPPP (Picture, Promise, Prove, Push)
  - OCR (One-time-offer, Call-to-action, Result)
- Output both framework name AND stage breakdown:
  ```json
  {
    "copy_structure": {
      "framework": "AIDA",
      "breakdown": {
        "attention": "Opening hook about challenge...",
        "interest": "Medal achievement system...",
        "desire": "Personal transformation story...",
        "action": "Sign up call-to-action..."
      }
    }
  }
  ```

**5. TagsKG Output Only**
- All ML-generated tags written to TagsKG column only
- Airtable context fields are INPUT only (read, not written)

### Reusability Opportunities

- Extend `llm.py` with dynamic prompt builder
- Extend `airtable.py` to fetch full record context (not just find by ID)
- Modify `video.py` frame extraction for weighted sampling
- Integrate with existing audio pipeline for speech-to-text

### Scope Boundaries

**In Scope:**
- First-3-seconds weighted frame extraction
- Dynamic prompt generation from Airtable ART Grid context
- Visual Hook structured output (action, subject, environment)
- Copy Structure classification with stage breakdown
- Speech-to-text integration for transcript analysis
- English-only tag output

**Out of Scope:**
- Modifying Airtable columns other than TagsKG
- Multi-language tag support
- Training custom ML models (using existing/pretrained models)
- Real-time video streaming analysis

### Technical Considerations

- Integration with existing `find_by_art_id()` function
- Extend pyairtable queries to fetch additional columns
- Frame extraction must handle variable video lengths
- Speech-to-text model selection (Whisper recommended)
- LLM prompt size limits when including context + frames + transcript
