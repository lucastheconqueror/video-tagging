# Task Breakdown: Airtable Integration

## Overview
Total Tasks: 10

## Task List

### Setup

#### Task Group 1: Dependencies & Exceptions
**Dependencies:** None

- [ ] 1.0 Complete setup
  - [ ] 1.1 Add pyairtable to requirements.txt
  - [ ] 1.2 Create `src/videotagger/exceptions.py` with custom exceptions
    - `RecordNotFoundError`
    - `AirtableAPIError`

**Acceptance Criteria:**
- pyairtable is installable
- Custom exceptions are defined

### Airtable Client

#### Task Group 2: Core Airtable Functions
**Dependencies:** Task Group 1

- [ ] 2.0 Complete Airtable client
  - [ ] 2.1 Write 4-6 focused tests for Airtable functions
    - Test find_by_art_id returns record when found
    - Test find_by_art_id raises RecordNotFoundError when not found
    - Test update_tags updates record successfully
    - Test extract_art_id parses filename correctly
    - Test extract_art_id raises ValueError for invalid filename
  - [ ] 2.2 Create `src/videotagger/airtable.py` module
  - [ ] 2.3 Implement `extract_art_id(filename: str)` function
    - Regex pattern: `a\d+` before file extension
    - Return extracted Art ID string
    - Raise ValueError if not found
  - [ ] 2.4 Implement `find_by_art_id(art_id: str)` function
    - Use pyairtable Table.first() with formula filter
    - Return record dict if found
    - Raise RecordNotFoundError if not found
  - [ ] 2.5 Implement `update_tags(art_id: str, tags: dict)` function
    - Find record first
    - Update TagsKG field with JSON string
    - Return updated record
  - [ ] 2.6 Implement `get_airtable_client()` factory
    - Load config from Settings
    - Return configured Table instance
  - [ ] 2.7 Ensure tests pass
    - Run only tests from 2.1

**Acceptance Criteria:**
- All 4-6 tests pass
- Art ID extraction works for valid filenames
- Find and update operations work correctly
- Proper error handling for missing records

### Quality Assurance

#### Task Group 3: Code Quality & Verification
**Dependencies:** Task Group 2

- [ ] 3.0 Complete quality checks
  - [ ] 3.1 Run ruff linting and fix issues
  - [ ] 3.2 Verify type hints are complete
  - [ ] 3.3 Run all feature tests

**Acceptance Criteria:**
- Zero ruff linting errors
- All type hints present
- All tests pass

## Execution Order

1. Setup (Task Group 1)
2. Airtable Client (Task Group 2)
3. Quality Assurance (Task Group 3)
