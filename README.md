# APG Posting Desk

Installable PWA for Alpha Premiere Group's human-in-the-loop Facebook posting
workflow.

The app prepares everything needed for a post, then lets an operator review and
publish manually in Facebook Web. After the operator pastes the live Facebook
URL back into the dashboard, the backend logs it to the tracker sheet and daily
report document.

## Workflow

1. Operator enters the assigned property name.
2. Backend fetches the property folder, downloads at least three images, and
   extracts the caption details document.
3. NVIDIA NIM generates a caption with APG rules: no emojis, no "least term",
   and no "negotiables".
4. PWA displays the caption and images for review.
5. Operator copies the caption, downloads the images or image zip, and posts in
   Facebook Web.
6. Operator pastes the published Facebook URL into the PWA and clicks Log Post.
7. Backend appends the tracker sheet row and daily progress report entry.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
npm install
copy .env.example .env
```

Edit `.env` with Google and NVIDIA credentials. Do not commit `.env`.

## Configure

Defaults live in `config.yaml`. Environment variables override YAML values.

Required values for caption generation and logging:

- `GOOGLE_APPLICATION_CREDENTIALS`
- `NVIDIA_API_KEY`
- `POSTING_TRACKER_SHEET_ID`
- `DAILY_REPORT_DOC_ID`
- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_APP_ID`
- `VITE_APG_GOOGLE_DOMAIN`

The default caption model is NVIDIA NIM `stepfun-ai/step-3.7-flash` at
`https://integrate.api.nvidia.com/v1/chat/completions`.

## Run The PWA With Vite

The default dev command starts both services:

- FastAPI backend on `http://localhost:8000`
- Vite PWA frontend on `http://localhost:5173`

It uses demo mode with the local Novaliches fixture, so it starts without live
Google or NVIDIA credentials.

```powershell
npm run dev
```

Open:

```text
http://localhost:5173
```

For phones and other devices on the same network, open:

```text
http://<your-computer-lan-ip>:5173
```

For live Google/NVIDIA operation:

```powershell
npm run dev:live
```

Backend only:

```powershell
npm run dev:api
```

Frontend only:

```powershell
npm run dev:web
```

Dry-run queue validation:

```powershell
python -m apg_automation.main --dry-run --local-folder "C:/Users/Deign/Downloads/APG Prototype System for Automated Posting/Novaliches, 440 Bagbag"
```

## Test

```powershell
python -m pytest -q
```

## Architecture

- `review_pipeline.py`: split preparation and logging workflow.
- `web_app.py`: FastAPI routes and PWA static serving.
- `firebase_auth.py`: Firebase Admin ID token verification.
- `firebase_queue.py`: Firestore-backed property queue claims.
- `static/`: installable dashboard UI, manifest, and service worker.
- `local_folder.py`: local fixture source for testing without live Google access.
- `google_workspace_mcp.py`: MCP-oriented Google Workspace data boundary.
