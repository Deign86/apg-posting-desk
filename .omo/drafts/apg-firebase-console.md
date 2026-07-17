---
slug: apg-firebase-console
status: awaiting-approval
intent: clear
pending-action: write .omo/plans/apg-firebase-console.md
approach: Build a Firebase-backed APG Posting Console matching the prototype's workflow, with role-aware UI/API behavior for admin, Ma'am Jean, and operators while preserving manual Facebook posting.
---

# Draft: apg-firebase-console

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
| C1 | Firebase project/workspace setup, Auth provider, Firestore rules/indexes, and SDK config | active | Firebase MCP environment + project list |
| C2 | Role model for admin, Ma'am Jean, and users/operators enforced by backend dependencies and Firestore rules | active | `apg_automation/firebase_auth.py`, Firebase custom-claims docs |
| C3 | Firestore job backend for queue, assignment, validation, caption variants, selected images, publish checklist, tracker preview, and activity log | active | prototype IDs/functions + current `firebase_queue.py` |
| C4 | FastAPI routes that bridge Firebase-authenticated users to Drive preparation, AI captions, tracker logging, and job state changes | active | `apg_automation/web_app.py`, `review_pipeline.py` |
| C5 | Vite console UI rebuilt from prototype behavior and extracted `DESIGN.md` tokens | active | prototype HTML + current `src/main.js`/`index.html` |
| C6 | Tests and real-surface QA proving role permissions, Firebase-backed job flows, and responsive UI behavior | active | current pytest/Vite tests + visual QA skill |

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
<!-- assumption | adopted default | rationale | reversible? -->
| Facebook publishing | Keep manual human-in-the-loop posting | Root `AGENTS.md` marks automated Facebook posting out of scope unless explicitly changed | reversible by future scope change |
| Role storage | Use Firebase custom claims for coarse role and Firestore docs for profile/display metadata | Official Firebase docs support custom claims in rules; claims avoid trusting client role state | reversible with migration |
| Bootstrap admin | Use `APG_BOOTSTRAP_ADMIN_EMAIL`/manual Admin SDK command to grant the first admin, then admin UI manages roles | Avoids hardcoding a personal UID/email in source | reversible |
| Backend shape | Keep FastAPI as privileged backend for Drive, AI caption generation, Sheets/Docs tracking; use Firestore as operational job database | Current project already has FastAPI adapters and tests; Firebase client alone cannot safely call Google/NVIDIA secrets | reversible but larger |
| Design direction | Extract `DESIGN.md` from prototype's Instrument Sans/IBM Plex Mono, teal-on-warm-paper command-center style | Prototype is the visual/product contract; current repo has no `DESIGN.md` | reversible before implementation |
| Test strategy | TDD/red-first for backend/API/domain changes plus browser QA for UI | Required by ultrawork and programming rules | not reversible |

## Findings (cited - path:lines)
- Prototype: `C:/Users/Deign/Downloads/apg-property-posting-console.html:127` queue nav counts for assigned, approval, ready, posted.
- Prototype: `C:/Users/Deign/Downloads/apg-property-posting-console.html:163` intake/validation panel with property, assigned-by, operator, due date, Drive URL.
- Prototype: `C:/Users/Deign/Downloads/apg-property-posting-console.html:203` Drive assets panel with selectable photos and selected count.
- Prototype: `C:/Users/Deign/Downloads/apg-property-posting-console.html:217` caption workbench with variants and APG rules check.
- Prototype: `C:/Users/Deign/Downloads/apg-property-posting-console.html:244` human-in-the-loop publish checklist.
- Prototype: `C:/Users/Deign/Downloads/apg-property-posting-console.html:272` tracker sync preview.
- Prototype: `C:/Users/Deign/Downloads/apg-property-posting-console.html:297` activity log.
- Current UI: `index.html` is a simpler prepare/log flow; it lacks job list, role views, validation editing, variants, tracker preview, and activity log.
- Current JS: `src/main.js` already initializes Firebase Auth, Google sign-in, hosted-domain hint, bearer token API calls, `/api/prepare`, `/api/log`, and `/api/queue/next`.
- Current backend: `apg_automation/web_app.py` has `/api/prepare`, `/api/log`, `/api/queue/next`; it lacks full job CRUD, role gates, activity persistence, caption variant selection, checklist state, and tracker preview endpoints.
- Current Firebase queue: `apg_automation/firebase_queue.py` only claims one pending property and updates `status=processing`.
- Current auth: `apg_automation/firebase_auth.py` verifies Firebase ID tokens but does not enforce roles.
- Firebase MCP: authenticated as `deign86@gmail.com`; project directory points at `C:\Users\Deign\Downloads\deign-lazaro-dev`; no active project, no `firebase.json`.
- Firebase MCP: accessible projects are `gamecon-2026-ops`, `hermes-instagram-watcher`, `mathpulse-ai-2026`, and `rcbc-debt-tracker-app`; none obviously belongs to APG.
- Firebase docs via Context7: Firebase custom claims are intended for role/access data and can be consumed by Firestore security rules.
- Firebase JS SDK docs via Context7: existing `signInWithPopup`, `GoogleAuthProvider`, `getIdToken`, and Firestore imports are appropriate for web auth/data access.
- Frontend gate: no `DESIGN.md` exists; implementation must create/extract one before UI changes.

## Decisions (with rationale)
- Plan will preserve manual Facebook posting; "fully functional" means the console workflow persists, validates, assigns, prepares, posts manually, and logs/tracks through the system.
- Plan will use two roles: `admin` and `user`.
- `admin` can manage users/roles, seed jobs, see all queues, override stuck jobs, and inspect logs.
- `user` can claim/process assigned jobs, validate assets, generate/select captions, complete manual publish checklist, and submit Facebook URLs for logging.
- Firestore collections will be planned as `users`, `jobs`, `jobs/{jobId}/activity`, and optional `settings`.
- Backend will remain the trust boundary for external secrets and Google/NVIDIA operations; client Firestore writes are limited by rules.
- API endpoints will be role-gated server-side even if Firestore rules also gate client reads/writes.
- Plan will include Firebase MCP setup but will not assume an active APG project until the user provides/chooses it.

## Scope IN
- Firebase project directory setup for this workspace.
- Firebase Auth Google provider plan and web app SDK config retrieval.
- Firestore rules/schema/indexes for APG job workflow and roles.
- Backend role dependencies and job API surface.
- UI parity with prototype workflow plus role-specific navigation/states.
- Demo/local mode compatible fakes so tests pass without live Firebase credentials.
- TDD tests, API/manual surface QA, browser screenshots, and reviewer gate.

## Scope OUT (Must NOT have)
- No automated Facebook Graph API publishing.
- No real secret values committed to source.
- No tests requiring live Google/Firebase/NVIDIA/Facebook credentials.
- No silent use of unrelated Firebase projects.
- No UI implementation before `DESIGN.md` exists.
- No replacement of the existing Drive/AI/Google tracking adapters unless required for the role/job backend.

## Open questions
- Firebase project binding: use an existing project, or create/select a new APG-specific Firebase project before execution?
- Approval: write the full execution plan to `.omo/plans/apg-firebase-console.md` using the approach above?

## Approval gate
status: awaiting-approval
pending: approval to write detailed plan todos into `.omo/plans/apg-firebase-console.md`; execution still requires a later explicit start command.
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
