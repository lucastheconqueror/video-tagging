# Tech Stack

## Overview
This is a Python automation/CLI project with TUI interface. No web frontend required.

## Core Application

### Language & Runtime
- **Language:** Python 3.11+
- **Package Manager:** pip with `requirements.txt` (or Poetry)
- **Environment:** Local development + Dockerized for deployment

### TUI Framework
- **Primary:** Textual (modern Python TUI framework)
- **Fallback:** Rich (for simpler output formatting)

### Video Processing
- **Frame Extraction:** OpenCV (`cv2`) or `ffmpeg-python`
- **Model:** Qwen3-VL via vLLM on RunPod

## External Services

### Synology NAS
- **Protocol:** SSH/SFTP via `paramiko`
- **Path:** `/volume1/The Conqueror NAS/Video Team`
- **Pattern:** Files matching `V - *a{id}.mp4`

### Airtable
- **SDK:** `pyairtable`
- **Base ID:** `appJ2qQblTz0tt7Zx`
- **Table ID:** `tblHJVV34fcoMPsam`
- **Columns:** Art ID (read), TagsKG (write)

### RunPod
- **S3 Storage:** 
  - Endpoint: `https://s3api-eu-ro-1.runpod.io`
  - Bucket: `sujcaslgwu`
  - SDK: `boto3`
- **SSH Access:** Via `paramiko` or subprocess
- **Pod ID:** `azvih68libdpx4`

### vLLM Inference
- **Model:** Qwen3-VL (vision-language model)
- **Server:** vLLM running on RunPod GPU instance
- **API:** OpenAI-compatible endpoint

## Configuration

### Credentials Management
- **Primary:** Environment variables
- **Local Dev:** `.env` file with `python-dotenv`
- **Secrets:** Never committed to git

### Required Environment Variables
```bash
# Synology
SYNOLOGY_HOST=TheConqueror
SYNOLOGY_USER=Lucas
SYNOLOGY_PASSWORD=<secret>
SYNOLOGY_VIDEO_PATH=/volume1/The Conqueror NAS/Video Team

# Airtable
AIRTABLE_API_KEY=<secret>
AIRTABLE_BASE_ID=appJ2qQblTz0tt7Zx
AIRTABLE_TABLE_ID=tblHJVV34fcoMPsam

# RunPod S3
RUNPOD_S3_ENDPOINT=https://s3api-eu-ro-1.runpod.io
RUNPOD_S3_BUCKET=sujcaslgwu
RUNPOD_S3_ACCESS_KEY=<secret>
RUNPOD_S3_SECRET_KEY=<secret>

# RunPod SSH
RUNPOD_SSH_HOST=ssh.runpod.io
RUNPOD_SSH_USER=b0jzswbowem8i8-644118d5
RUNPOD_SSH_KEY_PATH=~/.ssh/id_ed25519
RUNPOD_POD_ID=b0jzswbowem8i8
```

## Testing & Quality
- **Testing:** Pytest
- **Linting/Formatting:** Ruff
- **Type Checking:** mypy (optional)

## Key Dependencies
```
textual>=0.40.0
rich>=13.0.0
pyairtable>=2.0.0
boto3>=1.28.0
paramiko>=3.0.0
python-dotenv>=1.0.0
opencv-python>=4.8.0
requests>=2.31.0
```
