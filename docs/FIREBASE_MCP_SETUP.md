# Firebase MCP Setup Checklist

Use the official Firebase MCP server for project setup and live Firestore/Auth
inspection once it is exposed in the Codex tool list.

## Auth

1. Select or create the Firebase project for APG Posting Desk.
   - Current project: `apg-posting-desk-deign-2026`
2. Enable Authentication.
3. Enable Google provider.
4. Add authorized domains for local/dev access:
   - `localhost`
   - the LAN host/IP used by operators during testing
5. Create the web app config and copy these values into `.env`:
   - `VITE_FIREBASE_API_KEY=AIzaSyAPHFreROsT2nsIPrCZxfEepesGejG6EIY`
   - `VITE_FIREBASE_AUTH_DOMAIN=apg-posting-desk-deign-2026.firebaseapp.com`
   - `VITE_FIREBASE_PROJECT_ID=apg-posting-desk-deign-2026`
   - `VITE_FIREBASE_APP_ID=1:676310407748:web:9ab12f1c0ebcab17fbba11`
6. Set `VITE_APG_GOOGLE_DOMAIN` to the APG Workspace hosted domain (optional — leave blank for normal existing Google accounts).

## Firestore

1. Enable Firestore.
2. Create collection `property_queue`.
3. Seed documents like:

```json
{
  "property_name": "Novaliches, 440 Bagbag",
  "status": "pending",
  "assigned_at": "server timestamp",
  "assigned_by": "maam-jean"
}
```

4. Use Firebase MCP to inspect queue state:
   - list projects
   - select APG project
   - query `property_queue` where `status == "pending"`
   - verify operators can claim next property

## Backend Admin

The backend uses Firebase Admin Application Default Credentials. For local
development, use:

```powershell
gcloud auth application-default login
```

or provide the service account JSON through:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="path/to/firebase-service-account.json"
```
