# Product Mission

## Pitch
**VideoAirtableTagging** is a Python TUI tool that helps video/content teams automatically tag TikTok videos with AI-extracted metadata by leveraging Qwen3-VL vision model on RunPod and syncing results to Airtable.

## Users

### Primary Customers
- **Video/Content Teams**: Teams managing large libraries of TikTok content who need consistent, automated metadata tagging

### User Personas
**Content Manager** (25-40)
- **Role:** Video team lead or content curator
- **Context:** Managing hundreds of TikTok videos stored on Synology NAS, needs to categorize and search content efficiently
- **Pain Points:** Manual tagging is time-consuming and inconsistent; hard to find videos by mood, location, or brand mentions
- **Goals:** Automated, consistent video metadata extraction; searchable Airtable database of tagged content

## The Problem

### Manual Video Tagging is Slow and Inconsistent
Manually watching and tagging videos with location, brands, mood, and other metadata takes significant time and produces inconsistent results across team members.

**Our Solution:** Use Qwen3-VL vision model to automatically analyze video frames and extract structured JSON metadata, then push directly to Airtable.

## Differentiators

### End-to-End Pipeline with Confirmation Steps
Unlike generic AI tools, we provide a complete pipeline from NAS → S3 → RunPod → Airtable with TUI confirmation at each step, ensuring quality control before data is committed.

### Local Testing Mode
Process local video files directly for development and testing without requiring the full Synology/S3/RunPod infrastructure.

## Key Features

### Core Features
- **Synology Video Pull**: Connect to NAS and list videos matching pattern `V - *a{id}.mp4`
- **TUI Video Selection**: Interactive terminal UI to select all or specific videos for processing
- **S3 Sync to RunPod**: Transfer selected videos to RunPod network volume via S3
- **Qwen3-VL Processing**: Extract location, brand_objects, visual_text, mood, excitement from video frames
- **JSON Preview & Confirmation**: Review extracted metadata before committing to Airtable
- **Airtable Update**: Match Art ID and update TagsKG column with validated JSON

### Development Features
- **Local Video Mode**: Skip Synology/S3 and process local video files directly for testing
- **Step-by-Step Confirmation**: Pause and confirm at each pipeline stage
