# Specification: Airtable Integration

## Goal
Create an Airtable client that can find records by Art ID and update the TagsKG column with JSON metadata extracted from video analysis.

## User Stories
- As a developer, I want to find an Airtable record by Art ID so that I can update it with video tags.
- As a developer, I want to extract the Art ID from a video filename so that I can match it to the correct Airtable record.

## Specific Requirements

**Airtable Client Module**
- Create `src/videotagger/airtable.py` module
- Use pyairtable library for API access
- Initialize client with credentials from existing AirtableConfig
- Provide clean interface for find and update operations

**Find Record by Art ID**
- Implement `find_by_art_id(art_id: str)` function
- Use Airtable formula filter: `{Art ID} = "a1433"`
- Return record ID and current fields if found
- Raise custom `RecordNotFoundError` if no match
- Handle API errors gracefully

**Update TagsKG Column**
- Implement `update_tags(art_id: str, tags: dict)` function
- Serialize tags dict to JSON string
- Find record first, then update by record ID
- Return updated record data on success
- Raise `RecordNotFoundError` if Art ID not found

**Art ID Extraction**
- Implement `extract_art_id(filename: str)` function
- Pattern: match `a` followed by digits at end of filename before extension
- Examples: `V - something a1433.mp4` → `a1433`
- Raise `ValueError` if no Art ID found in filename

**Error Handling**
- Create custom exceptions in `src/videotagger/exceptions.py`
- `RecordNotFoundError` - Art ID not found in Airtable
- `AirtableAPIError` - Wrap pyairtable exceptions
- Provide clear, actionable error messages

**Integration with Config**
- Accept AirtableConfig or load from Settings
- Provide `get_airtable_client()` factory function
- Support dependency injection for testing

## Visual Design
No visual assets provided.

## Existing Code to Leverage

**src/videotagger/config.py**
- `AirtableConfig` model with `api_key`, `base_id`, `table_id`
- `get_settings()` function to load configuration
- Pattern for Pydantic models and validation

## Out of Scope
- Batch updates for multiple records
- Creating new Airtable records
- Reading columns other than Art ID
- Caching API responses
- Rate limiting (pyairtable handles internally)
- Syncing all records or listing operations
