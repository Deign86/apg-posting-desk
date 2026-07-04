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
- `admin` can also create and assign jobs, approve caption/assets, prepare tracker
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

- Body/UI: Instrument Sans.
- Data, ids, counts, timestamps: IBM Plex Mono.
- Base body size: 16px minimum.
- Letter spacing: 0.

Light theme:

- Background: `#f7f6f2`.
- Surface: `#fbfaf7`.
- Raised/subtle surface: `#f0ede7`.
- Text: `#28251d`.
- Muted text: `#6f6c66`.
- Border: `rgba(40, 37, 29, 0.12)`.
- Primary teal: `#01696f`.
- Primary hover: `#0c4e54`.
- Primary soft: `#dbeaea`.

Dark theme:

- Background: `#171614`.
- Surface: `#1d1c19`.
- Raised/subtle surface: `#252320`.
- Text: `#e8e3dc`.
- Muted text: `#aba59a`.
- Border: `rgba(255, 255, 255, 0.11)`.
- Primary teal: `#58a9b2`.
- Primary hover: `#7ec1c9`.
- Primary soft: `#223539`.

Status colors:

- Success/ready: light `#386f20`, dark `#7ab15f`.
- Warning/review: light `#a45a1f`, dark `#cf8a4c`.
- Error/blocked: light `#9b3158`, dark `#d06d97`.

Shape and spacing:

- Spacing scale: 4px base, with 8/12/16/20/24/32/40/48px steps.
- Panel radius: 16px maximum.
- Repeated job cards/photo cards: 8px to 16px depending density.
- Inputs/buttons: minimum 44px height.
- Focus ring: 2px teal outline with 2px offset.

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

## Accessibility Contracts

- All form fields have visible labels.
- Icon-only controls require `aria-label`; text controls still need accessible
  names.
- Keyboard focus order follows the visual workflow.
- Error messages appear near the field or panel they affect.
- Disabled controls use semantic `disabled` attributes and visible styling.
- Reduced motion keeps state changes understandable without animation.
- Touch targets are at least 44px high/wide with at least 8px spacing.
