# Spec Initialization

## Raw Idea
**Airtable Integration** — Implement Airtable API client to read Art ID column, find records by Art ID, and update TagsKG column with JSON data.

## Context
This is the second feature in the roadmap. It builds on the configuration system (Feature 1) and provides the data layer for storing video tag results.

## Known Requirements
- Connect to Airtable using credentials from config
- Base ID: appJ2qQblTz0tt7Zx
- Table ID: tblHJVV34fcoMPsam
- Read "Art ID" column to match videos
- Write to "TagsKG" column with JSON metadata from Qwen3-VL
- Video files have Art ID in filename (e.g., `V - something a1433.mp4`)
