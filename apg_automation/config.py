from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class GoogleDriveConfig:
    listings_folder_id: str


@dataclass(frozen=True)
class TrackingConfig:
    posting_tracker_sheet_id: str
    daily_report_doc_id: str


@dataclass(frozen=True)
class SupabaseConfig:
    url: str = ""
    service_role_key: str = ""
    anon_key: str = ""


@dataclass(frozen=True)
class ProcessingConfig:
    min_images: int = 3
    max_retries: int = 3
    batch_size: int = 5
    concurrent_tasks: int = 3


@dataclass(frozen=True)
class AIConfig:
    provider: str = "nvidia-nim"
    model: str = "stepfun-ai/step-3.7-flash"


@dataclass(frozen=True)
class AppConfig:
    google_drive: GoogleDriveConfig
    tracking: TrackingConfig
    supabase: SupabaseConfig = SupabaseConfig()
    processing: ProcessingConfig = ProcessingConfig()
    ai: AIConfig = AIConfig()
    posted_by: str = "APG Automation"
    timezone: str = "Asia/Manila"


def validate_runtime_config(config: AppConfig, *, dry_run: bool) -> None:
    if dry_run:
        return

    missing = []
    if not config.supabase.url:
        missing.append("SUPABASE_URL")
    if not config.supabase.service_role_key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")
    if not config.supabase.anon_key:
        missing.append("SUPABASE_ANON_KEY")

    provider_key = config.ai.provider.lower()
    if provider_key in {"nvidia", "nvidia-nim", "nim"}:
        if not os.getenv("NVIDIA_API_KEY", ""):
            missing.append("NVIDIA_API_KEY")
    elif provider_key == "openai":
        if not os.getenv("OPENAI_API_KEY", ""):
            missing.append("OPENAI_API_KEY")
    elif provider_key in {"anthropic", "claude"}:
        if not os.getenv("ANTHROPIC_API_KEY", ""):
            missing.append("ANTHROPIC_API_KEY")

    if missing:
        raise ValueError("Missing required environment variables: " + ", ".join(missing))


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    config_path = Path(path)
    data: dict[str, Any] = {}
    if config_path.exists():
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    return AppConfig(
        google_drive=GoogleDriveConfig(
            listings_folder_id=_value(
                data, "google_drive.listings_folder_id",
                "GOOGLE_DRIVE_LISTINGS_FOLDER_ID",
                "1GXeGULYswb7jXcMGCCRm2RQ_h0EKsDll",
            )
        ),
        tracking=TrackingConfig(
            posting_tracker_sheet_id=_value(
                data, "tracking.posting_tracker_sheet_id",
                "POSTING_TRACKER_SHEET_ID",
                "1xzzuq8KHbzrRIGMyIo0AQVgq0LQklDkW8-S9Y__7RvM",
            ),
            daily_report_doc_id=_value(
                data, "tracking.daily_report_doc_id",
                "DAILY_REPORT_DOC_ID",
                "1mctXkKFhZLCEXQtnzO4dmHhUSGOKFdFliF_qL17U68o",
            ),
        ),
        supabase=SupabaseConfig(
            url=_value(data, "supabase.url", "SUPABASE_URL", ""),
            service_role_key=_value(data, "supabase.service_role_key", "SUPABASE_SERVICE_ROLE_KEY", ""),
            anon_key=_value(data, "supabase.anon_key", "SUPABASE_ANON_KEY", ""),
        ),
        processing=ProcessingConfig(
            min_images=int(_value(data, "processing.min_images", "MIN_IMAGES", 3)),
            max_retries=int(_value(data, "processing.max_retries", "MAX_RETRIES", 3)),
            batch_size=int(_value(data, "processing.batch_size", "BATCH_SIZE", 5)),
            concurrent_tasks=int(_value(data, "processing.concurrent_tasks", "CONCURRENT_TASKS", 3)),
        ),
        ai=AIConfig(
            provider=_value(data, "ai.provider", "AI_PROVIDER", "nvidia-nim"),
            model=_value(data, "ai.model", "AI_MODEL", "stepfun-ai/step-3.7-flash"),
        ),
        posted_by=_value(data, "posted_by", "POSTED_BY", "APG Automation"),
        timezone=_value(data, "timezone", "TIMEZONE", "Asia/Manila"),
    )


def _value(data: dict[str, Any], dotted_key: str, env_key: str, default: Any) -> Any:
    if env_key in os.environ and os.environ[env_key] != "":
        return os.environ[env_key]
    current: Any = data
    for key in dotted_key.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current
