# APG Posting Desk - Human-In-The-Loop Flow

```mermaid
flowchart TD
    U[Operator] -->|Inputs property name| PWA[PWA Dashboard]
    PWA -->|POST /api/prepare| API[FastAPI Backend]
    API -->|Search folder and fetch files| GD[(APG Listing Drive)]
    GD -->|Images and caption document| API
    API -->|Caption details| NIM{NVIDIA NIM}
    NIM -->|Generated caption| API
    API -->|Caption, images, zip URL| PWA
    PWA -->|Review, copy caption, download images| U
    U -->|Manual publish| FB[Facebook Web]
    FB -->|Live post URL| U
    U -->|Pastes URL and clicks Log Post| PWA
    PWA -->|POST /api/log| API
    API -->|Append row| GS[(Posting Tracker Sheet)]
    API -->|Append bullet| DOC[(Daily Progress Report Doc)]
```

## Backend Routes

### `POST /api/prepare`

Request:

```json
{
  "property_name": "Novaliches, 440 Bagbag"
}
```

Response:

```json
{
  "preparation_id": "generated-id",
  "property_name": "Novaliches, 440 Bagbag",
  "caption": "Generated APG-safe caption",
  "caption_details": "Raw extracted caption details",
  "images": [
    { "name": "2.png", "url": "/prepared/generated-id/2.png" }
  ],
  "download_zip_url": "/api/preparations/generated-id/images.zip",
  "requires_manual_review": false,
  "violations": []
}
```

### `POST /api/log`

Request:

```json
{
  "property_name": "Novaliches, 440 Bagbag",
  "facebook_url": "https://facebook.com/live-post-url"
}
```

Response:

```json
{
  "status": "logged"
}
```

## Removed Integration

The project no longer posts through Facebook Graph API. Operators publish in
Facebook Web, then the app logs the resulting URL.
