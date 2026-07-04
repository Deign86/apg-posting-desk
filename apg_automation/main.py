from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from .ai_clients import build_ai_client
from .caption_generator import CaptionGenerator
from .config import load_config, validate_runtime_config
from .google_drive import GoogleDriveRepository, build_drive_service
from .google_tracking import GoogleDocsClient, GoogleSheetsClient, build_docs_service, build_sheets_service
from .local_folder import LocalFolderRepository
from .logging_config import configure_logging
from .queue_manager import QueueManager
from .tracker_updater import TrackerUpdater
from .web_app import create_app


class DemoCaptionGenerator:
    def generate(self, caption_details: str):
        from .caption_generator import CaptionReview

        safe_details = caption_details.replace("least term", "lease terms").replace(
            "negotiables", "terms",
        )
        return CaptionReview(
            "Property listing prepared for manual posting.\n\n" + safe_details.strip()
        )


class ConsoleTracker:
    def record_success(self, property_name, post_url, posted_at):
        print(f"LOGGED {posted_at:%Y-%m-%d %H:%M} | {property_name} | {post_url}")


def parse_property_names(args: argparse.Namespace) -> list[str]:
    names: list[str] = []
    if args.properties:
        names.extend(args.properties)
    if args.properties_file:
        lines = Path(args.properties_file).read_text(encoding="utf-8").splitlines()
        names.extend(line.strip() for line in lines if line.strip())
    if not names and args.local_folder:
        names.append(Path(args.local_folder).name)
    return names


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="APG property posting automation")
    parser.add_argument("properties", nargs="*", help="Property names to process")
    parser.add_argument("--properties-file", help="Text file with one property per line")
    parser.add_argument("--local-folder", help="Use a local property folder as the source")
    parser.add_argument("--config", default="config.yaml", help="Config YAML path")
    parser.add_argument("--host", default="0.0.0.0", help="PWA server host")
    parser.add_argument("--port", default=8000, type=int, help="PWA server port")
    parser.add_argument("--dry-run", action="store_true", help="Validate property queue without generating captions or logging")
    parser.add_argument("--serve", action="store_true", help="Start the PWA server")
    parser.add_argument("--demo", action="store_true", help="Start the PWA with local source and no external credentials")
    return parser


def main() -> int:
    load_dotenv()
    configure_logging()

    args = build_parser().parse_args()
    property_names = parse_property_names(args)
    config = load_config(args.config)
    if not args.demo:
        try:
            validate_runtime_config(config, dry_run=args.dry_run)
        except ValueError as error:
            print(error)
            return 2

    if args.demo:
        local_folder = args.local_folder or "Novaliches, 440 Bagbag"
        drive = LocalFolderRepository(local_folder)
    elif args.local_folder:
        drive = LocalFolderRepository(args.local_folder)
    else:
        drive = GoogleDriveRepository(
            service=build_drive_service(),
            listings_folder_id=config.google_drive.listings_folder_id,
        )
    if args.dry_run:
        if not property_names:
            print("No property names supplied")
            return 2
        result = QueueManager(
            drive=drive,
            min_images=config.processing.min_images,
        ).build_queue(property_names)
        for property_name, error in result.errors.items():
            print(f"{property_name} skipped: {error}")
        for item in result.ready:
            print(f"{item.property_name} ready for processing from folder {item.folder_id}")
        return 0 if not result.errors else 1

    if not args.serve:
        print("Use --serve to start the PWA or --dry-run to validate properties.")
        return 2

    if args.demo:
        caption_generator = DemoCaptionGenerator()
        tracker = ConsoleTracker()
        auth_verifier = None
        queue = None
        job_store = None
        auth_required = False
    else:
        from .supabase_client import build_supabase_client
        from .supabase_auth import SupabaseTokenVerifier
        from .supabase_job_store import SupabaseJobStore
        from .supabase_queue import SupabasePropertyQueue
        from .supabase_tracking import SupabaseTracker

        supabase_client = build_supabase_client(
            url=config.supabase.url,
            service_role_key=config.supabase.service_role_key,
        )
        caption_generator = CaptionGenerator(
            client=build_ai_client(config.ai.provider, config.ai.model),
            max_retries=config.processing.max_retries,
        )
        tracker = TrackerUpdater(
            sheets_client=GoogleSheetsClient(service=build_sheets_service()),
            docs_client=GoogleDocsClient(service=build_docs_service()),
            posting_tracker_sheet_id=config.tracking.posting_tracker_sheet_id,
            daily_report_doc_id=config.tracking.daily_report_doc_id,
            posted_by=config.posted_by,
        )
        auth_verifier = SupabaseTokenVerifier(client=supabase_client)
        queue = SupabasePropertyQueue(supabase_client)
        job_store = SupabaseJobStore(supabase_client)
        auth_required = True
        # Auto-seed accounts on startup so email/password login works immediately
        try:
            result = auth_verifier.seed_accounts()
            print(f"Seeded {result['seeded']} account(s): {', '.join(result['accounts'])}")
        except Exception as exc:
            print(f"Seed skipped (accounts may already exist): {exc}")
    app = create_app(
        drive=drive,
        caption_generator=caption_generator,
        tracker=tracker,
        auth_verifier=auth_verifier,
        queue=queue,
        job_store=job_store,
        auth_required=auth_required,
        download_root=Path("downloads"),
    )
    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
