from __future__ import annotations

import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv

from .ai_clients import build_ai_client
from .caption_generator import CaptionGenerator
from .config import load_config
from .web_app import create_app


def build_live_app() -> "FastAPI":
    """Build and return a Supabase-backed FastAPI app for serverless deployment.

    Unlike main.main(), this does NOT:
      - start uvicorn
      - seed seed_accounts()
      - probe NVIDIA NIM reachability at module load
      - accept CLI arguments

    Reads configuration from env and wires all Supabase adapters.
    Catches and exposes startup errors so the Vercel function returns a
    descriptive message instead of a generic FUNCTION_INVOCATION_FAILED.
    """
    from fastapi import FastAPI, Request
    from fastapi.responses import PlainTextResponse

    try:
        return _build_app()
    except Exception as exc:
        tb = traceback.format_exc()
        _init_error = str(exc)

        app = FastAPI(title="APG Review Dashboard (ERROR)")

        @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
        async def error_handler(path: str):
            return PlainTextResponse(
                f"Startup error: {_init_error}\n\nTraceback:\n{tb}",
                status_code=500,
            )

        return app


def _build_app():
    from .google_drive import GoogleDriveRepository, build_drive_service
    from .supabase_auth import SupabaseTokenVerifier
    from .supabase_client import build_supabase_client
    from .supabase_job_store import SupabaseJobStore
    from .supabase_queue import SupabasePropertyQueue
    from .supabase_tracking import SupabaseTracker

    load_dotenv()
    config = load_config()

    _supabase = build_supabase_client(
        url=config.supabase.url,
        service_role_key=config.supabase.service_role_key,
    )

    # -- AI caption generator --
    _ai_client = build_ai_client(config.ai.provider, config.ai.model)
    _caption_generator = CaptionGenerator(
        client=_ai_client,
        max_retries=config.processing.max_retries,
    )

    # -- Supabase-backed services (auth, queue, jobs, tracking) --
    _tracker = SupabaseTracker(_supabase, posted_by=config.posted_by)
    _auth_verifier = SupabaseTokenVerifier(client=_supabase)
    _queue = SupabasePropertyQueue(_supabase)
    _job_store = SupabaseJobStore(_supabase)

    # -- Google Drive as the single source of truth for property assets --
    _drive = GoogleDriveRepository(
        service=build_drive_service(),
        listings_folder_id=config.google_drive.listings_folder_id,
    )

    # Serverless /tmp is the only writable filesystem
    _download_root = Path("/tmp/apg-prepared")

    app = create_app(
        drive=_drive,
        caption_generator=_caption_generator,
        tracker=_tracker,
        auth_verifier=_auth_verifier,
        queue=_queue,
        job_store=_job_store,
        auth_required=True,
        download_root=_download_root,
    )
    return app
