# Python Automation & Scripting Standards

## Role & Scope
**Usage:** Strictly for background automation, data processing, and scheduled tasks.
**Non-Usage:** Do NOT use Python to serve web pages or API endpoints (use Next.js for that).

## Infrastructure & Runtime
- **Deployment:** All Python scripts must be **Dockerized**.
- **Container:** Use strict `python:3.11-slim` or newer base images.
- **Environment Variables:**
  - Load via `python-dotenv` for local development.
  - Inject via Dokploy/Docker for production.
  - **Never** hardcode credentials.

## Firebase & Cloud Integration
**Shared Access:** Python scripts access the same Firestore/Storage as the Next.js app.
- **Auth:** Use `firebase-admin` initialized with a Service Account (JSON credential).
- **Pattern:**
  1. Initialize App: `firebase_admin.initialize_app(cred)`
  2. DB Access: `db = firestore.client()`
  3. Storage Access: `bucket = storage.bucket()`

## Code Quality (Ruff)
- **Linter/Formatter:** Use `ruff` for both linting and formatting.
- **Type Hinting:** Mandatory. Use standard Python `typing` (e.g., `def process_data(items: list[str]) -> dict:`).

## File Structure
- Place automation scripts in a dedicated root folder (e.g., `/automation` or `/scripts`).
- Must include a `Dockerfile` and `requirements.txt` in that specific folder for independent deployment.

