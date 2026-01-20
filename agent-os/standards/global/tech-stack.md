## Tech stack

This document defines the technical stack for the project. It serves as the single source of truth for all team members and agents.

### Project Structure Roles
- **Frontend/Web App:** Next.js (User Interface, Auth, standard CRUD)
- **Automation/Workers:** Python (Data processing, scheduled tasks, background jobs)

### 1. Web Application (Frontend)
- **Framework:** Next.js 15+ (App Router)
- **Runtime:** Node.js (Standard)
- **Language:** TypeScript
- **Package Manager:** pnpm (Primary), npm (Fallback)
- **UI Components:** shadcn/ui (via `npx shadcn@latest add`), Lucide React
- **Styling:** Tailwind CSS + TweakCN

### 2. Automation & Scripting
- **Language:** Python 3.11+
- **Environment:** Dockerized (Required for deployment)
- **Package Manager:** pip (requirements.txt) or Poetry
- **Key Libraries:** `firebase-admin` (Python SDK), `google-cloud-storage`

### Infrastructure & Services
- **Database:** Firebase Firestore (NoSQL) - *Shared by both Next.js and Python*
- **File Storage:** Google Cloud Storage - *Shared access*
- **Authentication:** Firebase Auth
- **Hosting Strategy:**
  - **Next.js:** Vercel (Primary) or Dokploy (Secondary, via Docker)
  - **Python Scripts:** Dokploy (VPS) - *Always Dockerized*
- **CI/CD:** GitHub Actions

### Testing & Quality
- **JS/TS:** Vitest, ESLint, Prettier
- **Python:** Pytest, Ruff (Linting/Formatting)

