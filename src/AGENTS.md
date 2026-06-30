# FRONTEND KNOWLEDGE BASE

## OVERVIEW

Vite browser app for the APG operator workflow: prepare property, inspect source
details, download assets, copy caption, open Facebook, then log the live URL.

## STRUCTURE

```text
src/
|-- main.js      # DOM state machine, Firebase auth, API calls
`-- styles.css   # Full PWA styling
```

Top-level `index.html` supplies the DOM nodes consumed by `src/main.js`.
`public/` supplies the Vite manifest, icon, and service worker.

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Workflow state | `main.js` | `workflowState`, `resetWorkflowState`, `updateWorkflowGuide` |
| API transport | `main.js` | `authFetch` attaches Firebase token when available |
| Firebase login | `main.js` | Popup Google sign-in, optional hosted domain hint |
| Image rendering | `main.js` | `renderImages` uses `#imageTemplate` |
| Visual layout | `styles.css` | Dashboard, workflow steps, gallery, responsive behavior |
| Browser shell | `../index.html` | Forms, buttons, templates, status labels |
| Dev proxy | `../vite.config.js` | `/api` and `/prepared` to FastAPI on port 8000 |

## CONVENTIONS

- Keep browser state explicit in `workflowState`; update controls via `updateWorkflowGuide`.
- API endpoints should stay relative so Vite proxy and same-origin FastAPI serving both work.
- Do not require Firebase config for demo mode; missing config should keep the app usable.
- Disable or lock workflow actions until prerequisites are met.
- Preserve service worker registration path `/service-worker.js`.

## ANTI-PATTERNS

- Do not duplicate server validation only in the frontend; backend remains the source of truth.
- Do not hardcode live Firebase credentials in source.
- Do not let copy/log actions proceed before assets and caption have been prepared.
- Do not rename DOM IDs without updating `main.js` selectors and tests.

## QA NOTES

- Manual surface is `npm run dev`, then open `http://localhost:5173`.
- Demo path should work with the `Novaliches, 440 Bagbag` fixture and no live credentials.
- Build check is `npm run build`.
