# APG Posting Desk — Manual Testing Guide

This document covers manual test cases for the APG Posting Desk system. It
covers demo mode (no external credentials), live local mode (real AI + Google),
and Supabase/serverless mode (full auth, queue, tracking). Credentials needed
to access the system in each mode are listed in the **Credentials** section.

---

## Table of Contents

1. [System Modes](#1-system-modes)
2. [Credentials](#2-credentials)
3. [Prerequisites & Startup](#3-prerequisites--startup)
4. [Login & Authentication](#4-login--authentication)
5. [Session API](#5-session-api)
6. [Role-Based Access Control](#6-role-based-access-control)
7. [Property Details Tab](#7-property-details-tab)
8. [Property Photos Tab](#8-property-photos-tab)
9. [Caption Drafting Tab](#9-caption-drafting-tab)
10. [Facebook Posting (Publish) Tab](#10-facebook-posting-publish-tab)
11. [Post Log Tab](#11-post-log-tab)
12. [Job List & Metrics](#12-job-list--metrics)
13. [Queue Processing](#13-queue-processing)
14. [Caption Rules Validation](#14-caption-rules-validation)
15. [Direct API Endpoint Tests](#15-direct-api-endpoint-tests)
16. [Asset Serving & Downloads](#16-asset-serving--downloads)
17. [Theme & PWA Features](#17-theme--pwa-features)
18. [Error Handling & Edge Cases](#18-error-handling--edge-cases)
19. [Live Mode Integration Tests](#19-live-mode-integration-tests)
20. [Automated Test Verification](#20-automated-test-verification)

---

## 1. System Modes

| Mode | Command | Auth | AI | Tracking | Asset Source |
|------|---------|------|----|----------|--------------|
| **Demo** | `npm run dev` | Demo login (in-memory) | DemoCaptionGenerator (no NIM) | ConsoleTracker (stdout only) | Local fixture folder |
| **Demo API only** | `npm run dev:api` | Same as demo | Same as demo | Same as demo | Local fixture folder |
| **Live local** | `npm run dev:live` | Demo login | Real NVIDIA NIM | ConsoleTracker | Local fixture folder |
| **Supabase / Serverless** | `vercel deploy` / Vercel function | Supabase Auth (JWT bearer) | Real NVIDIA NIM | Supabase tracker (sheets/docs) | Supabase Storage |

- **Demo mode** is the default and requires **zero external credentials**. Use it
  for all UI and basic API testing.
- **Live local mode** requires `NVIDIA_API_KEY` for real caption generation.
- **Supabase mode** is the production path; it requires Supabase, NVIDIA, and
  Google credentials and runs behind Supabase Auth JWT verification.

### URLs

| Surface | URL |
|---------|-----|
| Vite PWA (dev) | `http://localhost:5173` |
| FastAPI backend (dev) | `http://localhost:8001` |
| Vite preview (built) | `http://localhost:4173` |
| Vercel production frontend | `https://apg-posting-desk.vercel.app` |
| Firebase hosting (legacy) | `https://apg-posting-desk-deign-2026.web.app/` |
| APG Listing Drive | `https://drive.google.com/drive/folders/1GXeGULYswb7jXcMGCCRm2RQ_h0EKsDll` |

---

## 2. Credentials

### 2.1 Demo Login Accounts (no setup required)

These are seeded in-memory by the FastAPI demo backend and in the Playwright
E2E tests. They work in **demo** and **live local** mode.

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@apg.local` | `admin@123` |
| Operator (user) | `operator@apg.local` | `oper@123` |

> In Supabase mode, the same two accounts are seeded into Supabase Auth on
> startup via `seed_accounts()` (admin role = `admin`, operator role = `staff`).

### 2.2 Environment Variables (`.env`)

Copy `.env.example` to `.env` and fill in real values for live/Supabase mode.

#### AI Caption Generation

| Variable | Purpose | Demo Value | Live Value |
|----------|---------|------------|------------|
| `NVIDIA_API_KEY` | NVIDIA NIM API key (required for real captions) | _(not used in demo)_ | Your NVIDIA NIM key |
| `AI_PROVIDER` | AI provider | `nvidia-nim` | `nvidia-nim` / `openai` / `anthropic` |
| `AI_MODEL` | Model name | `stepfun-ai/step-3.7-flash` | same |
| `OPENAI_API_KEY` | OpenAI key (if provider=openai) | — | Your OpenAI key |
| `ANTHROPIC_API_KEY` | Anthropic key (if provider=claude) | — | Your Anthropic key |

#### Google Workspace (Drive / Sheets / Docs)

| Variable | Purpose |
|----------|---------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google service account JSON |
| `POSTING_TRACKER_SHEET_ID` | Google Sheets ID for posting tracker |
| `DAILY_REPORT_DOC_ID` | Google Docs ID for daily report |
| `POSTED_BY` | Label written into tracker (default `APG Automation`) |
| `TIMEZONE` | Timezone for timestamps (default `Asia/Manila`) |

Defaults already in `config.yaml`:

| Key | Value |
|-----|-------|
| `google_drive.listings_folder_id` | `1GXeGULYswb7jXcMGCCRm2RQ_h0EKsDll` |
| `tracking.posting_tracker_sheet_id` | `1xzzuq8KHbzrRIGMyIo0AQVgq0LQklDkW8-S9Y__7RvM` |
| `tracking.daily_report_doc_id` | `1mctXkKFhZLCEXQtnzO4dmHhUSGOKFdFliF_qL17U68o` |

#### Supabase (shared project with apg-website)

| Variable | Purpose | Notes |
|----------|---------|-------|
| `SUPABASE_URL` | Supabase project URL | Project ref: `ldtavdybcgwjgticrymz` |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key | **Server only — never expose to browser** |
| `SUPABASE_ANON_KEY` | Anon public key | Safe for browser |

#### Frontend (Vite env vars, prefix `VITE_`)

| Variable | Purpose |
|----------|---------|
| `VITE_SUPABASE_URL` | Supabase URL for browser client |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key for browser client |
| `VITE_APG_GOOGLE_DOMAIN` | Optional hosted-domain restriction (leave blank for normal Google accounts) |

#### Firebase (DEPRECATED — retained only for legacy demo path)

| Variable | Value |
|----------|-------|
| `VITE_FIREBASE_API_KEY` | `AIzaSyAPHFreROsT2nsIPrCZxfEepesGejG6EIY` |
| `VITE_FIREBASE_AUTH_DOMAIN` | `apg-posting-desk-deign-2026.firebaseapp.com` |
| `VITE_FIREBASE_PROJECT_ID` | `apg-posting-desk-deign-2026` |
| `VITE_FIREBASE_APP_ID` | `1:676310407748:web:9ab12f1c0ebcab17fbba11` |

#### Storage Buckets (from `config.yaml`)

| Key | Value |
|-----|-------|
| `storage.bucket_private` | `apg-private` |
| `storage.bucket_public` | `apg-public` |
| `storage.bucket_listings` | `apr-listing` |
| `storage.signed_url_ttl_seconds` | `3600` |

### 2.3 Admin / Backend Credentials

| Credential | How to obtain |
|------------|---------------|
| Google service account JSON | `gcloud auth application-default login` or set `GOOGLE_APPLICATION_CREDENTIALS` to a JSON path |
| Supabase CLI auth | `supabase link --project-ref ldtavdybcgwjgticrymz` |

---

## 3. Prerequisites & Startup

### 3.1 Install Dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
npm install
copy .env.example .env
```

### 3.2 Start the App (Demo Mode)

```powershell
npm run dev
```

Verify:
- [ ] FastAPI backend prints startup messages (no errors)
- [ ] `NVIDIA NIM probe skipped` or `NVIDIA NIM ready` appears (depends on env)
- [ ] `Seeded job for local fixture: Novaliches, 440 Bagbag` appears
- [ ] Vite dev server starts on `http://localhost:5173`
- [ ] Opening `http://localhost:5173` shows the login screen

### 3.3 Start Backend Only

```powershell
npm run dev:api
```

- [ ] FastAPI starts on `http://localhost:8001`
- [ ] `GET http://localhost:8001/` returns the static `index.html`

### 3.4 Start Frontend Only

```powershell
npm run dev:web
```

- [ ] Vite starts on `http://localhost:5173`
- [ ] API calls to `/api/*` and `/prepared/*` proxy to `http://127.0.0.1:8001`

### 3.5 Local Test Fixture

The folder `Novaliches, 440 Bagbag/` contains:

| File | Type |
|------|------|
| `2.png`, `3.png`, `4.png`, `5.png` | Property images |
| `caption reference.jpeg` | Image |
| `Untitled document.docx` | Caption details document (DOCX) |

This fixture satisfies the minimum 3 images + 1 document requirement.

---

## 4. Login & Authentication

### 4.1 Login Screen Rendering

**Steps:** Open `http://localhost:5173` (demo mode).

- [ ] Login screen is visible (`#loginScreen` not hidden)
- [ ] Email field (`#loginEmail`) is visible and accepts email type
- [ ] Password field (`#loginPassword`) is visible and is password type
- [ ] Sign in button (`#loginSubmit`) is visible
- [ ] Theme toggle button (`#loginThemeToggle`) is visible
- [ ] App content (`#appContent`) is hidden

### 4.2 Invalid Login

**Steps:** Enter `wrong@apg.local` / `wrong` and click Sign in.

- [ ] `#loginError` becomes visible
- [ ] Error text contains "invalid" (case-insensitive)
- [ ] Login screen remains visible
- [ ] App content remains hidden

### 4.3 Admin Login

**Steps:** Enter `admin@apg.local` / `admin@123` and click Sign in.

- [ ] Login screen hides (`#loginScreen` hidden = true)
- [ ] App content is visible (`#appContent`)
- [ ] `#sessionTitle` contains "Signed in"
- [ ] Role badge (`#roleBadge`) shows admin role
- [ ] User label shows "Admin"
- [ ] Admin-only buttons are visible (`#newJobBtn`, `#processNext`)

### 4.4 Operator Login

**Steps:** Enter `operator@apg.local` / `oper@123` and click Sign in.

- [ ] Login screen hides
- [ ] App content is visible
- [ ] Role badge shows user/operator role
- [ ] User label shows "Operator"
- [ ] Admin-only buttons are hidden (`#newJobBtn`, `#processNext`)

### 4.5 Sign Out

**Steps:** After logging in as admin, click `#signOutButton`.

- [ ] Login screen becomes visible again
- [ ] App content is hidden
- [ ] Can log back in afterwards

### 4.6 Supabase Auth (Live / Serverless Mode)

**Prerequisite:** `.env` has `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`,
`SUPABASE_ANON_KEY`, and frontend has `VITE_SUPABASE_URL` /
`VITE_SUPABASE_ANON_KEY`.

- [ ] Login with Supabase Auth sends a JWT bearer token to the backend
- [ ] `Authorization: Bearer <token>` header is present on API requests
- [ ] `GET /api/session` returns the verified Supabase user (uid, email, role)
- [ ] Invalid/expired token returns HTTP 401 "Missing access token" or "Invalid access token"
- [ ] `profiles` table role (`admin` / `staff`) is respected for access control

---

## 5. Session API

### 5.1 Get Session (Demo)

**Request:**
```
GET /api/session
Header: X-Demo-Role: admin
```

- [ ] Returns `{ "user": { "uid": "demo", "email": "demo@apg.local", "role": "admin", "display_name": "Demo Admin" } }`

### 5.2 Get Session (Operator Role)

**Request:**
```
GET /api/session
Header: X-Demo-Role: user
```

- [ ] Returns user with `role: "user"` and `display_name: "Demo User"`

### 5.3 Get Session (No Header)

**Request:**
```
GET /api/session
```

- [ ] Defaults to `role: "user"`, `display_name: "Demo User"`

---

## 6. Role-Based Access Control

### 6.1 Admin-Only: Create User

**Request (demo):**
```
POST /api/admin/users
Header: X-Demo-Role: admin
Body: { "email": "new@apg.local", "password": "pass", "role": "user" }
```

- [ ] Returns 201 with `{ "uid": "seed-admin", "email": "new@apg.local", "role": "user", "status": "demo-created" }`

### 6.2 Non-Admin Cannot Create User

**Request:**
```
POST /api/admin/users
Header: X-Demo-Role: user
Body: { "email": "x@apg.local", "password": "x", "role": "user" }
```

- [ ] Returns HTTP 403 "Insufficient role"

### 6.3 Admin-Only: Seed Accounts

**Request:**
```
POST /api/admin/seed
Header: X-Demo-Role: admin
```

- [ ] Returns `{ "seeded": 2, "accounts": ["admin@apg.local", "operator@apg.local"] }`

### 6.4 Non-Admin Cannot Seed

**Request:**
```
POST /api/admin/seed
Header: X-Demo-Role: user
```

- [ ] Returns HTTP 403

### 6.5 Admin-Only: Create Job

**Request:**
```
POST /api/jobs
Header: X-Demo-Role: admin
Body: {
  "property_name": "Test Property",
  "assigned_by": "Ma'am Jean",
  "operator": "Operator 1",
  "due_date": "2026-07-17",
  "drive_url": "https://drive.google.com/..."
}
```

- [ ] Returns 201 with a job ID like `APG-0717-001`
- [ ] Job appears in `GET /api/jobs` list

### 6.6 Non-Admin Cannot Create Job

- [ ] `POST /api/jobs` with `X-Demo-Role: user` returns HTTP 403

### 6.7 Admin-Only: Queue Next

- [ ] `POST /api/queue/next` with `X-Demo-Role: admin` works (returns property or 404 if no queue)
- [ ] `POST /api/queue/next` with `X-Demo-Role: user` returns HTTP 403

### 6.8 UI Role Visibility

- [ ] Admin sees `#newJobBtn` (New intake) and `#processNext` (Process next property)
- [ ] Operator has `#newJobBtn` and `#processNext` hidden
- [ ] Both roles can see the property list and workflow tabs

---

## 7. Property Details Tab

### 7.1 Seeded Job Appears

**Steps:** Start in demo mode. Login as admin.

- [ ] The seeded job "Novaliches, 440 Bagbag" appears in the property list (`#jobList`)
- [ ] Clicking the job selects it and populates the details form
- [ ] `#propertyName` shows "Novaliches, 440 Bagbag"
- [ ] `#assignedBy` shows "Ma'am Jean"
- [ ] `#operatorName` shows "Unassigned"
- [ ] `#driveUrl` shows the resolved local folder path

### 7.2 Validate Property Files

**Steps:** Select the seeded job, click "Validate property files" (`#validateAssetsBtn`).

- [ ] Validation steps appear in `#validationSteps`
- [ ] Status shows the property has sufficient images and a caption document
- [ ] A toast message confirms validation result

### 7.3 Run Property Check (Prepare)

**Steps:** Click "Run property check" (`#simulatePipelineBtn`).

- [ ] `POST /api/jobs/{job_id}/prepare` is called
- [ ] Caption is generated (demo text in demo mode)
- [ ] Images are populated in the photos tab
- [ ] Metrics update: `#metricProperty`, `#metricAssets`, `#metricDoc`
- [ ] Toast shows "Property check complete."
- [ ] Activity log shows the preparation step

### 7.4 New Intake (Admin Only)

**Steps:** Login as admin, click "New intake" (`#newJobBtn`).

- [ ] A new job appears at the top of the list
- [ ] Job ID follows `APG-0717-00X` pattern
- [ ] Status is "missing-assets" initially
- [ ] Fields are editable: property name, assigned by, operator, due date, drive URL

### 7.5 Continue to Photos

**Steps:** After running property check, click "Continue to photos" (`#nextToPhotos`).

- [ ] Photos tab becomes active (`#panel-photos` visible)
- [ ] Tab `#tab-photos` is enabled and `aria-selected="true"`
- [ ] Details tab is no longer active

---

## 8. Property Photos Tab

### 8.1 Image Thumbnails

**Steps:** After preparing a job, navigate to the Photos tab.

- [ ] Thumbnails render in `#thumbs`
- [ ] Image counter badge (`#imageCounterBadge`) shows count (e.g. "3 selected")
- [ ] Each thumbnail has a name and a selection state

### 8.2 Caption Source File

- [ ] `#sourceDocName` shows the caption document name (e.g. "Untitled document.docx")
- [ ] `#captionSourceOutput` shows extracted caption details text

### 8.3 Asset Summary

- [ ] `#assetSummary` shows a summary of the asset package (image count, document name)

### 8.4 Download All Photos (ZIP)

**Steps:** Click "Download all photos" (`#zipDownload`).

- [ ] Link is not disabled (`aria-disabled != "true"`)
- [ ] A ZIP file downloads (from `/api/preparations/{id}/images.zip` in demo/local mode)
- [ ] ZIP contains the selected images
- [ ] Activity log records "Photo package downloaded"

### 8.5 Navigate Back and Forth

- [ ] "Back" (`#backToDetails`) returns to Property details tab
- [ ] "Continue to caption" (`#nextToCaption`) advances to Caption tab

---

## 9. Caption Drafting Tab

### 9.1 Caption Display

**Steps:** After preparing a job, navigate to the Caption tab.

- [ ] `#captionDetails` textarea shows the extracted caption details
- [ ] `#finalCaption` textarea shows the generated caption
- [ ] `#captionVariants` shows caption options
- [ ] Caption guidance copy is visible: "No emojis", "Caption source file"
- [ ] "Generate Caption" button (`#generateCaption`) is visible
- [ ] "Check rules" button (`#checkRulesBtn`) is visible

### 9.2 Generate Caption

**Steps:** Click "Generate Caption" (`#generateCaption`).

- [ ] `POST /api/jobs/{job_id}/captions` is called
- [ ] Caption variants are returned and displayed
- [ ] Activity log shows "Caption variants generated with APG rules."

### 9.3 Check Rules

**Steps:** Click "Check rules" (`#checkRulesBtn`).

- [ ] `#captionRuleResult` shows validation result
- [ ] If caption is compliant, shows pass/success
- [ ] If caption has violations, lists them (emojis, forbidden phrases, length)

### 9.4 Caption Source Output

- [ ] `#captionSourceOutput` (on Photos tab) shows the raw extracted document text
- [ ] Text matches the content of `Untitled document.docx`

### 9.5 Navigate to Publish

- [ ] "Continue to publish" (`#nextToPublish`) advances to Publish tab
- [ ] "Back" (`#backToPhotos`) returns to Photos tab

---

## 10. Facebook Posting (Publish) Tab

### 10.1 Workflow Progress Guide

**Steps:** Navigate to the Publish tab.

- [ ] "Workflow Progress Guide" heading is visible
- [ ] Step 1: "Download photos" is listed
- [ ] Step 2: "Copy the caption" is listed
- [ ] Step 3: "Post to Facebook" is listed
- [ ] Step 4: "Paste the live post URL" is listed
- [ ] Step 5: "Log the post" is listed

### 10.2 Checklist Items

- [ ] Checkbox "At least 3 photos are selected" (`#checkPhotosSelected`) is present
- [ ] Checkbox "Caption is approved" (`#checkCaptionApproved`) is present
- [ ] Checkbox "Property was posted manually on Facebook" (`#checkPostedToFacebook`) is present

### 10.3 Copy Caption

**Steps:** Click "Copy caption" (`#copyCaptionBtn`).

- [ ] Caption text is copied to clipboard
- [ ] Workflow guide updates to show step 2 complete

### 10.4 Copy Posting Checklist

- [ ] "Copy posting checklist" (`#copyChecklistBtn`) copies a checklist to clipboard

### 10.5 Open Facebook

**Steps:** Click "Open Facebook" (`#openFacebookBtn`).

- [ ] Opens `https://www.facebook.com/` in a new tab
- [ ] Workflow guide updates

### 10.6 Facebook URL Input (Gated)

- [ ] Facebook URL input group (`#facebookUrlGroup`) is hidden until checklist items are checked
- [ ] After checking relevant checkboxes, the URL field appears
- [ ] "Mark as posted" button (`#logPostButton`) is disabled until a valid URL is entered

### 10.7 Mark as Posted

**Steps:** Enter a Facebook URL (e.g. `https://facebook.com/posts/123`), check the checklist, click "Mark as posted".

- [ ] `POST /api/jobs/{job_id}/mark-posted` is called
- [ ] Job status updates to "posted"
- [ ] Tracker is called (ConsoleTracker prints to stdout in demo mode)
- [ ] In Supabase mode: tracker sheet row and daily report doc entry are appended
- [ ] `#facebookLink` retains the URL
- [ ] Activity log shows the post was logged

### 10.8 Invalid Facebook URL

**Steps:** Enter `https://example.com/post` and try to mark posted.

- [ ] Returns HTTP 400 with "Facebook URL must start with https://facebook.com/"
- [ ] Toast shows the error message

### 10.9 Navigate to Log

- [ ] "Continue to log" (`#nextToLog`) advances to Post log tab
- [ ] "Back" (`#backToCaption`) returns to Caption tab

---

## 11. Post Log Tab

### 11.1 Tracker Preview

**Steps:** After marking a job as posted, navigate to the Log tab.

- [ ] `#trackerPreview` shows a formatted tracker row (date, property, URL, status, posted_by)
- [ ] `#dailyReportPreview` shows a formatted end-of-day note

### 11.2 Prepare Updates

- [ ] "Prepare updates" button (`#prepareTrackerBtn`) generates tracker/daily report text

### 11.3 Copy Tracker Row

- [ ] "Copy tracker row" (`#copyTrackerRowBtn`) copies the tracker row to clipboard

### 11.4 Copy Daily Report

- [ ] "Copy daily report" (`#copyDailyReportBtn`) copies the daily report note to clipboard

### 11.5 Tracker Status

- [ ] `#trackerStatus` shows whether tracking was logged or pending

### 11.6 Finish Workflow

**Steps:** Click "Finish and start new" (`#finishWorkflow`).

- [ ] Workflow resets
- [ ] A new (empty) job may be created or selection cleared
- [ ] Activity log can be cleared

### 11.7 Recent Actions Log

- [ ] `#activityLog` shows timestamped entries for each action taken
- [ ] "Clear log" (`#clearLogBtn`) clears the activity log

---

## 12. Job List & Metrics

### 12.1 Dashboard Metrics

**Steps:** After login, observe the metrics row.

- [ ] "Assigned today" (`#assignedCount`) count is visible
- [ ] "Waiting approval" (`#approvalCount`) count is visible
- [ ] "Ready to post" (`#readyCount`) count is visible
- [ ] "Posted today" (`#postedCount`) count is visible
- [ ] Counts update when jobs change status

### 12.2 Sidebar Navigation Filters

- [ ] Clicking "Assigned today" filters the job list to assigned jobs
- [ ] Clicking "Waiting approval" filters to waiting_approval
- [ ] Clicking "Ready to post" filters to ready_to_post
- [ ] Clicking "Posted today" filters to posted

### 12.3 Property List

- [ ] `#jobList` shows all jobs as cards/rows
- [ ] Each job shows: name, ID, status badge, tracker status
- [ ] Clicking a job selects it and loads it into the workflow

### 12.4 Metrics Cards

- [ ] `#metricProperty` shows the selected property name
- [ ] `#metricAgent` shows "Assigned by <name>"
- [ ] `#metricAssets` shows photo count
- [ ] `#metricDoc` shows "Caption file <name>"
- [ ] `#metricStatus` shows current post status
- [ ] `#metricTracker` shows tracker status

---

## 13. Queue Processing

### 13.1 Process Next Property (Admin Only)

**Steps:** Login as admin, click "Process next property" (`#processNext`).

- [ ] `POST /api/queue/next` is called
- [ ] If a pending property exists, it loads into the property name field and prepares
- [ ] If no queue configured (demo mode): returns 404 "Queue is not configured" or "No pending properties"
- [ ] Toast shows the result

### 13.2 Queue Not Configured (Demo Mode)

- [ ] In demo mode (no Supabase), `/api/queue/next` returns 404 "Queue is not configured"
- [ ] This is expected behavior — demo uses in-memory seed jobs, not a queue

### 13.3 Live Queue (Supabase Mode)

**Prerequisite:** Supabase `property_queue` / `posting_jobs` table has pending entries.

- [ ] `POST /api/queue/next` (admin) claims the next pending property
- [ ] The claimed property's status changes from `pending` to `assigned`/`in_progress`
- [ ] The operator_uid is set to the admin's UID
- [ ] Returns `{ "id": "...", "property_name": "..." }`
- [ ] If no pending properties, returns 404 "No pending properties"

---

## 14. Caption Rules Validation

The system enforces these caption rules (in `caption_generator.py`):

| Rule | Detail |
|------|--------|
| No emojis | Any Unicode emoji character is a violation |
| No "least term" | Forbidden phrase (case-insensitive) |
| No "negotiables" | Forbidden phrase (case-insensitive) |
| No "negotioables" | Forbidden misspelling (case-insensitive) |
| Max length | 2000 characters |

### 14.1 Valid Caption

**Steps:** Generate a caption in demo mode. The demo generator sanitizes "least term" to "lease terms" and "negotiables" to "terms".

- [ ] Caption passes validation (no violations)
- [ ] `requires_manual_review` is `false`

### 14.2 Emoji Detection

**Manual test:** If using live NIM, edit the caption to include an emoji (e.g. a house emoji) and check rules.

- [ ] `validate_caption` returns violation "Contains emojis"

### 14.3 Forbidden Phrase Detection

- [ ] Caption containing "least term" returns violation "Contains forbidden phrase: 'least term'"
- [ ] Caption containing "negotiables" returns violation "Contains forbidden phrase: 'negotiables'"
- [ ] Caption containing "negotioables" returns violation "Contains forbidden phrase: 'negotioables'"

### 14.4 Max Length

- [ ] Caption exceeding 2000 characters returns violation "Exceeds max length: 2000"

### 14.5 Retry Behavior

- [ ] If the AI returns a violating caption, the generator retries up to `max_retries` (default 3)
- [ ] If all retries fail, returns `requires_manual_review: true` with accumulated violations

---

## 15. Direct API Endpoint Tests

All endpoints below can be tested with `curl` or a REST client. In demo mode,
add header `X-Demo-Role: admin` or `X-Demo-Role: user` to simulate roles.

### 15.1 Session

```powershell
# Demo session
curl http://localhost:8001/api/session -H "X-Demo-Role: admin"

# Login (demo)
curl -X POST http://localhost:8001/api/login -H "Content-Type: application/json" -d "{\"email\":\"admin@apg.local\",\"password\":\"admin@123\"}"

# Logout
curl -X POST http://localhost:8001/api/logout
```

- [ ] Session returns user dict with correct role
- [ ] Login returns `{ "email", "role", "display_name", "status": "demo" }`
- [ ] Logout returns `{ "status": "logged_out" }`

### 15.2 Jobs

```powershell
# List jobs
curl http://localhost:8001/api/jobs -H "X-Demo-Role: admin"

# Create job
curl -X POST http://localhost:8001/api/jobs -H "X-Demo-Role: admin" -H "Content-Type: application/json" -d "{\"property_name\":\"Test Prop\",\"assigned_by\":\"Jean\",\"operator\":\"Op1\",\"due_date\":\"2026-07-17\",\"drive_url\":\"\"}"
```

- [ ] List returns `{ "jobs": [...], "counts": {...} }`
- [ ] Create returns job object with generated ID

### 15.3 Prepare

```powershell
# Prepare via legacy endpoint
curl -X POST http://localhost:8001/api/prepare -H "X-Demo-Role: admin" -H "Content-Type: application/json" -d "{\"property_name\":\"Novaliches, 440 Bagbag\"}"

# Prepare via job endpoint (use a real job ID from the list)
curl -X POST http://localhost:8001/api/jobs/APG-0717-001/prepare -H "X-Demo-Role: admin"
```

- [ ] Returns preparation with `preparation_id`, `caption`, `images`, `download_zip_url`
- [ ] Images array contains entries with `name` and `url`
- [ ] `caption_details` contains the extracted document text

### 15.4 Log Post

```powershell
curl -X POST http://localhost:8001/api/log -H "X-Demo-Role: admin" -H "Content-Type: application/json" -d "{\"property_name\":\"Novaliches, 440 Bagbag\",\"facebook_url\":\"https://facebook.com/posts/123\"}"
```

- [ ] Returns `{ "status": "logged" }`
- [ ] ConsoleTracker prints `LOGGED ...` to backend stdout (demo mode)

### 15.5 Mark Posted

```powershell
curl -X POST http://localhost:8001/api/jobs/APG-0717-001/mark-posted -H "X-Demo-Role: admin" -H "Content-Type: application/json" -d "{\"facebook_url\":\"https://facebook.com/posts/456\"}"
```

- [ ] Returns the job with `status: "posted"` and `facebook_url` set

### 15.6 Validate Job

```powershell
curl -X POST http://localhost:8001/api/jobs/APG-0717-001/validate -H "X-Demo-Role: admin"
```

- [ ] Returns `{ "ok": true/false, "data": { "property_name", "errors" } }`

### 15.7 Generate Captions

```powershell
curl -X POST http://localhost:8001/api/jobs/APG-0717-001/captions -H "X-Demo-Role: admin"
```

- [ ] Returns `{ "variants": ["..."] }` with at least one caption variant

### 15.8 Job Activity

```powershell
curl http://localhost:8001/api/jobs/APG-0717-001/activity -H "X-Demo-Role: admin"
```

- [ ] Returns `{ "activity": [ { "at": "HH:MM", "text": "..." }, ... ] }`

### 15.9 Offerings (Supabase Mode Only)

```powershell
curl http://localhost:8001/api/offerings -H "Authorization: Bearer <token>"
```

- [ ] In demo mode: returns `{ "offerings": [] }` (no asset service)
- [ ] In Supabase mode: returns offerings from the `offerings` table

### 15.10 Asset Signed URL (Supabase Mode Only)

```powershell
curl -X POST http://localhost:8001/api/assets/signed-url -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d "{\"asset_id\":\"<uuid>\",\"expires_in\":3600}"
```

- [ ] In demo mode: returns 503 "Asset service not configured"
- [ ] In Supabase mode: returns `{ "url": "..." }` (signed or public URL)

---

## 16. Asset Serving & Downloads

### 16.1 Static Index

```powershell
curl http://localhost:8001/
```

- [ ] Returns `index.html` from `apg_automation/static/`

### 16.2 Static Assets

```powershell
curl http://localhost:8001/styles.css
curl http://localhost:8001/app.js
curl http://localhost:8001/manifest.webmanifest
curl http://localhost:8001/service-worker.js
curl http://localhost:8001/icon.svg
```

- [ ] Each returns the file content
- [ ] Requesting an unlisted asset (e.g. `/unknown.js`) returns 404

### 16.3 Prepared Images (Demo/Local Mode)

```powershell
curl http://localhost:8001/prepared/<preparation_id>/<image_name>.png
```

- [ ] Returns the image file
- [ ] The `/prepared` mount serves from `downloads/_public/`

### 16.4 Preparation ZIP

```powershell
curl http://localhost:8001/api/preparations/<preparation_id>/images.zip -o images.zip
```

- [ ] Downloads a ZIP containing the prepared images
- [ ] Non-existent preparation ID returns 404 "Preparation not found"

### 16.5 Job Prepared ZIP (Supabase Mode)

```powershell
curl http://localhost:8001/api/jobs/<job_id>/prepared.zip -H "Authorization: Bearer <token>" -o job-images.zip
```

- [ ] In demo mode: returns 503 "Asset service not configured"
- [ ] In Supabase mode: streams a ZIP of selected images from Storage

---

## 17. Theme & PWA Features

### 17.1 Theme Toggle (Login Screen)

- [ ] Click `#loginThemeToggle` on the login screen
- [ ] Theme switches between light and dark
- [ ] Theme persists in `localStorage` key `apg-theme`

### 17.2 Theme Toggle (App)

- [ ] Click `#themeToggle` in the sidebar
- [ ] `data-theme` attribute on `<html>` changes
- [ ] Theme persists across page reloads

### 17.3 PWA Manifest

- [ ] `GET /manifest.webmanifest` returns a valid Web App Manifest
- [ ] Manifest includes name, icons, display mode
- [ ] Browser offers "Install app" prompt

### 17.4 Service Worker

- [ ] `GET /service-worker.js` returns the service worker script
- [ ] Service worker registers in the browser
- [ ] Offline-capable (cached assets load without network in some browsers)

### 17.5 Mobile / LAN Access

- [ ] From a device on the same network, `http://<LAN-IP>:5173` loads the app
- [ ] Login and workflow are usable on mobile viewport

---

## 18. Error Handling & Edge Cases

### 18.1 Property Not Found

```powershell
curl -X POST http://localhost:8001/api/prepare -H "X-Demo-Role: admin" -H "Content-Type: application/json" -d "{\"property_name\":\"Nonexistent Property\"}"
```

- [ ] Returns 400 with "Property not found"

### 18.2 Insufficient Images

**Setup:** Point `--local-folder` to a folder with fewer than 3 images.

- [ ] `QueueManager.build_queue` returns error "Insufficient images"
- [ ] Prepare endpoint returns 400

### 18.3 Missing Caption Document

**Setup:** Folder with no `.docx`, `.pdf`, or `.txt` files.

- [ ] Queue returns error "Missing caption document"
- [ ] Prepare returns 400

### 18.4 Empty Caption Document

**Setup:** A `.docx`/`.txt` with no text content.

- [ ] `ContentExtractor.extract_document_text` returns empty string
- [ ] `ContentExtractor.extract` raises "Caption document is empty"

### 18.5 Unsupported Document Type

**Setup:** Folder with only `.xlsx` (not `.docx`/`.pdf`/`.txt`).

- [ ] `extract_document_text` raises "Unsupported caption document type: .xlsx"

### 18.6 NIM Unreachable (Live Mode)

- [ ] If `NVIDIA_API_KEY` is missing: `NvidiaNimClient.__init__` raises `ValueError`
- [ ] If NIM is down: `probe()` returns False, startup prints "NVIDIA NIM unreachable"
- [ ] Caption generation calls fail gracefully

### 18.7 Missing Auth Token (Supabase Mode)

```powershell
curl http://localhost:8001/api/session
```

- [ ] Without `Authorization: Bearer <token>`: returns 401 "Missing access token"
- [ ] With invalid token: returns 401 "Invalid access token"

### 18.8 Non-Existent Job

```powershell
curl http://localhost:8001/api/jobs/nonexistent-id/activity -H "X-Demo-Role: admin"
```

- [ ] Returns 404 "Job not found"

### 18.9 Dry-Run Queue Validation

```powershell
python -m apg_automation.main --dry-run --local-folder "C:/Users/Deign/Downloads/APG Prototype System for Automated Posting/Novaliches, 440 Bagbag"
```

- [ ] Validates config and property folder without generating captions or logging
- [ ] Exits 0 on success, 2 on config validation error

---

## 19. Live Mode Integration Tests

### 19.1 Live Local Mode (`npm run dev:live`)

**Prerequisite:** `.env` has `NVIDIA_API_KEY`.

- [ ] Startup prints "NVIDIA NIM ready: stepfun-ai/step-3.7-flash" (if reachable)
- [ ] Caption generation uses real NIM API (not DemoCaptionGenerator)
- [ ] Generated caption is professional, no emojis, no forbidden phrases
- [ ] Tracker is still ConsoleTracker (prints to stdout)

### 19.2 Supabase Auth Seed

**Prerequisite:** Supabase mode, admin login.

- [ ] On startup, `seed_accounts()` creates `admin@apg.local` (admin) and `operator@apg.local` (staff)
- [ ] If accounts already exist, seed is skipped with a message
- [ ] Both accounts can log in via Supabase Auth

### 19.3 Supabase Tracker (Google Sheets/Docs)

**Prerequisite:** `GOOGLE_APPLICATION_CREDENTIALS` set, sheet/doc IDs configured.

- [ ] After marking a job posted, a row is appended to the posting tracker sheet
- [ ] Row contains: date, property name, Facebook URL, "Posted", posted_by
- [ ] A daily report entry is appended to the daily report doc
- [ ] Entry format: "- {property} - Posted at {HH:MM}\n  Link: {url}"

### 19.4 Supabase Storage Assets

- [ ] `find_property_folder` queries Supabase `assets` and `property_asset_relations` tables
- [ ] Images are served via signed URLs from `apg-private` or public URLs from `apg-public`
- [ ] `get_signed_url(asset_id)` returns a time-limited URL (TTL from config)

### 19.5 Supabase Job Store

- [ ] `GET /api/jobs` reads from `posting_jobs` table
- [ ] `POST /api/jobs` inserts into `posting_jobs`
- [ ] `mark_posted` updates the job row and inserts into `posted_log`

### 19.6 Serverless (Vercel) Deployment

- [ ] `build_live_app()` in `serverless.py` wires all Supabase adapters
- [ ] On startup error, returns 500 with traceback (not generic FUNCTION_INVOCATION_FAILED)
- [ ] Download root is `/tmp/apg-prepared` (Vercel writable filesystem)
- [ ] Vercel frontend at `https://apg-posting-desk.vercel.app` loads the PWA

---

## 20. Automated Test Verification

Run these before and after manual testing to catch regressions.

### 20.1 Python Unit Tests

```powershell
python -m pytest -q
```

- [ ] All tests pass
- [ ] No warnings about missing credentials (demo mode tests should run)

### 20.2 Playwright E2E Tests

**Prerequisite:** `npm run dev` must be running (both API + Vite).

```powershell
npm run test:e2e
```

- [ ] All auth.spec.ts tests pass (login screen, invalid login, admin/operator roles, sign out, session API)
- [ ] All workflow.spec.ts tests pass (5-tab workflow, progress guide, sidebar, tabs, caption guidance, metrics, theme toggle)

### 20.3 Smoke Test (Fast)

```powershell
node e2e/smoke.mjs
```

- [ ] Prints "PASS" for each step
- [ ] Ends with "ALL E2E SMOKE TESTS PASSED"

### 20.4 Build

```powershell
npm run build
```

- [ ] Vite build completes without errors
- [ ] `dist/` directory is created

### 20.5 Vite Preview

```powershell
npm run preview
```

- [ ] Preview server starts on `http://localhost:4173`
- [ ] Built app loads and login screen is visible

---

## Appendix A: API Endpoint Reference

| Method | Path | Auth | Role | Purpose |
|--------|------|------|------|---------|
| GET | `/api/session` | Demo/Supabase | any | Get current user |
| POST | `/api/login` | none | — | Demo login |
| POST | `/api/logout` | none | — | Demo logout |
| POST | `/api/admin/users` | yes | admin | Create user |
| POST | `/api/admin/seed` | yes | admin | Seed accounts |
| POST | `/api/prepare` | yes | any | Legacy prepare endpoint |
| GET | `/api/preparations/{id}/images.zip` | none | — | Download prepared images ZIP |
| POST | `/api/log` | yes | any | Log a Facebook post URL |
| GET | `/api/jobs` | yes | any | List jobs + counts |
| POST | `/api/jobs` | yes | admin | Create a new job |
| POST | `/api/jobs/{id}/prepare` | yes | any | Prepare a job (downloads + caption) |
| POST | `/api/jobs/{id}/validate` | yes | any | Validate job property files |
| POST | `/api/jobs/{id}/captions` | yes | any | Regenerate caption variants |
| POST | `/api/jobs/{id}/mark-posted` | yes | any | Mark job posted with FB URL |
| GET | `/api/jobs/{id}/prepared.zip` | yes | any | Download job image ZIP (Supabase) |
| GET | `/api/jobs/{id}/activity` | yes | any | Get job activity log |
| POST | `/api/queue/next` | yes | admin | Claim next queue property |
| GET | `/api/offerings` | yes | any | List offerings (Supabase) |
| POST | `/api/assets/signed-url` | yes | any | Get asset signed URL (Supabase) |
| GET | `/` | none | — | Serve index.html |
| GET | `/{asset_name}` | none | — | Serve static asset |
| GET | `/prepared/{id}/{name}` | none | — | Serve prepared image (demo/local) |

---

## Appendix B: Caption Rules Quick Reference

| Rule | Value |
|------|-------|
| Forbidden phrases | `least term`, `negotiables`, `negotioables` |
| Max length | 2000 characters |
| Emojis | None allowed |
| Validation function | `validate_caption()` in `caption_generator.py` |
| AI prompt | `build_caption_prompt()` includes rules in prompt |
| Max retries | 3 (from `config.processing.max_retries`) |
| Min images | 3 (from `config.processing.min_images`) |

---

## Appendix C: Test Fixture Details

**Folder:** `Novaliches, 440 Bagbag/`

| File | Role | Format |
|------|------|--------|
| `2.png` | Property photo | PNG |
| `3.png` | Property photo | PNG |
| `4.png` | Property photo | PNG |
| `5.png` | Property photo | PNG |
| `caption reference.jpeg` | Property photo | JPEG |
| `Untitled document.docx` | Caption details document | DOCX |

**Queue requirements:**
- Minimum 3 images (PNG/JPEG/JPG supported)
- Minimum 1 caption document (DOCX/PDF/TXT supported)
- Images with suffixes `.jpg`, `.jpeg`, `.png` are valid
- Documents with suffixes `.docx`, `.pdf`, `.txt` are valid

---

*End of Manual Testing Guide*
