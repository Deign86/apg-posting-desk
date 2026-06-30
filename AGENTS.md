# PROJECT KNOWLEDGE BASE

**Generated:** 2026-06-30
**Commit:** none; directory is not a git worktree
**Branch:** none

## OVERVIEW

APG Posting Desk is a Python FastAPI plus Vite PWA for preparing Facebook
property posts, keeping a human in the publishing step, then logging the final
Facebook URL to Google tracking surfaces.

Current implementation is human-in-the-loop. Treat `CODEX_DEVELOPMENT_PROMPT.md`
as historical context, not the active spec for fully automated Facebook posting.

## STRUCTURE

```text
APG Prototype System for Automated Posting/
|-- apg_automation/        # Python backend, pipeline, adapters, static fallback
|-- src/                   # Vite frontend source for the PWA
|-- public/                # Vite PWA manifest, icon, service worker
|-- tests/                 # pytest coverage for backend, web app, config, UI wiring
|-- docs/                  # setup notes for external MCP/Firebase integration
|-- Novaliches, 440 Bagbag/ # local demo fixture, not source code
|-- downloads/             # generated prepared assets, not source code
|-- logs/                  # generated runtime logs, not source code
|-- index.html             # Vite entry HTML
|-- vite.config.js         # Vite dev proxy to FastAPI
|-- package.json           # npm scripts and frontend deps
|-- pyproject.toml         # Python package metadata
|-- requirements.txt       # install set used by README
`-- config.yaml            # defaults; env vars override
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| CLI/server wiring | `apg_automation/main.py` | Chooses demo vs live services and starts uvicorn |
| Prepare/log workflow | `apg_automation/review_pipeline.py` | Core backend behavior for review dashboard |
| HTTP API | `apg_automation/web_app.py` | `/api/prepare`, `/api/log`, `/api/queue/next`, asset serving |
| Caption rules | `apg_automation/caption_generator.py` | No emojis, no `least term`, no `negotiables` |
| Drive/local content | `apg_automation/google_drive.py`, `apg_automation/local_folder.py` | Same repository-like boundary |
| Tracking writes | `apg_automation/tracker_updater.py`, `apg_automation/google_tracking.py` | Sheets and Docs append behavior |
| Firebase auth/queue | `apg_automation/firebase_auth.py`, `apg_automation/firebase_queue.py` | Live-mode auth and Firestore queue claims |
| PWA behavior | `src/main.js`, `src/styles.css`, `index.html` | Vite source of the browser app |
| Static fallback assets | `apg_automation/static/` | Served by FastAPI when not using Vite |
| System diagram | `SYSTEM_FLOW_DIAGRAM.md`, `system_diagram.html` | Architecture communication artifacts |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `main` | function | `apg_automation/main.py` | CLI entry and server bootstrap |
| `DemoCaptionGenerator` | class | `apg_automation/main.py` | Credential-free demo caption substitute |
| `ReviewPipeline` | class | `apg_automation/review_pipeline.py` | Downloads assets, generates caption, logs URL |
| `PreparedPost` | dataclass | `apg_automation/review_pipeline.py` | API payload source for prepared review data |
| `create_app` | function | `apg_automation/web_app.py` | FastAPI app factory used by tests and CLI |
| `CaptionGenerator` | class | `apg_automation/caption_generator.py` | AI retry loop plus rule validation |
| `validate_caption` | function | `apg_automation/caption_generator.py` | Enforces APG caption constraints |
| `QueueManager` | class | `apg_automation/queue_manager.py` | Validates property folders before preparation |
| `ContentExtractor` | class | `apg_automation/content_extractor.py` | Reads image bundle and caption document text |
| `TrackerUpdater` | class | `apg_automation/tracker_updater.py` | Records successful manual posts |
| `FirebaseTokenVerifier` | class | `apg_automation/firebase_auth.py` | Verifies live-mode browser identity |
| `FirestorePropertyQueue` | class | `apg_automation/firebase_queue.py` | Claims pending property work |
| `authFetch` | function | `src/main.js` | Adds Firebase bearer token when signed in |

## CONVENTIONS

- Demo mode must run without Google, Firebase, or NVIDIA credentials.
- Live mode requires Firebase auth in the browser and backend token verification.
- Environment variables override `config.yaml`; do not hardcode secrets or IDs beyond documented defaults.
- Keep Facebook posting manual. Backend accepts a human-supplied live Facebook URL.
- Use repository-style adapters for external systems so tests can use fakes.
- Preserve the APG caption rules in both prompts and validation.
- Runtime asset output belongs under `downloads/` or the configured `download_root`.

## ANTI-PATTERNS (THIS PROJECT)

- Do not add automated Facebook Graph posting unless the active request explicitly changes the product direction.
- Do not commit or document real secret values from `.env`.
- Do not make tests depend on live Google, Firebase, NVIDIA, or Facebook services.
- Do not treat `logs/`, `downloads/`, `dist/`, `node_modules/`, or local fixture media as source code.
- Do not bypass caption validation when adding AI providers.

## COMMANDS

```powershell
python -m pip install -r requirements.txt
npm install
npm run dev
npm run dev:live
npm run dev:api
npm run dev:web
npm run build
python -m pytest -q
python -m apg_automation.main --dry-run --local-folder "C:/Users/Deign/Downloads/APG Prototype System for Automated Posting/Novaliches, 440 Bagbag"
```

## NOTES

- Vite proxies `/api` and `/prepared` to `http://127.0.0.1:8000`.
- `npm run dev` starts FastAPI in demo mode plus Vite.
- `apg_automation/static/` and top-level Vite files can drift; update both only when the request needs both surfaces.
- `CaptionReview.__eq__` intentionally compares clean reviews to strings for older tests.
- This folder currently has no `.git`; commands that need commit or branch data will fail until initialized or opened from a repository.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **APG Prototype System for Automated Posting** (1031 symbols, 1651 relationships, 23 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/APG Prototype System for Automated Posting/context` | Codebase overview, check index freshness |
| `gitnexus://repo/APG Prototype System for Automated Posting/clusters` | All functional areas |
| `gitnexus://repo/APG Prototype System for Automated Posting/processes` | All execution flows |
| `gitnexus://repo/APG Prototype System for Automated Posting/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
