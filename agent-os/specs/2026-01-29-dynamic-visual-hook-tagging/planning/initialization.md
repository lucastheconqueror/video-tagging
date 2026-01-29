# Spec Initialization: Dynamic Visual Hook Tagging

## Raw Idea (User's Exact Description)

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

Audio: Copy Storyline. We need to take the basic concepts from the airtable and create dynamic tags.

Copy Structure detection: will need speech-to-text model that takes the audio and converts it into a Copy Structure classification.

Key insight: First step is to create a dynamic Prompt - when we fetch video from NAS, we find its art ID and search for it in the Airtable and populate the prompt.

Frame sampling strategy: Send most information in first three seconds, then maybe 1 frame every 2 seconds. Really need to dive into the visual hook.

## Date Created
2026-01-29
