from __future__ import annotations

import os


def build_supabase_client(
    *, url: str | None = None, service_role_key: str | None = None
):
    from supabase import create_client  # lazy import

    url = url or os.getenv("SUPABASE_URL", "")
    key = service_role_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required for live mode"
        )
    return create_client(url, key)
