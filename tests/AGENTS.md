# TEST KNOWLEDGE BASE

## OVERVIEW

Pytest suite covering backend workflow, configuration, adapters, PWA file wiring,
and focused frontend/static expectations.

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Pipeline behavior | `test_review_pipeline.py` | Fake drive, captioner, tracker |
| FastAPI routes | `test_web_app.py` | `TestClient` around `create_app` |
| Caption rules | `test_caption_generator.py` | Forbidden phrase, emoji, retry validation |
| Config/env | `test_config.py` | YAML defaults and env overrides |
| Google boundaries | `test_google_auth.py`, `test_google_workspace_mcp.py` | Auth and MCP adapter behavior |
| Firebase boundaries | `test_firebase_auth.py`, `test_firestore_queue.py` | Live-mode auth/queue fakes |
| Frontend wiring | `test_vite_app.py`, `test_main_local.py` | Scripts, proxy, CLI behavior |
| E2E browser auth flow | `e2e/specs/auth.spec.ts` | Playwright: login, role gates, session API |
| E2E workflow smoke | `e2e/specs/workflow.spec.ts` | Playwright: 5 tabs, metrics, workflow guide |
| E2E quick smoke | `e2e/smoke.mjs` | Node script: fast full-flow test (8 scenarios) |
| Fixture integration | `test_real_property_fixture.py` | Skips if local fixture is absent |

## CONVENTIONS

- Use fake collaborators for external services.
- Use `tmp_path` for downloaded assets and generated files.
- Keep assertions at the user-visible contract level: payloads, records, errors, scripts.
- Prefer `python -m pytest -q` from the repository root.
- Real local fixture tests must skip when fixture data is absent.

## ANTI-PATTERNS

- Do not add tests that need real credentials or network access.
- Do not weaken caption rule tests to fit generated model output.
- Do not inspect generated `downloads/` or `logs/` as stable fixtures.
- Do not rely on test ordering; each test should construct its own fakes and state.

## COMMANDS

```powershell
python -m pytest -q
python -m pytest tests/test_review_pipeline.py -q
python -m pytest tests/test_web_app.py -q
npm run test:e2e          # Requires running servers (npm run dev)
node e2e/smoke.mjs        # Quick E2E smoke test (fast, no test runner overhead)
```
