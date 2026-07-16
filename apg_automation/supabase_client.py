from __future__ import annotations

import os


def build_supabase_client(
    *, url: str | None = None, service_role_key: str | None = None
):
    try:
        from supabase import create_client, ClientOptions
    except ImportError:
        # Fallback for older supabase package versions
        from supabase import Client, ClientOptions

        def create_client(url, key, options=None):
            return Client(url, key, options=options)  # type: ignore

    url = url or os.getenv("SUPABASE_URL", "")
    key = service_role_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required for live mode"
        )
    options = ClientOptions(
        storage_client_timeout=15,
        postgrest_client_timeout=15,
        schema="public",
    )
    return create_client(url, key, options=options)
