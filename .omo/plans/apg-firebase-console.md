# apg-firebase-console - Work Plan

## TL;DR (For humans)

**What you'll get:** A working APG Posting Console with role-aware access for admin, Ma'am Jean, and users, backed by the new Firebase project. It will cover the prototype workflow: queue management, intake validation, asset selection, caption variants, manual publish checklist, tracker preview, and activity history.

**Why this approach:** Firebase Auth and Firestore handle identity, roles, and shared job state, while FastAPI stays the trusted backend for Drive, AI captions, and Google tracker updates. The UI will use the prototype as the product contract and the ui-ux-pro-max guidance for a polished operations-console aesthetic.

**What it will NOT do:** It will not automate Facebook publishing, commit real secrets, or require live Firebase/Google/NVIDIA credentials for local tests.

**Effort:** Large
**Risk:** High - auth, roles, external Firebase state, backend routes, and a full UI rebuild all touch core behavior.
**Decisions to sanity-check:** Manual Facebook posting stays in scope; Firebase project is `apg-posting-desk-deign-2026`; role names are `admin`, `maam_jean`, `user`.

Your next move: execute the plan, then run the final review and deploy. Full execution detail follows below.

---

> TL;DR (machine): HEAVY plan: Firebase role/job backend + prototype-equivalent Vite console + tests + deployed/manual QA.

## Scope
### Must have
- Firebase project binding remains `apg-posting-desk-deign-2026` in `.firebaserc`, `.env`, `.env.example`, and MCP environment.
- Role model supports `admin`, `maam_jean`, and `user` from Firebase ID token custom claims, with demo fallback roles for tests/local mode.
- Backend exposes job APIs for list, create/intake, validate/prepare, caption variant generation/selection, image selection, publish checklist, mark posted/log tracker, tracker preview, activity log, and role/user bootstrap views.
- Firestore-backed implementation is used in live mode; in-memory demo implementation keeps `npm run dev` and pytest credential-free.
- Frontend matches the prototype's functional surface: sidebar queues/counts, job list, metrics, intake/validation, assets, caption variants, manual publish checklist, tracker preview, activity log, theme toggle, role-aware controls.
- UI aesthetics use APG command-center style: warm operational light theme plus dark theme, teal primary, status colors, Instrument Sans / IBM Plex Mono, 44px controls, visible focus, responsive 375/768/1280 widths.
- `DESIGN.md` exists before UI code uses new tokens and documents components/states.
- Tests and manual QA prove the role gates and end-to-end job flow.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- No automated Facebook Graph API publishing.
- No real service account JSON or private secret committed.
- No tests requiring live Google, Firebase, NVIDIA, or Facebook credentials.
- No silent reuse of unrelated Firebase projects.
- No frontend freehand styling outside `DESIGN.md` tokens.
- No weakening or deleting existing tests.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD with pytest for backend/API/domain and existing Vite build tests for frontend source contracts.
- Red proof: add failing tests before production changes for role claims/job API/UI markup contracts.
- Automated commands: `python -m pytest -q`, `npm run build`, `firebase deploy --only firestore,hosting --project apg-posting-desk-deign-2026`.
- HTTP QA: `curl.exe -i http://127.0.0.1:<port>/api/jobs` without auth must return 200 in demo mode or 401 in live-auth mode depending launched command; `curl.exe -i https://apg-posting-desk-deign-2026.web.app/` must return `HTTP/1.1 200 OK` and console title.
- Browser QA: Playwright/Chrome screenshots at 375, 768, 1280 after `npm run dev` or a preview server; evidence under `.omo/evidence/apg-firebase-console/`.
- Firebase QA: MCP/CLI environment must show active project alias `default: apg-posting-desk-deign-2026` and active web app.

## Execution strategy
### Parallel execution waves
- Wave 1: backend role/job tests + backend implementation; design system + frontend tests/UI implementation can run in parallel using the API contract below.
- Wave 2: integration fixes, Firebase rules/index updates, static FastAPI fallback sync.
- Wave 3: automated QA, browser QA, deploy, reviewer gate.

### Backend/API contract for frontend workers
- `GET /api/session` -> `{user:{uid,email,role,display_name}, firebase_project_id}`.
- `GET /api/jobs` -> `{jobs:[...], counts:{assigned_today,waiting_approval,ready_to_post,posted_today}}`.
- `POST /api/jobs` body `{property_name,assigned_by,operator,due_date,drive_url}` -> created job.
- `POST /api/jobs/{job_id}/validate` -> updates validation status.
- `POST /api/jobs/{job_id}/prepare` -> runs existing pipeline when possible and fills caption details/images/caption.
- `POST /api/jobs/{job_id}/captions` -> generates or returns 3 variants.
- `PATCH /api/jobs/{job_id}` -> allowed job field updates.
- `POST /api/jobs/{job_id}/mark-posted` body `{facebook_url}` -> validates checklist, records tracker, status posted.
- `GET /api/jobs/{job_id}/activity` -> activity list.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1 | none | 2, 4 | none |
| 2 | 1 | 4, 5 | 3 |
| 3 | 1 | 5 | 2 |
| 4 | 2 | 6 | 5 |
| 5 | 2, 3 | 6 | 4 |
| 6 | 4, 5 | final wave | none |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Create design system and backend/frontend RED tests
  What to do / Must NOT do: Write `DESIGN.md` from prototype/ui-ux-pro-max findings. Add failing pytest coverage for role extraction, role dependency denial, job API list/create/mark-posted. Add frontend source tests asserting prototype console sections and role labels exist. Do not edit production behavior yet.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 2, 3, 4, 5
  References: `.omo/drafts/apg-firebase-console.md`; `C:/Users/Deign/Downloads/apg-property-posting-console.html`; `tests/test_firebase_auth.py`; `tests/test_web_app.py`; `tests/test_vite_app.py`; ui-ux-pro-max result in session.
  Acceptance criteria: `python -m pytest tests/test_firebase_auth.py tests/test_web_app.py tests/test_vite_app.py -q` fails for missing role/job/console behavior, not syntax/import mistakes.
  QA scenarios: HTTP failure proof via `python -m pytest tests/test_web_app.py -q` red output saved to `.omo/evidence/apg-firebase-console/task-1-red.txt`.
  Commit: N | staged with later implementation.

- [ ] 2. Implement role-aware Firebase job backend
  What to do / Must NOT do: Add typed backend role/session helpers and a job store abstraction with in-memory demo store and Firestore live store. Extend FastAPI routes to the API contract. Preserve `/api/prepare`, `/api/log`, `/api/queue/next` compatibility where practical. Do not call live services in tests.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 4, 5
  References: `apg_automation/firebase_auth.py`; `apg_automation/firebase_queue.py`; `apg_automation/web_app.py`; `apg_automation/review_pipeline.py`; `firestore.rules`.
  Acceptance criteria: `python -m pytest tests/test_firebase_auth.py tests/test_web_app.py tests/test_review_pipeline.py -q` passes.
  QA scenarios: HTTP call `curl.exe -i http://127.0.0.1:<demo-port>/api/jobs` returns 200 and JSON counts in demo mode; save `.omo/evidence/apg-firebase-console/task-2-api.txt`.
  Commit: Y | `feat(backend): add role-aware Firebase job API`.

- [ ] 3. Implement prototype-equivalent console UI
  What to do / Must NOT do: Replace simple Vite page with console layout matching prototype functions, role-aware controls, theme toggle, queue counts, job workspace, validation, assets, caption variants, publish checklist, tracker preview, and activity log. Use `DESIGN.md` tokens and ui-ux-pro-max accessibility/touch guidance. Do not use emojis as icons.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 5
  References: `DESIGN.md`; `index.html`; `src/main.js`; `src/styles.css`; prototype IDs/functions listed in draft findings.
  Acceptance criteria: `python -m pytest tests/test_vite_app.py -q` and `npm run build` pass.
  QA scenarios: Browser action `page.goto(http://127.0.0.1:5173)`, click theme toggle, click New intake, fill property, validate, generate captions; screenshots 375/768/1280 saved under `.omo/evidence/apg-firebase-console/task-3-*.png`.
  Commit: Y | `feat(frontend): build APG role-aware posting console`.

- [ ] 4. Connect Firebase rules, config, and docs to role/job schema
  What to do / Must NOT do: Update `firestore.rules`, indexes if needed, Firebase docs, and local env examples for final role/job collections. Use custom-claim roles and allow only safe client operations. Do not expose private secrets.
  Parallelization: Wave 2 | Blocked by: 2 | Blocks: 6
  References: `firestore.rules`; `firebase.json`; `.env.example`; `docs/FIREBASE_MCP_SETUP.md`; Context7 Firebase custom-claims findings.
  Acceptance criteria: `firebase deploy --only firestore --project apg-posting-desk-deign-2026 --json` succeeds.
  QA scenarios: Firebase CLI `firebase apps:list --project apg-posting-desk-deign-2026 --json` returns active web app; save `.omo/evidence/apg-firebase-console/task-4-firebase.json`.
  Commit: Y | `chore(firebase): align rules with APG job roles`.

- [ ] 5. Sync FastAPI static fallback and README/operator docs
  What to do / Must NOT do: If top-level Vite UI changes, sync `apg_automation/static/` where current app expects it, or document Vite-only serving clearly. Update README with role setup, first admin bootstrap, dev/live commands, and Firebase project ID. Do not duplicate stale instructions.
  Parallelization: Wave 2 | Blocked by: 2, 3 | Blocks: 6
  References: `README.md`; `apg_automation/static/`; `docs/FIREBASE_MCP_SETUP.md`; root `AGENTS.md` note about static/Vite drift.
  Acceptance criteria: `python -m pytest -q` and `npm run build` pass.
  QA scenarios: HTTP call to FastAPI root in demo mode returns console HTML containing `APG Posting Console`; save `.omo/evidence/apg-firebase-console/task-5-fastapi.txt`.
  Commit: Y | `docs(app): document Firebase role console setup`.

- [ ] 6. Full verification, deploy, cleanup, and review gate
  What to do / Must NOT do: Run complete automated suite, browser visual QA, HTTP QA, Firebase deploy, cleanup running servers, and review-work gate. Do not claim done from tests alone.
  Parallelization: Wave 3 | Blocked by: 4, 5 | Blocks: final wave
  References: all changed files; `.omo/start-work/ledger.jsonl`; review-work skill.
  Acceptance criteria: `python -m pytest -q`, `npm run build`, deploy success, deployed `curl` 200, screenshots captured, reviewer approval or fixed rerun.
  QA scenarios: Browser and HTTP evidence saved under `.omo/evidence/apg-firebase-console/final/` with cleanup receipt.
  Commit: N unless user asks to commit.

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit
- [ ] F2. Code quality review
- [ ] F3. Real manual QA
- [ ] F4. Scope fidelity

## Commit strategy
No git commits unless explicitly requested. This folder was previously not a git worktree; if git remains unavailable, report changed files and suggested conventional commit messages instead.

## Success criteria
- Firebase MCP and local files point at `apg-posting-desk-deign-2026`.
- Admin, Ma'am Jean, and user roles have distinct backend/UI capabilities.
- Prototype workflow is available in the app with persistent job/activity state.
- Demo mode runs without live credentials; live mode uses Firebase Auth/Firestore.
- Existing tests plus new role/job/UI tests pass.
- Vite build passes and deployed Firebase Hosting returns the console.
- Browser QA verifies desktop/tablet/mobile layouts and primary workflow.

