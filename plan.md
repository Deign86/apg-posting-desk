# APG Posting Desk — Project Plan

> **Repo:** Local workspace `APG Prototype System for Automated Posting`
> **Linked repo:** `Deign86/apg-posting-desk` (GitHub)
> **Shared backend:** One Supabase project with `Deign86/apg-website` (ref `ldtavdybcgwjgticrymz`)
> **Status:** Human-in-the-loop posting workflow; Supabase migration in progress
> **Last updated:** 2026-07-05

---

## 1. Project Overview

APG Posting Desk is a **Python FastAPI backend + Vite PWA frontend** that automates the preparation stage of Alpha Premier Group's Facebook property posting workflow. A human operator always performs the actual Facebook publish step — the desk handles everything up to and after that moment.

### User Flow

```
Operator enters property name
  → Backend fetches property folder + images + caption doc
  → NVIDIA NIM generates APG-rule-compliant caption
  → PWA shows 5-tab review: Details → Photos → Caption → Publish → Log
  → Operator copies caption + downloads images, posts to Facebook manually
  → Operator pastes live Facebook URL back into the PWA
  → Backend logs to Google Sheets tracker + daily report document
```

### Core Constraints (non-negotiable)

- **Facebook posting is always manual.** Backend accepts a human-supplied live URL; no Graph API automation.
- **Demo mode runs without live credentials.** Google, Firebase, and NVIDIA credentials are not required for local development.
- **Repository-style adapters.** All external system calls (Google Drive, Firebase, Supabase) go through adapter classes so tests use fakes.
- **Caption rules are always enforced.** No emojis, no "least term", no "negotiables" — in both AI prompts and validation.
- **No secrets in source.** `.env` is gitignored; real credentials are never documented in plan files.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    APG Posting Desk                              │
│                                                                 │
│  ┌──────────────────┐     ┌───────────────────────────────┐    │
│  │ Vite PWA Frontend │     │  FastAPI Backend              │    │
│  │  (src/main.js)    │     │  (apg_automation/)            │    │
│  │                    │     │                               │    │
│  │  5-tab flow:      │     │  /api/prepare                 │    │
│  │  1. Property      │────▶│  /api/log                     │    │
│  │  2. Photos        │     │  /api/queue/next              │    │
│  │  3. Caption       │     │  /api/jobs/*                  │    │
│  │  4. Publish       │     │  /prepared/* (assets)         │    │
│  │  5. Log           │     │                               │    │
│  └──────────────────┘     └───────────┬───────────────────┘    │
│                                        │                        │
└────────────────────────────────────────┼────────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
           ┌────────▼────────┐  ┌──────▼───────┐  ┌────────▼────────┐
           │  Supabase       │  │  Google      │  │  Firebase       │
           │  (shared with   │  │  Workspace   │  │  (legacy/demo)  │
           │   apg-website)  │  │  (tracking)  │  │                  │
           │                  │  │              │  │                  │
           │  Postgres:       │  │  Sheets      │  │  Firestore:      │
           │  posting_jobs   │  │  tracker     │  │  queue claims    │
           │  posting_job_   │  │  doc         │  │  (demo path)     │
           │    assets       │  │              │  │                  │
           │  posted_log     │  │              │  │                  │
           │  daily_report   │  │              │  │                  │
           │                  │  │              │  │                  │
           │  Storage:       │  │              │  │                  │
           │  apg-public     │  │              │  │                  │
           │  apg-private    │  │              │  │                  │
           └─────────────────┘  └──────────────┘  └─────────────────┘
```

### Shared Supabase Backend (apg-website interop)

The desk shares **one Supabase project** (`ldtavdybcgwjgticrymz`) with `apg-website`.

| Owner | Tables | Notes |
|-------|--------|-------|
| **Both repos read** | `public.categories`, `public.transaction_types`, `public.properties`, `public.property_assets`, `public.property_asset_relations`, `public.raw_folder_mappings`, `public.ingestion_runs` | Website never writes to these |
| **Posting-desk owns** | `posting_desk.posting_jobs`, `posting_desk.posting_job_assets`, `posting_desk.posted_log`, `posting_desk.daily_report`, `posting_desk.audit_logs` | Workflow state + operational history |

See the `apg-website` repo's `SHARED_ASSET_ARCHITECTURE.md` for the full canonical asset model design.

---

## 3. Module Map

### Core Workflow

| Module | Role |
|--------|------|
| `main.py` | CLI entry, server bootstrap, demo/live service selection |
| `review_pipeline.py` | Core workflow: queue → asset fetch → caption generation → PWA payload → post logging |
| `web_app.py` | FastAPI app factory; `/api/prepare`, `/api/log`, `/api/queue/next`, asset serving |

### AI & Caption

| Module | Role |
|--------|------|
| `caption_generator.py` | NVIDIA NIM caption generation with APG rule validation + retry loop |
| `ai_clients.py` | Abstractions for AI provider clients (NVIDIA NIM primary; swap in future) |
| `models.py` | Pydantic request/response models |

### Content Sourcing

| Module | Role |
|--------|------|
| `local_folder.py` | Local filesystem content source (demo mode fixtures) |
| `google_drive.py` | Google Drive API integration (live mode) |
| `content_extractor.py` | Reads image bundles + caption documents from source |
| `folder_parser.py` | Parses raw folder names into structured property data |

### Queue & Job State

| Module | Role |
|--------|------|
| `queue_manager.py` | Validates property folders before preparation; enqueue/dequeue |
| `job_store.py` | In-memory job state (demo/local mode) |
| `supabase_queue.py` | Supabase-backed queue for persistent job state (live mode) |
| `supabase_job_store.py` | Supabase job persistence |

### Auth

| Module | Role |
|--------|------|
| `firebase_auth.py` | Firebase Admin ID token verification (legacy demo path) |
| `firebase_queue.py` | Firestore-backed property queue claims (legacy demo path) |
| `supabase_auth.py` | Supabase Auth + `profiles.role` verification (current) |
| `auth_deps.py` | FastAPI dependency injection for authenticated routes |

### Tracking & Reporting

| Module | Role |
|--------|------|
| `tracker_updater.py` | Appends rows to Google Sheets posting tracker |
| `google_tracking.py` | Google Docs daily report append |
| `supabase_tracking.py` | Supabase-backed tracking (current live path) |

### Supabase Integration

| Module | Role |
|--------|------|
| `supabase_client.py` | Supabase client singleton (anon + service_role) |
| `supabase_assets.py` | Asset repository — reads/writes `property_assets`, `property_asset_relations` |
| `asset_service.py` | Business logic layer for asset operations |
| `ingest.py` | CLI: Windows folder → Supabase import pipeline |

### Infrastructure

| Module | Role |
|--------|------|
| `config.py` | YAML defaults + env var overrides |
| `retry.py` | Retry decorators for external calls |
| `logging_config.py` | Structured logging setup |
| `__init__.py` | Package exports |

---

## 4. Frontend Structure

Vite PWA with 5-tab review flow. Vite proxies `/api` and `/prepared` to `http://127.0.0.1:8000`.

| File | Role |
|------|------|
| `index.html` | Vite entry point + PWA manifest link |
| `src/main.js` | PWA app logic: queue browsing, review UI, post logging |
| `src/styles.css` | All PWA styles |
| `public/manifest.webmanifest` | Installable PWA manifest |
| `public/service-worker.js` | Offline-capable service worker |
| `vite.config.js` | Dev proxy + build config |

### Tab Flow

```
Tab 1: Property Details     — location, size, transaction type
Tab 2: Photos               — image gallery, select/deselect for post
Tab 3: Caption              — AI-generated caption, edit, validate
Tab 4: Publish              — review summary, download zip, post to Facebook
Tab 5: Log                  — paste live Facebook URL, confirm log
```

---

## 5. Demo vs Live Mode

| Aspect | Demo Mode | Live Mode |
|--------|-----------|-----------|
| **Start command** | `npm run dev` | `npm run dev:live` |
| **Credentials needed** | None | Supabase, Firebase (legacy) or Supabase Auth (current) |
| **Content source** | `Novaliches, 440 Bagbag/` local fixture | Supabase `public.properties` + Google Drive |
| **Auth** | None (local only) | Firebase ID token verification or Supabase Auth |
| **Queue** | In-memory (`job_store.py`) | Supabase Firestore or Supabase tables |
| **Caption** | `DemoCaptionGenerator` (stub) | NVIDIA NIM (`CaptionGenerator`) |
| **Tracking** | No-op | Google Sheets + Docs via `tracker_updater.py` |

### Demo Mode Constraints

- Runs entirely without Google, Firebase, or NVIDIA credentials.
- Uses the `Novaliches, 440 Bagbag/` fixture folder for property data.
- `DemoCaptionGenerator` returns a static caption — no API calls.

---

## 6. Commands

```powershell
# Install
python -m pip install -r requirements.txt
npm install

# Dev (FastAPI + Vite, demo mode)
npm run dev

# Dev with live credentials
npm run dev:live

# Backend only
npm run dev:api

# Frontend only
npm run web

# Build frontend
npm run build

# Tests
python -m pytest -q

# Dry-run queue validation (local fixture)
python -m apg_automation.main --dry-run --local-folder "C:/Users/Deign/Downloads/APG Prototype System for Automated Posting/Novaliches, 440 Bagbag"

# Supabase ingest from APR LISTING
python -m apg_automation.ingest --source "C:/Users/Deign/Downloads/APG Prototype System for Automated Posting/APR LISTING" --dry-run
python -m apg_automation.ingest --source "C:/Users/Deign/Downloads/APG Prototype System for Automated Posting/APR LISTING" --verify
python -m apg_automation.ingest --source "C:/Users/Deign/Downloads/APG Prototype System for Automated Posting/APR LISTING"
```

---

## 7. Shared Supabase Data Model (Workflow-Owned Tables)

These tables live in the `posting_desk` schema of the shared Supabase project. The website never queries them.

### `posting_desk.posting_jobs`

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID PK | |
| `job_code` | TEXT UNIQUE | e.g. `APG-0705-001` |
| `property_id` | UUID FK → `public.properties` | |
| `status` | TEXT | `assigned` → `ready_for_review` → `ready_to_post` → `posted` → `archived` |
| `caption_draft` | TEXT | AI-generated before operator edit |
| `caption_final` | TEXT | Operator-approved caption |
| `caption_details` | TEXT | Extracted caption reference document content |
| `facebook_url` | TEXT | Operator-pasted live URL |
| `posted_at` | TIMESTAMPTZ | Set when `mark-posted` is called |
| `operator` | TEXT | Assigned operator name |

### `posting_desk.posting_job_assets`

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID PK | |
| `posting_job_id` | UUID FK | |
| `asset_id` | UUID FK → `public.property_assets` | |
| `display_order` | INT | Gallery order for this job |
| `selected` | BOOLEAN | Operator selection; frozen on approval |
| `caption_override` | TEXT | Per-asset caption override |

### `posting_desk.posted_log`

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID/BIGSERIAL PK | |
| `posting_job_id` | UUID FK | |
| `facebook_url` | TEXT | Final live URL |
| `posted_at` | TIMESTAMPTZ | |
| `operator` | TEXT | |

### `posting_desk.daily_report`

Aggregated view of daily posting activity for management reporting.

### `posting_desk.audit_logs`

Immutable action log: `job_created`, `asset_selected`, `caption_approved`, `posted`, etc.

---

## 8. Current Implementation State

### ✅ Completed

- FastAPI backend with `/api/prepare`, `/api/log`, `/api/queue/next`
- Vite PWA with 5-tab review flow
- NVIDIA NIM caption generation with APG rule validation
- Demo mode (no credentials required)
- Local fixture content sourcing (`local_folder.py`)
- Firebase auth + Firestore queue (legacy; still functional for demo)
- Google Drive content sourcing (live mode)
- Google Sheets tracker + Docs daily report logging
- Supabase client + asset repository (`supabase_assets.py`)
- Supabase-backed queue + job store (`supabase_queue.py`, `supabase_job_store.py`)
- Supabase auth (`supabase_auth.py`)
- Supabase tracking (`supabase_tracking.py`)
- `ingest.py` CLI for Windows folder → Supabase import
- `folder_parser.py` for raw folder name parsing
- 18 test files with pytest coverage
- Installable PWA (manifest + service worker)

### 🔄 In Progress / Partial

- Supabase asset migration: adapters exist but old Firebase/local paths still parallel
- Full ingest pipeline: `ingest.py` CLI exists; needs real-world validation against `APR LISTING/`
- Operator admin UI: not yet built

### ❌ Not Started

- Admin asset management UI (gallery reorder, replace image, run import)
- Production credential-verified deployment
- CI/CD pipeline

---

## 9. Implementation Roadmap

### Phase 1: Supabase-First Validation (current → 1 week)
- [ ] Run `ingest.py --dry-run` against full `APR LISTING/`; review parse confidence report
- [ ] Run full ingest; verify all `properties` rows created with correct category/transaction_type
- [ ] Verify `property_assets` + `property_asset_relations` rows for 10+ sample properties
- [ ] Confirm posting-desk reads from Supabase (not local folder) in live mode

### Phase 2: Deprecate Legacy Paths (1–2 weeks)
- [ ] Set `CONTENT_SOURCE=supabase` as default; keep `local` fallback 48-hour rollback
- [ ] Remove Firebase auth dependency from live mode (Supabase Auth replaces it)
- [ ] Archive Firebase config files (`firebase.json`, `.firebaserc`, `docs/FIREBASE_MCP_SETUP.md`)
- [ ] Remove `FirebaseTokenVerifier` + `FirestorePropertyQueue` from production code path

### Phase 3: Admin Asset UI (2–3 weeks)
- [ ] Build `/admin/assets` page in posting-desk: table of all assets per property
- [ ] Drag-to-reorder gallery (updates `display_order`)
- [ ] "Replace image" flow: upload new → new asset UUID → update relations
- [ ] "Run import" button (server-side script invocation)

### Phase 4: Polish & Production Readiness (1–2 weeks)
- [ ] Full test suite passes: `pytest -q` → green
- [ ] Frontend build: `npm run build` → clean
- [ ] LSP diagnostics: 0 errors on changed files
- [ ] Vercel deployment with serverless API functions
- [ ] CI pipeline (lint + test + build on PR)

---

## 10. Key Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| One shared Supabase project with `apg-website` | Eliminates duplicate uploads, single source of truth, one admin console | 2026-06 |
| Facebook posting remains manual | Product direction; no Graph API automation without explicit request change | Ongoing |
| Supabase Auth replaces Firebase Auth | `profiles.role` check is simpler; no Firebase SDK in browser | 2026-06 |
| `apg-public` / `apg-private` two-bucket model | Explicit access boundary: public images vs private documents | 2026-06 |
| Windows `APR LISTING/` is import source only | Never read at runtime; Supabase is the only runtime asset backend | 2026-06 |
| `supabase_auth.py` uses `profiles.role='staff'` | Desk operators are `staff` role; satisfies `is_staff()` RLS | 2026-06 |

---

## 11. Known Issues & Tech Debt

| Issue | Severity | Notes |
|-------|----------|-------|
| Firebase + Supabase adapters run in parallel | Medium | Both functional; should consolidate to Supabase-only path |
| `AGENTS.md` claims no `.git` but `.git` exists | Low | Stale documentation; `.git` IS present (hidden) |
| `apg_automation/static/` may drift from `src/` | Low | Update both surfaces only when request needs both |
| No CI/CD pipeline | Medium | Manual deploy; no automated test gate |
| No operator admin UI | Medium | Asset management requires Supabase dashboard or raw SQL |
| `posted_log` table referenced but may not exist in current schema | Low | Verify `supabase_tracking.py` write target |

---

## 12. Relationships to apg-website

```
apg-website (public site + admin)
  │
  │  Shared Supabase project (ldtavdybcgwjgticrymz)
  │
  ├── Shared read: public.categories, transaction_types, properties,
  │                property_assets, property_asset_relations
  │
  └── apg-website writes: none (read-only consumer)
        apg-posting-desk writes: posting_desk.* tables
                                   ingestion to public.property_assets
                                   property_asset_relations
```

- `apg-website` serves property listings to the public.
- `apg-posting-desk` owns the posting workflow: ingest, prepare, publish, log.
- Both read from the same `public.properties`, `public.property_assets`, `public.property_asset_relations` tables.
- Image uploads happen once (via ingest pipeline), consumed by both systems with no duplication.
