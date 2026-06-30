# BACKEND KNOWLEDGE BASE

## OVERVIEW

Python package for APG post preparation, live-service adapters, and FastAPI API
surface.

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| CLI mode selection | `main.py` | Demo/live/dry-run routing |
| Review workflow | `review_pipeline.py` | Prepare assets and log human-posted URL |
| API routes | `web_app.py` | FastAPI app factory and static/prepared serving |
| Config loading | `config.py` | YAML plus environment override logic |
| Caption generation | `caption_generator.py`, `ai_clients.py` | Prompt, provider client, validation |
| Content extraction | `content_extractor.py` | TXT, DOCX, PDF, and image bundle validation |
| Folder lookup | `google_drive.py`, `local_folder.py` | Live Drive and local fixture sources |
| Tracking | `tracker_updater.py`, `google_tracking.py` | Google Sheets and Docs writes |
| Live auth/queue | `firebase_auth.py`, `firebase_queue.py` | Firebase Admin and Firestore queue |
| Shared data | `models.py` | Frozen dataclasses used across tests and API |

## CONVENTIONS

- Prefer constructor-injected collaborators over module-level clients.
- Keep external API construction in `build_*` helpers or `main.py`, not inside core workflow methods.
- Raise `ValueError` for user-fixable workflow failures; `web_app.py` maps them to HTTP 400.
- Keep dataclasses frozen unless mutation is essential.
- Use `Path` for filesystem paths and create parent directories at the write boundary.
- Tests use small fake collaborators; maintain protocols by behavior, not inheritance.

## ANTI-PATTERNS

- Do not perform live network calls from `ReviewPipeline`, `QueueManager`, or validators.
- Do not require credentials in demo mode or unit tests.
- Do not widen accepted post URLs beyond Facebook without updating tests and UI copy.
- Do not silently accept incomplete property folders; report explicit queue errors.
- Do not add provider-specific logic to tests when a fake client is enough.

## GOTCHAS

- `validate_runtime_config` currently checks only `NVIDIA_API_KEY` for non-dry-run NIM usage.
- `ReviewPipeline.log_post` uses `Asia/Manila` by default unless constructed otherwise.
- `web_app.create_app` stores prepared posts in process memory; restart loses zip lookup state.
- `DemoCaptionGenerator` rewrites forbidden phrases in fixture text before returning a review.
