from __future__ import annotations

from collections.abc import Callable, Mapping

from fastapi import Depends, Header, HTTPException

FirebaseUser = dict[str, str]


class FirebaseTokenVerifier:
    def __init__(self, *, firebase_auth=None) -> None:
        if firebase_auth is None:
            import firebase_admin
            from firebase_admin import auth, credentials

            if not firebase_admin._apps:
                firebase_admin.initialize_app(credentials.ApplicationDefault())
            firebase_auth = auth
        self.firebase_auth = firebase_auth

    def verify(self, token: str) -> Mapping[str, object]:
        return self.firebase_auth.verify_id_token(token)


def _claim_text(claims: Mapping[str, object], key: str) -> str:
    value = claims.get(key)
    return value if isinstance(value, str) else ""


def _normalize_claims(claims: Mapping[str, object]) -> FirebaseUser:
    uid = _claim_text(claims, "uid")
    email = _claim_text(claims, "email")
    display_name = (
        _claim_text(claims, "display_name")
        or _claim_text(claims, "name")
        or email
        or uid
    )
    return {
        "uid": uid,
        "email": email,
        "role": _claim_text(claims, "role") or "user",
        "display_name": display_name,
    }


def require_firebase_user(verifier: FirebaseTokenVerifier) -> Callable[..., FirebaseUser]:
    def dep(
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> FirebaseUser:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Firebase ID token")
        token = authorization.removeprefix("Bearer ").strip()
        try:
            return _normalize_claims(verifier.verify(token))
        except Exception as err:
            raise HTTPException(status_code=401, detail="Invalid Firebase ID token") from err

    return dep


def require_role(
    *roles: str,
    user_dependency: Callable[..., FirebaseUser] | None = None,
) -> Callable[..., FirebaseUser]:
    def dep(user: FirebaseUser = Depends(user_dependency)) -> FirebaseUser:
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return dep
