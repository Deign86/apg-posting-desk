# APG Posting Console Design System

## Product Direction

APG Posting Console is an operational command center for preparing Facebook
property posts while keeping the final publishing step human-in-the-loop. The
interface must support admins, Ma'am Jean, and operators moving jobs through
intake, Drive validation, asset selection, caption preparation, manual
publishing, tracker sync, and activity review.

The prototype at `C:/Users/Deign/Downloads/apg-property-posting-console.html`
is the functional and visual baseline. It establishes the first-screen product
signal, queue navigation, job workspace, intake validation, selectable Drive
assets, caption variants, manual publish checklist, tracker sync preview,
activity log, and theme toggle.

## Experience Principles

- Dense, scannable operations dashboard; no marketing hero or decorative
  illustration.
- Manual Facebook publishing remains explicit and checklist-driven.
- Every role sees clear capability boundaries before an action is attempted.
- Status is conveyed with text plus color, never color alone.
- All primary controls keep at least a 44px target, visible focus, and keyboard
  access.
- No emoji icons. Use consistent vector icons where icons are needed.
- Light and dark themes are designed together with semantic tokens.

## Roles

- `admin`: manage role bootstrap, view all jobs, override stuck jobs, inspect
  activity.
- `maam_jean`: create and assign jobs, approve caption/assets, prepare tracker
  sync.
- `user`: process assigned jobs, validate assets, choose photos, generate and
  select captions, complete the manual publish checklist, submit Facebook URLs.

## Required Surfaces

- App identity: `APG Posting Console`.
- Queue navigation with counts: Assigned today, Waiting approval, Ready to post,
  Posted today.
- Job list with job id, property name, assignee, due date, and status.
- Intake and validation form: property name, assigned by, operator, due date,
  Drive folder URL, validation results.
- Drive assets panel: selectable photos, selected-count badge, caption document
  status.
- Caption workbench: caption details source, final caption, 3 variants, rule
  check for no emojis, no `least term`, no `negotiables`.
- Human-in-the-loop publish checklist: caption approved, 3 photos selected,
  manually posted on Facebook, final Facebook URL.
- Tracker sync preview: posting tracker row and daily progress report entry.
- Activity log: chronological user/system events.
- Theme toggle: warm light theme and dark theme.

## Visual Tokens

Typography:

- Body/UI: Poppins.
- Display/headings: Orbitron.
- Data, ids, counts, timestamps: IBM Plex Mono.
- Base body size: 16px minimum.
- Letter spacing: 0.

Light theme:

- Background: `#f5f3ef`.
- Surface: `#ffffff`.
- Raised/subtle surface: `#f0ede7`.
- Text: `#2c2c2c`.
- Muted text: `#6a6a6a`.
- Border: `rgba(197, 160, 89, 0.25)`.
- Primary gold: `#b2912f`.
- Primary hover: `#c5a059`.
- Primary soft: `rgba(197, 160, 89, 0.1)`.
- Accent-2: `#e2c285`.

Dark theme:

- Background: `#0a0a0a`.
- Surface: `#141414`.
- Raised/subtle surface: `#1a1a1a`.
- Text: `#e0e0e0`.
- Muted text: `#9a9489`.
- Border: `rgba(197, 160, 89, 0.2)`.
- Primary gold: `#c5a059`.
- Primary hover: `#d4af37`.
- Primary soft: `rgba(197, 160, 89, 0.12)`.
- Accent-2: `#e2c285`.

Status colors:

- Success/ready: light `#386f20`, dark `#7ab15f`.
- Warning/review: light `#a45a1f`, dark `#e2c285`.
- Error/blocked: light `#b5443e`, dark `#d4675e`.

Shape and spacing:

- Spacing scale: 4px base, with 8/12/16/20/24/32/40/48px steps.
- Panel radius: 16px maximum.
- Repeated job cards/photo cards: 8px to 16px depending density.
- Inputs/buttons: minimum 44px height.
- Focus ring: 2px gold outline with 2px offset.

Materiality:

- Panels use `backdrop-filter: blur(10px)` for glassmorphism.
- Shadows are tinted to the gold accent hue (`--shadow-gold`).
- Golden scrollbar: gold thumb on dark/surface track.
- Transitions: `all 0.3s cubic-bezier(0.25, 1, 0.5, 1)`.

## Layout

- Desktop: sticky left sidebar for identity, theme, queue counts, and job list;
  main workspace uses a two-column operational layout.
- Tablet: collapse workspace to one column while preserving sidebar and counts.
- Mobile: single-column layout with queue navigation before workspace; no
  horizontal scrolling.
- Fixed-format elements such as queue badges, photo tiles, and icon buttons
  must use stable dimensions to avoid layout shift.

## Components

- Queue button: label plus count badge, active state using primary soft surface.
- Job row: property name, status badge, job id, assigned-by, due date.
- Metric tile: compact label, strong value, supporting helper text.
- Panel: header with title/action/status, body with form or workflow content.
- Validation step: title plus Passed/Needs attention text.
- Photo tile: selectable image/placeholder, selected state ring, file metadata.
- Caption variant: candidate label, caption body, use/copy actions.
- Checklist item: native checkbox with visible label.
- Tracker preview: read-only or editable textareas for row/report output.
- Activity item: timestamp and concise event text.

## UX Patterns

- Loading spinner: shown when API operations are in-flight (pipeline runs,
  caption generation, validation). Uses a gold circular spinner with
  `@keyframes` rotation. Respects `prefers-reduced-motion` by disabling
  animation.
- Error banner: persistent dismissible banner at the top of the workspace for
  failed API calls. Uses `role="alert"` and a dismiss button. Not a transient
  toast — stays visible until the operator dismisses it.
- Empty state: shown in the job list when no jobs are assigned. Displays a
  centered prompt with an icon, "No jobs assigned" title, and a hint to click
  "New intake" or "Process next" to begin.
- Confirmation dialog: native `<dialog>` element shown before the irreversible
  "Log Post" action. Displays the property name and Facebook URL, with Confirm
  and Cancel buttons. Uses `showModal()` / `close()`.

## Accessibility Contracts

- All form fields have visible labels.
- Icon-only controls require `aria-label`; text controls still need accessible
  names.
- Keyboard focus order follows the visual workflow.
- Error messages appear near the field or panel they affect.
- Disabled controls use semantic `disabled` attributes, `aria-disabled="true"`,
  and visible styling.
- Connection status element has `aria-live="polite"` and `role="status"` so
  screen readers announce state changes.
- Active job row in the job list has `aria-current="page"`.
- Workflow steps in the publish guide map `data-state` to
  `aria-current="step"` when active.
- Disabled log button has `aria-disabled="true"` alongside the `disabled`
  attribute.
- Reduced motion keeps state changes understandable without animation.
- Touch targets are at least 44px high/wide with at least 8px spacing.
