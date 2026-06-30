# APG Posting Desk Handoff

## Current User Request

The user no longer wants implementation continued in this turn. They asked for this `HANDOFF.md` so another AI can take over the previous queued work.

Queued prompts to carry forward:

1. Continue the prior `$omo:start-work` execution after planning.
2. Use `$ui-ux-pro-max` for the overall aesthetics of the system.
3. Fix Google sign-in so it uses normal Google OAuth with the user's existing Google account.
4. Run `$omo:review-work` to verify the system still matches APG's manual posting workflow.

## Project

Workspace:

```text
C:\Users\Deign\Downloads\APG Prototype System for Automated Posting
```

Reference prototype:

```text
C:\Users\Deign\Downloads\apg-property-posting-console.html
```

Current app shape:

- Python FastAPI backend in `apg_automation/`
- Vite PWA frontend in `src/`
- Firebase project and hosting already created
- Manual Facebook publishing is still the product boundary
- Backend should prepare assets/captions and log a human-supplied Facebook URL

## Firebase State

Firebase project created and connected:

```text
Project ID: apg-posting-desk-deign-2026
Hosting URL: https://apg-posting-desk-deign-2026.web.app/
Web app ID: 1:676310407748:web:9ab12f1c0ebcab17fbba11
```

Files already added or changed for Firebase:

- `.firebaserc`
- `firebase.json`
- `firestore.rules`
- `firestore.indexes.json`
- `.env`
- `.env.example`
- `.gitignore`
- `docs/FIREBASE_MCP_SETUP.md`

Firebase deploys reportedly succeeded earlier:

```powershell
firebase deploy --only firestore,hosting --project apg-posting-desk-deign-2026 --json
firebase deploy --only auth --project apg-posting-desk-deign-2026 --json
```

Do not write raw tokens, API keys, cookies, or service credentials into logs or docs.

## Important OAuth Issue

The user's screenshot shows Google sign-in forcing `@apg.example`.

Root cause found:

```text
.env: VITE_APG_GOOGLE_DOMAIN=apg.example
.env.example: VITE_APG_GOOGLE_DOMAIN=apg.example
src/main.js sets provider.setCustomParameters({ hd: hostedDomain })
```

This means Firebase Google OAuth is already being used, but the hosted-domain hint is set to a fake placeholder domain.

Next fix:

- Blank or remove `VITE_APG_GOOGLE_DOMAIN` in `.env`.
- Blank it in `.env.example`.
- Update `src/main.js` so placeholder domains such as `apg.example` are ignored.
- Update docs to say this setting is optional and should be blank for normal existing Google accounts.
- Rebuild and redeploy hosting after the fix.

Suggested robust frontend pattern:

```js
const hostedDomain = (import.meta.env.VITE_APG_GOOGLE_DOMAIN || "").trim();
const shouldRestrictDomain = hostedDomain && !hostedDomain.endsWith(".example");

if (shouldRestrictDomain) {
  provider.setCustomParameters({ hd: hostedDomain });
}
```

## Manual APG Workflow To Preserve

The user listed this as the real-world workflow:

1. Find the property on APG Listing Drive:
   `https://drive.google.com/drive/folders/1GXeGULYswb7jXcMGCCRm2RQ_h0EKsDll?usp=drive_link`
2. Property names to post are assigned by supervisor Ma'am Jean.
3. Each property should have at least 3 pictures and 1 document with caption details.
4. Caption details are minimal info; AI generates the final caption from that.
5. Caption rules:
   - no emojis
   - avoid `least term`
   - avoid `negotiables`
   - also guard likely misspelling `negotioables`
6. Human posts manually to Facebook.
7. Human copies the final Facebook post link.
8. System updates `POSTING TRACKER - INTERNS - Google Sheets`.
9. System updates `APG_Daily Progress Report (June 26, 2026) - Google Docs`.

Keep Facebook posting manual unless the user explicitly changes the product direction.

## Current Code Observations

Files changed by prior workers:

- `DESIGN.md`
- `tests/test_firebase_auth.py`
- `tests/test_web_app.py`
- `tests/test_vite_app.py`
- `apg_automation/firebase_auth.py`
- `apg_automation/web_app.py`
- `src/main.js`
- `src/styles.css`
- `index.html`

The prior audit reported:

```powershell
python -m pytest tests/test_firebase_auth.py tests/test_web_app.py tests/test_vite_app.py -q
# 19 passed, 1 warning

npm run build
# passed
```

Rerun verification because more work is still needed.

## Backend Gap Found Before Stop

The frontend references these routes:

```text
GET  /api/session
GET  /api/jobs
POST /api/jobs
POST /api/jobs/{job_id}/validate
POST /api/jobs/{job_id}/prepare
POST /api/jobs/{job_id}/captions
POST /api/jobs/{job_id}/mark-posted
GET  /api/jobs/{job_id}/activity
POST /api/prepare
POST /api/log
```

`apg_automation/web_app.py` currently exposes:

```text
GET  /api/session
POST /api/prepare
GET  /api/preparations/{preparation_id}/images.zip
POST /api/log
GET  /api/jobs
POST /api/jobs
POST /api/jobs/{job_id}/mark-posted
POST /api/queue/next
```

Missing route adapters likely still need implementation:

- `POST /api/jobs/{job_id}/validate`
- `POST /api/jobs/{job_id}/prepare`
- `POST /api/jobs/{job_id}/captions`
- `GET /api/jobs/{job_id}/activity`

These should call existing pipeline/store behavior and return payloads the frontend already expects.

## Existing Useful Files

Core backend:

- `apg_automation/web_app.py`
- `apg_automation/review_pipeline.py`
- `apg_automation/caption_generator.py`
- `apg_automation/google_drive.py`
- `apg_automation/google_tracking.py`
- `apg_automation/tracker_updater.py`
- `apg_automation/firebase_auth.py`
- `apg_automation/firebase_queue.py`
- `apg_automation/job_store.py`

Frontend:

- `src/main.js`
- `src/styles.css`
- `index.html`
- `public/manifest.webmanifest`
- `public/service-worker.js`

Docs/planning:

- `DESIGN.md`
- `.omo/plans/apg-firebase-console.md`
- `.omo/drafts/apg-firebase-console.md`
- `.omo/start-work/ledger.jsonl`
- `docs/FIREBASE_MCP_SETUP.md`

Tests:

- `tests/test_firebase_auth.py`
- `tests/test_web_app.py`
- `tests/test_vite_app.py`
- `tests/test_review_pipeline.py`

## Recommended Next Work Order

1. Fix OAuth hosted-domain restriction.
2. Add tests for missing job route adapters.
3. Implement missing job route adapters in `apg_automation/web_app.py` and, if needed, small store helpers in `apg_automation/job_store.py`.
4. Ensure caption validation catches `least term`, `negotiables`, and likely misspelling `negotioables`.
5. Verify manual flow:
   - Ma'am Jean/admin can create or assign property jobs.
   - User/operator can process an assigned property.
   - System validates at least 3 images and 1 caption document.
   - System generates a compliant caption.
   - Human manually posts to Facebook.
   - System accepts the pasted Facebook URL.
   - Tracker and daily report adapters are called.
6. Run:

```powershell
python -m pytest -q
npm run build
```

7. Run the app and smoke-test API/UI behavior:

```powershell
npm run dev
```

8. Deploy updated hosting after build:

```powershell
firebase deploy --only hosting --project apg-posting-desk-deign-2026 --json
```

9. Perform final review-work style check:
   - goal/constraint alignment
   - hands-on QA
   - code quality
   - security/auth review
   - context/manual-flow check

## Notes For Next AI

- This folder reportedly has no `.git`; normal git diff/status may fail.
- Do not revert unrelated existing changes.
- Use `apply_patch` for manual edits.
- On Windows, prefer the OMO `git_bash` MCP for shell commands when available.
- Keep `.env` secret-safe. Do not paste raw Firebase config into reports unless the user explicitly asks and it is safe.
- The product should feel like an internal operations console, not a marketing page.
- UI should stay dense, scannable, accessible, and workflow-first.
- The three system personas/roles are:
  - `admin`
  - `maam_jean`
  - `user`

