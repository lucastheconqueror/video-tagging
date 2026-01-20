# Specification: Configuration & Credentials Management

## Goal
Create a secure, validated configuration system that loads credentials from environment variables and `.env` files, providing type-safe access to Synology, Airtable, and RunPod settings with clear error messages on misconfiguration.

## User Stories
- As a developer, I want to load all credentials from a `.env` file so that I can easily configure the application locally without hardcoding secrets.
- As a developer, I want the app to fail fast with clear error messages when credentials are missing so that I can quickly identify configuration problems.

## Specific Requirements

**Project Structure**
- Create `src/videotagger/` package as the main application module
- Place configuration code in `src/videotagger/config.py`
- Create `src/videotagger/__main__.py` for CLI entry point
- Include `requirements.txt` at project root with all dependencies

**Pydantic Settings Models**
- Use Pydantic v2 `BaseSettings` with `SettingsConfigDict` for env loading
- Create separate model classes: `SynologyConfig`, `AirtableConfig`, `RunPodS3Config`, `RunPodSSHConfig`
- Create root `Settings` class that aggregates all config groups as nested models
- All credential fields are required (no defaults) to enforce fail-fast behavior

**Environment Variable Loading**
- Use `python-dotenv` to load `.env` file from project root
- Call `load_dotenv()` before instantiating Settings
- Support standard environment variable override (env vars take precedence over `.env`)

**Path Expansion**
- Use `@field_validator` on `RUNPOD_SSH_KEY_PATH` to expand `~` to user home directory
- Use `Path.expanduser()` for expansion
- Validate that the expanded path exists and is a file

**Error Handling**
- Pydantic's `ValidationError` provides field-specific error messages automatically
- Wrap Settings instantiation in try/except to catch and format validation errors
- Display user-friendly error listing which fields are missing or invalid

**CLI Validation Command**
- Entry point: `python -m videotagger validate-config`
- Load and validate all configuration
- On success: print confirmation with masked credential preview (show first/last 4 chars)
- On failure: print clear error messages for each invalid field

**Environment Example File**
- Create `.env.example` with all required variables and placeholder values
- Add comments explaining each credential group
- Add `.env` to `.gitignore` to prevent committing secrets

**Type Hints & Code Quality**
- All functions and methods must have complete type hints
- Use `ruff` for linting and formatting
- Follow Python 3.11+ syntax and patterns

## Visual Design
No visual assets provided.

## Existing Code to Leverage
No existing code in this project - this is the foundation module.

## Out of Scope
- Connection testing (verifying credentials actually work with external services)
- Multiple environment support (`.env.production`, `.env.staging`, etc.)
- Secrets encryption or secure storage beyond environment variables
- LLM prompts, video patterns, or other non-credential configuration
- Docker configuration (will be added in later specs)
- Integration with Synology, Airtable, or RunPod APIs (separate specs)
