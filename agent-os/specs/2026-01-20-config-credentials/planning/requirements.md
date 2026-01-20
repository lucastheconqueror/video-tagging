# Spec Requirements: Configuration & Credentials Management

## Initial Description
**Configuration & Credentials Management** — Create secure config system for storing Synology, Airtable, RunPod S3, and SSH credentials with environment variable support and .env file loading.

## Requirements Discussion

### First Round Questions

**Q1:** I assume we'll use a single `.env` file at the project root with `python-dotenv` for loading. Is that correct, or would you prefer a different approach (e.g., YAML config file, multiple env files for different environments)?
**Answer:** Confirmed - single `.env` file with `python-dotenv`

**Q2:** I'm thinking we'll create a `config.py` module with Pydantic models for validation and type safety. Should we use simple dataclasses instead, or is Pydantic preferred?
**Answer:** Confirmed - Pydantic models for validation

**Q3:** I assume credentials should never have defaults — the app should fail fast with a clear error if any required credential is missing. Is that correct, or should some have fallback defaults?
**Answer:** Confirmed - fail fast with clear errors, no defaults for credentials

**Q4:** For the SSH key path (`~/.ssh/id_ed25519`), should we expand `~` automatically, or require absolute paths in the config?
**Answer:** Confirmed - expand `~` automatically

**Q5:** I assume we'll create a `.env.example` file with placeholder values that gets committed to git (without real secrets). Is that correct?
**Answer:** Confirmed - create `.env.example`

**Q6:** Should there be a CLI command to validate the config (e.g., `python -m videotagger validate-config`) that checks all credentials are present and optionally tests connections?
**Answer:** Confirmed - include config validation command

**Q7:** Is there anything that should be explicitly **excluded** from this config system (e.g., LLM prompts, video patterns, or other non-credential settings)?
**Answer:** No exclusions specified - config system handles credentials only

### Existing Code to Reference
No similar existing features identified for reference.

### Follow-up Questions
None required - all questions confirmed.

## Visual Assets

### Files Provided:
No visual assets provided.

## Requirements Summary

### Functional Requirements
- Load credentials from `.env` file using `python-dotenv`
- Validate all credentials using Pydantic models
- Fail fast with clear error messages when required credentials are missing
- Automatically expand `~` in file paths (SSH key path)
- Provide CLI command to validate configuration
- Create `.env.example` template file

### Credential Groups to Support
1. **Synology NAS**
   - SYNOLOGY_HOST
   - SYNOLOGY_USER
   - SYNOLOGY_PASSWORD
   - SYNOLOGY_VIDEO_PATH

2. **Airtable**
   - AIRTABLE_API_KEY
   - AIRTABLE_BASE_ID
   - AIRTABLE_TABLE_ID

3. **RunPod S3**
   - RUNPOD_S3_ENDPOINT
   - RUNPOD_S3_BUCKET
   - RUNPOD_S3_ACCESS_KEY
   - RUNPOD_S3_SECRET_KEY

4. **RunPod SSH**
   - RUNPOD_SSH_HOST
   - RUNPOD_SSH_USER
   - RUNPOD_SSH_KEY_PATH
   - RUNPOD_POD_ID

### Reusability Opportunities
- Pydantic BaseSettings pattern can be reused for future config needs
- Validation logic can be extended for connection testing

### Scope Boundaries
**In Scope:**
- `.env` file loading with python-dotenv
- Pydantic models for each credential group
- Path expansion for file paths
- `.env.example` template
- CLI validation command
- Clear error messages for missing/invalid config

**Out of Scope:**
- Connection testing (validate credentials work) - future enhancement
- Multiple environment support (.env.production, etc.)
- Secrets encryption
- LLM prompts or non-credential configuration

### Technical Considerations
- Use Pydantic v2 `BaseSettings` for env loading
- Group credentials into logical Pydantic models (SynologyConfig, AirtableConfig, etc.)
- Single `Settings` class that aggregates all config groups
- `@field_validator` for path expansion
- Entry point: `python -m videotagger validate-config`
