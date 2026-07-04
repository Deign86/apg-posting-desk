# Auth Redesign: Firebase Email/Password Login, Admin-Created Accounts

## Goal

Keep Firebase Auth, but remove Google OAuth popup sign-in. Replace it with email/password login. Accounts are created by admin only; there is no public signup.

## Constraints

- Demo mode must still start without live Firebase credentials.
- Existing role-based access (`admin`, `maam_deign`, `user`) must be preserved.
- Keep changes local to the auth layer; do not refactor unrelated pipeline behavior.

## Architecture

### Backend

**Firebase Auth (kept)**
- Continue using Firebase Auth for identity.
- Keep `FirebaseTokenVerifier` in `apg_automation/firebase_auth.py` for ID token verification.
- Remove Google OAuth provider configuration and hosted-domain restrictions.

**Admin-created accounts**
- Use Firebase Admin SDK (`firebase_auth.create_user`) to create users with email/password.
- Admin assigns roles via custom claims (`/api/admin/set-role`) or a role field in Firestore.
- No public signup endpoint or self-service account creation.

**Session auth**
- Keep session endpoint `/api/session`; verify Firebase ID token from the frontend.
- Remove Google OAuth callback flow and domain hints.

### Frontend

- Keep Firebase client initialization, but remove Google Auth Provider and `signInWithPopup`.
- Replace with email/password sign-in form (`signInWithEmailAndPassword`).
- Add sign-out using `signOut`.
- Remove hosted-domain restrictions and Google OAuth UI.

### Auth boundary

Demo mode: no Firebase config required; existing demo-role fallback preserved.

Live mode: email/password login required; admin creates all accounts via admin tools.

## Data flow

```
Frontend                        Backend
---------                       -------
Admin creates user  --->  Firebase Admin SDK createUser()
                                   setCustomClaims(role)
User submits email/password ---> signInWithEmailAndPassword()
                                   Firebase returns ID token
                                   Frontend stores token in memory
Subsequent requests  --->  Authorization: Bearer <ID token>
                             backend verifies token
                             401 if missing/invalid
Logout             --->  signOut()
                                   clear local token
```

## Admin account creation

- Admin-only route `POST /api/admin/users` uses Firebase Admin SDK to create user with `email` and `password`.
- Admin assigns role via custom claim or Firestore user document.
- Seed script can bootstrap admin accounts using service-account credentials.

## Password reset

- Firebase handles email-based password reset natively (`sendPasswordResetEmail`) if desired.
- Admin can also reset passwords via Admin SDK.

## Not in scope

- Google OAuth or other OAuth providers.
- Multi-factor auth.
- Self-service signup or account creation.

## Risks

- Firebase project quota and abuse protection (email/password sign-in is standard but may need reCAPTCHA if public, but no public signup here so lower risk).
- Admin credential management for Firebase Admin SDK.
