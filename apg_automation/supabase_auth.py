from __future__ import annotations

from collections.abc import Callable

from .auth_deps import require_role
from .supabase_client import build_supabase_client

TokenVerifierProtocol = Callable[..., dict]


class SupabaseTokenVerifier:
    def __init__(self, *, client=None) -> None:
        if client is None:
            client = build_supabase_client()
        self.client = client

    def verify(self, token: str) -> dict:
        from supabase import Client  # lazy

        if not isinstance(self.client, Client):
            self.client = build_supabase_client()
        user = self.client.auth.get_user(token)
        uid = user.user.id
        email = user.user.email or ""
        profile = (
            self.client.table("profiles")
            .select("role,display_name")
            .eq("id", uid)
            .limit(1)
            .execute()
        )
        rows = profile.data if profile and profile.data else []
        if rows:
            role = rows[0].get("role", "user")
            display_name = rows[0].get("display_name", "") or email or uid
        else:
            role = "user"
            display_name = email or uid
        return {
            "uid": uid,
            "email": email,
            "role": role,
            "display_name": display_name,
        }

    def create_user(
        self,
        *,
        email: str,
        password: str,
        role: str,
        display_name: str | None = None,
    ) -> dict:
        from supabase import Client

        if not isinstance(self.client, Client):
            self.client = build_supabase_client()
        user = self.client.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
            }
        )
        uid = user.user.id
        dn = display_name or email.split("@")[0]
        self.client.table("profiles").upsert(
            {"id": uid, "email": email, "display_name": dn, "role": role}
        ).execute()
        return {"uid": uid, "email": email, "role": role, "display_name": dn}

    def set_role(self, *, uid: str, role: str) -> dict:
        self.client.table("profiles").update({"role": role}).eq("id", uid).execute()
        return {"uid": uid, "role": role, "status": "updated"}

    def list_users(self) -> list[dict]:
        users = self.client.auth.admin.list_users()
        results = []
        for u in users:
            profile = (
                self.client.table("profiles")
                .select("role,display_name")
                .eq("id", u.id)
                .limit(1)
                .execute()
            )
            row = profile.data[0] if profile.data else {}
            results.append(
                {
                    "uid": u.id,
                    "email": u.email or "",
                    "role": row.get("role", "user"),
                    "display_name": row.get("display_name", u.email or u.id),
                }
            )
        return results

    def seed_accounts(self) -> dict:
        seeds = [
            ("admin@apg.local", "admin@123", "admin", "Admin"),
            ("operator@apg.local", "oper@123", "user", "Operator"),
        ]
        created = 0
        for email, pw, role, dn in seeds:
            try:
                self.create_user(email=email, password=pw, role=role, display_name=dn)
                created += 1
            except Exception:
                pass
        return {"seeded": created, "accounts": [s[0] for s in seeds]}


def require_supabase_user(
    verifier: SupabaseTokenVerifier,
) -> Callable:
    from fastapi import Header, HTTPException

    def dep(
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> dict:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing access token")
        token = authorization.removeprefix("Bearer ").strip()
        try:
            return verifier.verify(token)
        except Exception as err:
            raise HTTPException(status_code=401, detail="Invalid access token") from err

    return dep
