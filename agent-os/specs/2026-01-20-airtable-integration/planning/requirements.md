# Spec Requirements: Airtable Integration

## Initial Description
**Airtable Integration** — Implement Airtable API client to read Art ID column, find records by Art ID, and update TagsKG column with JSON data.

## Requirements Discussion

### First Round Questions

**Q1:** I assume the Art ID column contains values like "a1433" that match the suffix in video filenames. Is that correct?
**Answer:** Confirmed - Art ID format is like "a1433" or "a13332"

**Q2:** I assume TagsKG should store the JSON as a string (Airtable long text field). Is that correct, or is it a JSON field type?
**Answer:** Confirmed - store as JSON string in long text field

**Q3:** Should we overwrite existing TagsKG values, or append/merge with existing data?
**Answer:** Overwrite existing values

**Q4:** Do we need to handle batch updates (multiple records at once), or is single-record update sufficient for now?
**Answer:** Single-record update is sufficient for MVP; batch can be added later

**Q5:** Should we validate that the Art ID exists in Airtable before attempting to update?
**Answer:** Yes - fail gracefully with clear error if Art ID not found

### Existing Code to Reference
- `src/videotagger/config.py` - AirtableConfig model with credentials

### Follow-up Questions
None required.

## Visual Assets

### Files Provided:
No visual assets provided.

## Requirements Summary

### Functional Requirements
- Create Airtable client using pyairtable library
- Find record by Art ID column value
- Update TagsKG column with JSON string
- Extract Art ID from video filename pattern `V - *a{id}.mp4`
- Handle "record not found" gracefully with clear error
- Use credentials from existing config system

### API Operations
1. **find_by_art_id(art_id: str)** - Find single record by Art ID
2. **update_tags(art_id: str, tags: dict)** - Update TagsKG for a record
3. **extract_art_id(filename: str)** - Parse Art ID from video filename

### Scope Boundaries
**In Scope:**
- Airtable client wrapper using pyairtable
- Find record by Art ID
- Update TagsKG column
- Art ID extraction from filename
- Error handling for missing records

**Out of Scope:**
- Batch updates (future enhancement)
- Creating new records
- Reading other columns beyond Art ID
- Caching or rate limiting (pyairtable handles this)

### Technical Considerations
- Use pyairtable library (official Airtable Python SDK)
- Integrate with existing AirtableConfig from config.py
- Return Pydantic models for type safety
- Regex pattern for Art ID extraction: `a\d+` at end of filename
