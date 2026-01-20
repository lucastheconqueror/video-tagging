# Task Breakdown: Configuration & Credentials Management

## Overview
Total Tasks: 12

## Task List

### Project Setup

#### Task Group 1: Project Structure & Dependencies
**Dependencies:** None

- [x] 1.0 Complete project setup
  - [x] 1.1 Create project directory structure
    - Create `src/videotagger/` package directory
    - Create `src/videotagger/__init__.py`
    - Create empty `src/videotagger/config.py`
    - Create empty `src/videotagger/__main__.py`
  - [x] 1.2 Create `requirements.txt` with dependencies
    - `pydantic>=2.0.0`
    - `pydantic-settings>=2.0.0`
    - `python-dotenv>=1.0.0`
    - `ruff>=0.1.0` (dev dependency)
    - `pytest>=7.0.0` (dev dependency)
  - [x] 1.3 Create `.env.example` template
    - Include all credential groups with placeholder values
    - Add comments explaining each section
  - [x] 1.4 Update `.gitignore` for Python project
    - Add `.env` to prevent committing secrets
    - Add standard Python ignores (`__pycache__`, `*.pyc`, `.venv`, etc.)

**Acceptance Criteria:**
- Project structure exists with all required directories
- Dependencies file is complete
- `.env.example` documents all required variables
- `.gitignore` protects secrets

### Configuration Layer

#### Task Group 2: Pydantic Settings Models
**Dependencies:** Task Group 1

- [x] 2.0 Complete configuration models
  - [x] 2.1 Write 4-6 focused tests for config validation
    - Test missing required field raises ValidationError
    - Test valid config loads successfully
    - Test path expansion works for SSH key path
    - Test SSH key path validation (file exists check)
  - [x] 2.2 Create `SynologyConfig` model
    - Fields: `host`, `user`, `password`, `video_path`
    - All fields required (no defaults)
    - Use `env_prefix = "SYNOLOGY_"`
  - [x] 2.3 Create `AirtableConfig` model
    - Fields: `api_key`, `base_id`, `table_id`
    - All fields required (no defaults)
    - Use `env_prefix = "AIRTABLE_"`
  - [x] 2.4 Create `RunPodS3Config` model
    - Fields: `endpoint`, `bucket`, `access_key`, `secret_key`
    - All fields required (no defaults)
    - Use `env_prefix = "RUNPOD_S3_"`
  - [x] 2.5 Create `RunPodSSHConfig` model
    - Fields: `host`, `user`, `key_path`, `pod_id`
    - All fields required (no defaults)
    - Use `env_prefix = "RUNPOD_SSH_"`
    - Add `@field_validator` for `key_path` to expand `~` and validate file exists
  - [x] 2.6 Create root `Settings` class
    - Aggregate all config groups as nested models
    - Use `SettingsConfigDict` with `env_file=".env"`
    - Create `get_settings()` helper function with caching
  - [x] 2.7 Ensure config tests pass
    - Run only the tests written in 2.1
    - Verify all validation works correctly

**Acceptance Criteria:**
- All 4-6 tests pass
- Missing credentials raise clear ValidationError
- Path expansion works for `~` in SSH key path
- Invalid paths are rejected with helpful message

### CLI Layer

#### Task Group 3: Validation Command
**Dependencies:** Task Group 2

- [x] 3.0 Complete CLI validation command
  - [x] 3.1 Write 2-4 focused tests for CLI command
    - Test successful validation prints confirmation
    - Test missing config prints error message
    - Test masked credential display (first/last 4 chars)
  - [x] 3.2 Implement `validate-config` command in `__main__.py`
    - Load dotenv and instantiate Settings
    - On success: print confirmation with masked credentials
    - On failure: catch ValidationError and print user-friendly errors
  - [x] 3.3 Add credential masking utility
    - Show first 4 and last 4 characters: `patN...0e4e`
    - Handle short credentials gracefully
  - [x] 3.4 Ensure CLI tests pass
    - Run only the tests written in 3.1
    - Verify command works end-to-end

**Acceptance Criteria:**
- `python -m videotagger validate-config` runs successfully
- Valid config shows masked credential preview
- Invalid config shows clear, actionable error messages
- All 2-4 tests pass

### Quality Assurance

#### Task Group 4: Code Quality & Final Verification
**Dependencies:** Task Groups 1-3

- [x] 4.0 Complete quality checks
  - [x] 4.1 Run ruff linting and fix issues
    - Ensure all code passes `ruff check`
    - Apply `ruff format` for consistent style
  - [x] 4.2 Verify type hints are complete
    - All functions have parameter and return type hints
    - No `Any` types unless absolutely necessary
  - [x] 4.3 Run all feature tests
    - Run tests from 2.1 and 3.1 (approximately 6-10 tests)
    - Verify all pass
  - [x] 4.4 Manual end-to-end verification
    - Create a test `.env` file with real placeholder structure
    - Run `python -m videotagger validate-config`
    - Verify output is correct

**Acceptance Criteria:**
- Zero ruff linting errors
- All type hints present
- All 6-10 tests pass
- CLI command works manually

## Execution Order

Recommended implementation sequence:
1. Project Setup (Task Group 1)
2. Configuration Models (Task Group 2)
3. CLI Command (Task Group 3)
4. Quality Assurance (Task Group 4)
