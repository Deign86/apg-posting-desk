from __future__ import annotations

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

    It reads configuration from env (via load_config which already respects
    environment variables over config.yaml defaults) and wires all Supabase
    adapters: auth, queue, job store, asset repository, and tracking.
    """
    from .asset_service import AssetService
    from .supabase_assets import SupabaseAssetRepository
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

    # -- Supabase-backed services --
    _tracker = SupabaseTracker(_supabase, posted_by=config.posted_by)
    _auth_verifier = SupabaseTokenVerifier(client=_supabase)
    _queue = SupabasePropertyQueue(_supabase)
    _job_store = SupabaseJobStore(_supabase)

    # -- Canonical asset service + repository (no Google Drive) --
    _asset_service = AssetService.from_config(config)
    _drive = SupabaseAssetRepository(
        _supabase,
        bucket_private=config.storage.bucket_private,
        bucket_public=config.storage.bucket_public,
        signed_url_ttl=config.storage.signed_url_ttl_seconds,
        min_images=config.processing.min_images,
    )

    # Serverless /tmp is the only writable filesystem, and nothing persists
    # across invocations — the prepared images go straight to Storage as signed
    # URLs, so download_root is only needed for transient pipeline workspace.
    _download_root = Path("/tmp/apg-prepared")

    app = create_app(
        drive=_drive,
        caption_generator=_caption_generator,
        tracker=_tracker,
        auth_verifier=_auth_verifier,
        queue=_queue,
        job_store=_job_store,
        asset_service=_asset_service,
        auth_required=True,
        download_root=_download_root,
    )
    return app
