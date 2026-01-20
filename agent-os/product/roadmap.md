# Product Roadmap

1. [x] **Configuration & Credentials Management** — Create secure config system for storing Synology, Airtable, RunPod S3, and SSH credentials with environment variable support and .env file loading. `S`

2. [x] **Airtable Integration** — Implement Airtable API client to read Art ID column, find records by Art ID, and update TagsKG column with JSON data. `S`

3. [x] **Local Video Processing Mode** — Build core video frame extraction and Qwen3-VL inference pipeline that processes a local video file and outputs structured JSON. `M`

4. [x] **TUI Framework Setup** — Set up Textual-based TUI with main menu, video list view, JSON preview panel, and confirmation dialogs. `M`

5. [x] **Synology NAS Integration** — Implement SSH/SFTP connection to Synology NAS, list videos matching pattern `V - *a{id}.mp4`, and download selected videos. `S`

6. [x] **RunPod S3 Sync** — Implement S3 upload to RunPod bucket and verification that files are accessible on the RunPod volume. `S`

7. [x] **RunPod vLLM Orchestration** — SSH into RunPod, trigger vLLM inference on synced videos, and retrieve JSON results. `M`

8. [x] **End-to-End Pipeline with Confirmations** — Wire all components together with TUI confirmation steps: video selection → S3 sync confirm → LLM output review → Airtable update confirm. `M`

9. [x] **Batch Processing & Progress** — Add progress bars, batch video processing, error handling with retry, and summary report at completion. `S`

> Notes
> - Items 1-4 form the MVP for local testing
> - Items 5-7 add production infrastructure
> - Item 8-9 complete the full pipeline with UX polish
