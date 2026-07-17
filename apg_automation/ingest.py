from __future__ import annotations

"""Import pipeline: walks APR LISTING into the shared Supabase canonical model.

The source can be a local Windows folder (--source) or Google Drive (--source-drive).
The Windows folder is ONLY an import source; Supabase is the live system of record.
Writes: categories, transaction_types, offerings, raw_folder_mappings, assets,
property_asset_relations, property_asset_versions, import_batches, import_file_mappings.
Storage: `config.storage.bucket_listings` (default `offerings`) using nested keys:
properties/{offering_id}/images/{asset_id}/original.{ext}
properties/{offering_id}/documents/{asset_id}/original.{ext}
`apg-private` is available via `config.storage.bucket_private` for staff-only signed-URL paths.
Idempotent: sha256 dedup + slug upsert + unique raw_folder_path.
"""

import argparse
import hashlib
import re
import uuid
import io
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from .config import load_config
from .folder_parser import (
    parse_property_folder_name,
    classify_category,
    classify_transaction_type,
    is_property_folder,
    is_property_folder_name,
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_DOCUMENT_EXTENSIONS,
)
from .supabase_client import build_supabase_client


def _sha256(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def _ext(filename: str) -> str:
    return Path(filename).suffix.lower()


def _mime_for(suffix: str) -> str:
    s = suffix.lower()
    if s in (".jpg", ".jpeg"):
        return "image/jpeg"
    if s == ".png":
        return "image/png"
    if s == ".pdf":
        return "application/pdf"
    if s == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if s == ".txt":
        return "text/plain"
    return "application/octet-stream"


def _image_dims(file_bytes: bytes) -> tuple[int, int]:
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(file_bytes))
        return img.size
    except Exception:
        return 0, 0


def _to_sqm(s: str) -> float | None:
    if not s:
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def _upsert_category(client, name: str, parent_id: str | None = None) -> str:
    slug = re.sub(r"-+", "-", name.lower().replace(" ", "-").replace("_", "-")).strip("-")
    payload = {"name": name, "slug": slug}
    if parent_id:
        payload["parent_id"] = parent_id
    res = client.table("categories").upsert(payload, on_conflict="name").select("id").execute()
    return res.data[0]["id"] if res and res.data else ""


def _upsert_transaction_type(client, name: str) -> str:
    res = client.table("transaction_types").upsert({"name": name}, on_conflict="name").select("id").execute()
    return res.data[0]["id"] if res and res.data else ""


def _asset_ids_for_offering(client, offering_id: str) -> list[str]:
    res = client.table("property_asset_relations").select("asset_id").eq("offering_id", offering_id).execute()
    return [r["asset_id"] for r in (res.data or [])]


def _dedup_asset_id(client, offering_id: str, sha: str) -> str | None:
    aids = _asset_ids_for_offering(client, offering_id)
    if not aids:
        return None
    res = (
        client.table("property_asset_versions")
        .select("asset_id").eq("sha256", sha).in_("asset_id", aids).limit(1).execute()
    )
    return res.data[0]["asset_id"] if res and res.data else None


def _get_or_create_offering(client, parsed: dict, category_id: str, txn_id: str, source_path: str, batch_id: str) -> str:
    res = client.table("offerings").select("id").eq("slug", parsed["slug"]).limit(1).execute()
    if res and res.data:
        return res.data[0]["id"]
    offering_id = str(uuid.uuid4())
    city = parsed.get("location_city", "")
    area = parsed.get("location_area", "")
    location_label = ", ".join(p for p in (city, area) if p)
    result = client.table("offerings").upsert({
        "title": parsed["normalized_title"],
        "slug": parsed["slug"],
        "location": city or None,
        "category_id": category_id or None,
        "transaction_type_id": txn_id or None,
        "raw_folder_name": parsed.get("raw_title", ""),
        "raw_folder_path": source_path,
        "normalized_title": parsed["normalized_title"],
        "location_label": location_label or None,
        "approximate_area_sqm": _to_sqm(parsed.get("size_sqm", "")),
        "parse_confidence": parsed.get("parse_confidence", "high"),
        "parse_errors": parsed.get("errors", []),
        "import_batch_id": batch_id,
        "status": "available",
        "is_published": False,
    }, on_conflict="slug").select("id").execute()
    return str(result.data[0]["id"]) if result and result.data else ""


def _import_file(client, offering_id: str, file_path: Path, bucket: str, kind: str, dry_run: bool, batch_id: str, display_order: int) -> dict:
    file_bytes = file_path.read_bytes()
    h = _sha256(file_bytes)
    fn = file_path.name
    size = len(file_bytes)
    suffix = _ext(fn)
    mime = _mime_for(suffix)

    if not dry_run:
        existing = _dedup_asset_id(client, offering_id, h)
        if existing:
            client.table("import_file_mappings").insert({
                "import_batch_id": batch_id, "source_path": str(file_path),
                "source_filename": fn, "source_folder": file_path.parent.name,
                "file_size_bytes": size, "mime_type": mime, "checksum_sha256": h,
                "asset_id": existing, "status": "skipped_duplicate",
                "processed_at": datetime.utcnow().isoformat(),
            }).execute()
            return {"status": "skipped", "asset_id": existing, "sha256": h}
    if dry_run:
        return {"status": "would_upload", "sha256": h, "filename": fn}

    asset_id = str(uuid.uuid4())
    sub = "images" if kind == "image" else "documents"
    object_path = f"properties/{offering_id}/{sub}/{asset_id}/original{suffix or ''}"
    width, height = _image_dims(file_bytes) if kind == "image" else (0, 0)

    client.storage.from_(bucket).upload(object_path, file_bytes, {"content-type": mime})

    asset_type = "image" if kind == "image" else "document"
    client.table("assets").insert({
        "id": asset_id, "asset_type": asset_type, "mime_type": mime,
        "size_bytes": size, "original_name": fn, "storage_path": object_path,
        "storage_bucket": bucket, "width": width, "height": height,
        "is_public": False, "ingestion_status": "pending_review",
        "current_version": 1, "import_batch_id": batch_id,
        "source_path": str(file_path),
    }).execute()

    gallery_role = "gallery" if kind == "image" else "brochure"
    client.table("property_asset_relations").insert({
        "offering_id": offering_id, "asset_id": asset_id,
        "gallery_role": gallery_role, "display_order": display_order,
        "is_cover": False, "alt_text": fn,
    }).execute()

    client.table("property_asset_versions").insert({
        "asset_id": asset_id, "version_number": 1, "storage_bucket": bucket,
        "object_path": object_path, "derivative_kind": "original",
        "width": width, "height": height, "size_bytes": size,
        "sha256": h, "is_current": True,
    }).execute()

    client.table("import_file_mappings").insert({
        "import_batch_id": batch_id, "source_path": str(file_path),
        "source_filename": fn, "source_folder": file_path.parent.name,
        "file_size_bytes": size, "mime_type": mime, "checksum_sha256": h,
        "asset_id": asset_id, "status": "uploaded",
        "processed_at": datetime.utcnow().isoformat(),
    }).execute()

    return {"status": "imported", "asset_id": asset_id, "sha256": h}


def _import_property_folder(client, folder_path: Path, category_id: str, txn_id: str, iteration_label: str, bucket: str, dry_run: bool, batch_id: str, source_root: Path) -> dict:
    parsed = parse_property_folder_name(folder_path.name)
    source_path = str(folder_path.relative_to(source_root))
    offering_id = ""
    if not dry_run:
        offering_id = _get_or_create_offering(client, parsed, category_id, txn_id, source_path, batch_id)
        client.table("raw_folder_mappings").upsert({
            "property_id": offering_id, "raw_folder_name": folder_path.name,
            "raw_folder_path": source_path, "category_id": category_id or None,
            "transaction_type_id": txn_id or None, "iteration_label": iteration_label or None,
            "parse_payload": parsed, "parse_confidence": parsed.get("parse_confidence", "high"),
            "parse_errors": parsed.get("errors", []), "import_batch_id": batch_id,
        }, on_conflict="raw_folder_path").execute()

    image_files = sorted([f for f in folder_path.iterdir() if f.is_file() and _ext(f.name) in SUPPORTED_IMAGE_EXTENSIONS])
    doc_files = sorted([f for f in folder_path.iterdir() if f.is_file() and _ext(f.name) in SUPPORTED_DOCUMENT_EXTENSIONS])
    results = []
    order = 0
    for f in image_files:
        results.append(_import_file(client, offering_id or "dry", f, bucket, "image", dry_run, batch_id, order))
        order += 1
    for f in doc_files:
        results.append(_import_file(client, offering_id or "dry", f, bucket, "document", dry_run, batch_id, order))
        order += 1

    imported = sum(1 for r in results if r["status"] == "imported")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    return {
        "property_name": folder_path.name, "offering_id": offering_id,
        "status": "ok" if not dry_run else "would_process",
        "parse_confidence": parsed.get("parse_confidence", "high"),
        "parse_errors": parsed.get("errors", []),
        "images": len(image_files), "documents": len(doc_files),
        "imported": imported, "skipped": skipped,
    }


def _walk_txn(client, txn_dir: Path, category_id: str, txn_id: str, bucket: str, dry_run: bool, batch_id: str, source_root: Path) -> list[dict]:
    results = []
    dirs_under = sorted([d for d in txn_dir.iterdir() if d.is_dir()])
    files_under = [f for f in txn_dir.iterdir() if f.is_file() and _ext(f.name) in SUPPORTED_IMAGE_EXTENSIONS]
    if files_under:
        results.append(_import_property_folder(client, txn_dir, category_id, txn_id, "", bucket, dry_run, batch_id, source_root))
        return results
    for sub_dir in dirs_under:
        if is_property_folder(sub_dir):
            results.append(_import_property_folder(client, sub_dir, category_id, txn_id, "", bucket, dry_run, batch_id, source_root))
        else:
            for prop_dir in sorted(sub_dir.iterdir()):
                if prop_dir.is_dir() and is_property_folder(prop_dir):
                    results.append(_import_property_folder(client, prop_dir, category_id, txn_id, "", bucket, dry_run, batch_id, source_root))
    return results


def _walk_sold(client, category_dir: Path, sold_cat_id: str, bucket: str, dry_run: bool, batch_id: str, source_root: Path) -> list[dict]:
    results = []
    for child in sorted(category_dir.iterdir()):
        if not child.is_dir():
            continue
        if is_property_folder(child):
            results.append(_import_property_folder(client, child, sold_cat_id, "", "", bucket, dry_run, batch_id, source_root))
        else:
            sub_cat_id = _upsert_category(client, child.name.upper(), parent_id=sold_cat_id) if not dry_run else ""
            for prop_dir in sorted(child.iterdir()):
                if prop_dir.is_dir() and is_property_folder(prop_dir):
                    results.append(_import_property_folder(client, prop_dir, sub_cat_id, "", "", bucket, dry_run, batch_id, source_root))
    return results


def _walk_virtual(client, category_dir: Path, virtual_cat_id: str, virtual_txn_id: str, bucket: str, dry_run: bool, batch_id: str, source_root: Path) -> list[dict]:
    results = []
    for iteration_dir in sorted(category_dir.iterdir()):
        if not iteration_dir.is_dir():
            continue
        for child in sorted(iteration_dir.iterdir()):
            if not child.is_dir():
                continue
            if is_property_folder(child):
                results.append(_import_property_folder(client, child, virtual_cat_id, virtual_txn_id, iteration_dir.name, bucket, dry_run, batch_id, source_root))
            else:
                for prop_dir in sorted(child.iterdir()):
                    if prop_dir.is_dir() and is_property_folder(prop_dir):
                        results.append(_import_property_folder(client, prop_dir, virtual_cat_id, virtual_txn_id, iteration_dir.name, bucket, dry_run, batch_id, source_root))
    return results


def _walk_and_import(client, source_root: Path, bucket: str, dry_run: bool, batch_id: str) -> list[dict]:
    results = []
    source_root = source_root.resolve()
    for category_dir in sorted(source_root.iterdir()):
        if not category_dir.is_dir():
            continue
        category_raw = category_dir.name
        cat_name, _ = classify_category(category_raw)
        txn_norm = classify_transaction_type(category_raw)
        cat_id = _upsert_category(client, cat_name) if not dry_run else ""
        if txn_norm == "sold":
            results += _walk_sold(client, category_dir, cat_id, bucket, dry_run, batch_id, source_root)
        elif txn_norm == "virtual":
            vtxn_id = _upsert_transaction_type(client, "virtual") if not dry_run else ""
            results += _walk_virtual(client, category_dir, cat_id, vtxn_id, bucket, dry_run, batch_id, source_root)
        else:
            for txn_dir in sorted(category_dir.iterdir()):
                if not txn_dir.is_dir():
                    continue
                txn_type = classify_transaction_type(txn_dir.name)
                txn_id = _upsert_transaction_type(client, txn_type) if not dry_run else ""
                results += _walk_txn(client, txn_dir, cat_id, txn_id, bucket, dry_run, batch_id, source_root)
    return results


def _verify(client, source_root: Path) -> int:
    """Compare Supabase contents against the folder; report missing/orphaned."""
    source_root = source_root.resolve()
    folder_props = set()
    for category_dir in sorted(source_root.iterdir()):
        if not category_dir.is_dir():
            continue
        for p in category_dir.rglob("*"):
            if p.is_dir() and is_property_folder(p):
                folder_props.add(str(p.relative_to(source_root)))
    res = client.table("raw_folder_mappings").select("raw_folder_path").execute()
    db_paths = {r["raw_folder_path"] for r in (res.data or [])}
    missing = sorted(folder_props - db_paths)
    orphaned = sorted(db_paths - folder_props)
    print(f"Verify: {len(folder_props)} property folders on disk, {len(db_paths)} in Supabase.")
    if missing:
        print(f"  Missing from Supabase ({len(missing)}):")
        for m in missing[:50]:
            print(f"    - {m}")
    if orphaned:
        print(f"  Orphaned in Supabase ({len(orphaned)}):")
        for o in orphaned[:50]:
            print(f"    - {o}")
    return 0 if not missing else 1



# ── Drive (Google Drive) source helpers ──
# These mirror the local-folder walk/import functions but use the Drive API.
# The core write path is shared; only the file enumeration and byte retrieval differ.


def _drive_list_subfolders(service, parent_id: str) -> list[dict]:
    """List immediate non-trashed subfolders of a Drive folder (paginated)."""
    items: list[dict] = []
    page_token = None
    while True:
        resp = service.files().list(
            q=f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="nextPageToken,files(id,name)",
            pageSize=1000,
            pageToken=page_token,
        ).execute()
        items.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items


def _drive_list_files(service, parent_id: str) -> list[dict]:
    """List non-folder, non-trashed items in a Drive folder (paginated)."""
    items: list[dict] = []
    page_token = None
    while True:
        resp = service.files().list(
            q=f"'{parent_id}' in parents and mimeType!='application/vnd.google-apps.folder' and trashed=false",
            fields="nextPageToken,files(id,name,mimeType,size)",
            pageSize=1000,
            pageToken=page_token,
        ).execute()
        items.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items


def _drive_download_bytes(service, file_id: str, mime_type: str) -> bytes:
    """Download a Drive file's full content as bytes."""
    if mime_type == "application/vnd.google-apps.document":
        request = service.files().export_media(fileId=file_id, mimeType="text/plain")
    else:
        request = service.files().get_media(fileId=file_id)
    try:
        return request.execute()
    except Exception:
        from googleapiclient.http import MediaIoBaseDownload
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buf.getvalue()


def _drive_import_file(
    client, service, offering_id: str, drive_file: dict,
    bucket: str, kind: str, dry_run: bool, batch_id: str, display_order: int,
) -> dict:
    """Download a single file from Drive, dedup, and write to Supabase."""
    fn = drive_file["name"]
    mime = drive_file.get("mimeType", "application/octet-stream")
    raw_mime = mime  # preserve original for download logic
    if mime == "application/vnd.google-apps.document":
        mime = "text/plain"
        fn = fn.rsplit(".", 1)[0] + ".txt"
    file_bytes = _drive_download_bytes(service, drive_file["id"], raw_mime)
    h = _sha256(file_bytes)
    size = len(file_bytes)

    if not dry_run:
        existing = _dedup_asset_id(client, offering_id, h)
        if existing:
            client.table("import_file_mappings").insert({
                "import_batch_id": batch_id, "source_path": drive_file["id"],
                "source_filename": fn, "source_folder": "",
                "file_size_bytes": size, "mime_type": mime, "checksum_sha256": h,
                "asset_id": existing, "status": "skipped_duplicate",
                "processed_at": datetime.utcnow().isoformat(),
            }).execute()
            return {"status": "skipped", "asset_id": existing, "sha256": h, "filename": fn}
    if dry_run:
        return {"status": "would_upload", "sha256": h, "filename": fn}

    asset_id = str(uuid.uuid4())
    suffix = _ext(fn)
    sub = "images" if kind == "image" else "documents"
    object_path = f"properties/{offering_id}/{sub}/{asset_id}/original{suffix or ''}"
    width, height = _image_dims(file_bytes) if kind == "image" else (0, 0)

    time.sleep(0.1)  # rate-limit Drive API pacing
    client.storage.from_(bucket).upload(object_path, file_bytes, {"content-type": mime})

    asset_type = "image" if kind == "image" else "document"
    client.table("assets").insert({
        "id": asset_id, "asset_type": asset_type, "mime_type": mime,
        "size_bytes": size, "original_name": fn, "storage_path": object_path,
        "storage_bucket": bucket, "width": width, "height": height,
        "is_public": False, "ingestion_status": "pending_review",
        "current_version": 1, "import_batch_id": batch_id,
        "source_path": drive_file["id"],
    }).execute()

    gallery_role = "gallery" if kind == "image" else "brochure"
    client.table("property_asset_relations").insert({
        "offering_id": offering_id, "asset_id": asset_id,
        "gallery_role": gallery_role, "display_order": display_order,
        "is_cover": False, "alt_text": fn,
    }).execute()
    client.table("property_asset_versions").insert({
        "asset_id": asset_id, "version_number": 1, "storage_bucket": bucket,
        "object_path": object_path, "derivative_kind": "original",
        "width": width, "height": height, "size_bytes": size,
        "sha256": h, "is_current": True,
    }).execute()
    client.table("import_file_mappings").insert({
        "import_batch_id": batch_id, "source_path": drive_file["id"],
        "source_filename": fn, "source_folder": "",
        "file_size_bytes": size, "mime_type": mime, "checksum_sha256": h,
        "asset_id": asset_id, "status": "uploaded",
        "processed_at": datetime.utcnow().isoformat(),
    }).execute()
    return {"status": "imported", "asset_id": asset_id, "sha256": h}


def _drive_import_property_folder(
    client, service, folder_id: str, folder_name: str,
    category_id: str, txn_id: str, bucket: str, dry_run: bool, batch_id: str,
) -> dict:
    """Import one property folder from Drive (files within a Drive folder)."""
    parsed = parse_property_folder_name(folder_name)
    source_path = folder_name
    offering_id = ""
    if not dry_run:
        offering_id = _get_or_create_offering(client, parsed, category_id, txn_id, source_path, batch_id)
        client.table("raw_folder_mappings").upsert({
            "property_id": offering_id, "raw_folder_name": folder_name,
            "raw_folder_path": source_path, "category_id": category_id or None,
            "transaction_type_id": txn_id or None, "iteration_label": None,
            "parse_payload": parsed, "parse_confidence": parsed.get("parse_confidence", "high"),
            "parse_errors": parsed.get("errors", []), "import_batch_id": batch_id,
        }, on_conflict="raw_folder_path").execute()

    files = _drive_list_files(service, folder_id)
    image_files = [f for f in files if f.get("mimeType", "").startswith("image/")]
    doc_files = [f for f in files if f.get("mimeType") in (
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/vnd.google-apps.document",
    )]

    results = []
    order = 0
    for f in image_files:
        results.append(_drive_import_file(client, service, offering_id or "dry", f, bucket, "image", dry_run, batch_id, order))
        order += 1
    for f in doc_files:
        results.append(_drive_import_file(client, service, offering_id or "dry", f, bucket, "document", dry_run, batch_id, order))
        order += 1

    imported = sum(1 for r in results if r["status"] == "imported")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    return {
        "property_name": folder_name, "offering_id": offering_id,
        "status": "ok" if not dry_run else "would_process",
        "parse_confidence": parsed.get("parse_confidence", "high"),
        "parse_errors": parsed.get("errors", []),
        "images": len(image_files), "documents": len(doc_files),
        "imported": imported, "skipped": skipped,
    }


def _drive_walk_properties(
    client, service, txn_folder: dict,
    category_id: str, txn_id: str, bucket: str, dry_run: bool, batch_id: str,
) -> list[dict]:
    """Walk a transaction-level Drive folder and import each property subfolder."""
    results = []
    for sub in _drive_list_subfolders(service, txn_folder["id"]):
        if is_property_folder_name(sub["name"]):
            results.append(_drive_import_property_folder(
                client, service, sub["id"], sub["name"],
                category_id, txn_id, bucket, dry_run, batch_id,
            ))
    return results


def _drive_walk_sold(
    client, service, cat_folder: dict,
    cat_id: str, bucket: str, dry_run: bool, batch_id: str,
) -> list[dict]:
    """Walk SOLD-category Drive folder: property folders at the category level."""
    results = []
    for child in _drive_list_subfolders(service, cat_folder["id"]):
        if is_property_folder_name(child["name"]):
            results.append(_drive_import_property_folder(
                client, service, child["id"], child["name"],
                cat_id, "", bucket, dry_run, batch_id,
            ))
    return results


def _drive_walk_virtual(
    client, service, cat_folder: dict,
    cat_id: str, vtxn_id: str, bucket: str, dry_run: bool, batch_id: str,
) -> list[dict]:
    """Walk Virtual Office category Drive folder (one nesting level)."""
    results = []
    for child in _drive_list_subfolders(service, cat_folder["id"]):
        if is_property_folder_name(child["name"]):
            results.append(_drive_import_property_folder(
                client, service, child["id"], child["name"],
                cat_id, vtxn_id, bucket, dry_run, batch_id,
            ))
    return results


def _drive_walk_and_import(
    client, service, root_folder_id: str,
    bucket: str, dry_run: bool, batch_id: str,
) -> list[dict]:
    """Top-level Drive tree walk: classify categories + types, dispatch."""
    results: list[dict] = []
    for cat_folder in _drive_list_subfolders(service, root_folder_id):
        category_raw = cat_folder["name"]
        cat_name, _ = classify_category(category_raw)
        cat_id = _upsert_category(client, cat_name) if not dry_run else ""
        txn_norm = classify_transaction_type(category_raw)
        if txn_norm == "sold":
            results += _drive_walk_sold(client, service, cat_folder, cat_id, bucket, dry_run, batch_id)
        elif txn_norm == "virtual":
            vtxn_id = _upsert_transaction_type(client, "virtual") if not dry_run else ""
            results += _drive_walk_virtual(client, service, cat_folder, cat_id, vtxn_id, bucket, dry_run, batch_id)
        else:
            for txn_folder in _drive_list_subfolders(service, cat_folder["id"]):
                txn_type = classify_transaction_type(txn_folder["name"])
                txn_id = _upsert_transaction_type(client, txn_type) if not dry_run else ""
                results += _drive_walk_properties(client, service, txn_folder, cat_id, txn_id, bucket, dry_run, batch_id)
    return results


def _drive_verify(client, service, root_folder_id: str) -> int:
    """Compare Drive folder tree against Supabase raw_folder_mappings."""
    folder_props: set[str] = set()

    def _walk(fid, prefix=""):
        for sub in _drive_list_subfolders(service, fid):
            name = sub["name"]
            rel = f"{prefix}/{name}" if prefix else name
            if is_property_folder_name(name):
                folder_props.add(rel)
            _walk(sub["id"], rel)
    _walk(root_folder_id)
    res = client.table("raw_folder_mappings").select("raw_folder_path").execute()
    db_paths = {r["raw_folder_path"] for r in (res.data or [])}
    missing = sorted(folder_props - db_paths)
    orphaned = sorted(db_paths - folder_props)
    print(f"Verify (Drive): {len(folder_props)} property folders on Drive, {len(db_paths)} in Supabase.")
    if missing:
        print(f"  Missing from Supabase ({len(missing)}):")
        for m in missing[:50]:
            print(f"    - {m}")
    if orphaned:
        print(f"  Orphaned in Supabase ({len(orphaned)}):")
        for o in orphaned[:50]:
            print(f"    - {o}")
    return 0 if not missing else 1


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Import APR LISTING into the shared Supabase canonical model")
    parser.add_argument("--source", required=False, help="Path to APR LISTING root folder (mutually exclusive with --source-drive)")
    parser.add_argument("--source-drive", action="store_true", help="Import from Google Drive instead of a local folder (uses config.google_drive.listings_folder_id)")
    parser.add_argument("--dry-run", action="store_true", help="Walk and report without writing")
    parser.add_argument("--verify", action="store_true", help="Compare Supabase contents against the source")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    config = load_config(args.config)

    if not args.source and not args.source_drive:
        print("ERROR: specify --source <path> or --source-drive")
        return 2
    if args.source and args.source_drive:
        print("ERROR: --source and --source-drive are mutually exclusive")
        return 2

    bucket = config.storage.bucket_listings
    source_label = args.source or "Drive"

    client = build_supabase_client(url=config.supabase.url, service_role_key=config.supabase.service_role_key)

    # ── Drive source ──
    if args.source_drive:
        from .google_drive import build_drive_service
        service = build_drive_service()
        root_id = config.google_drive.listings_folder_id
        if not root_id:
            print("ERROR: google_drive.listings_folder_id not configured")
            return 2

        if args.verify:
            return _drive_verify(client, service, root_id)

        batch_id = str(uuid.uuid4())
        print(f"Walking Drive folder {root_id} (dry_run={args.dry_run})")
        if not args.dry_run:
            client.table("import_batches").insert({
                "id": batch_id, "source_root": f"drive:{root_id}",
                "status": "running", "stats": {},
                "started_at": datetime.utcnow().isoformat(),
            }).execute()

        results = _drive_walk_and_import(client, service, root_id, bucket, args.dry_run, batch_id)
        prop_ok = sum(1 for r in results if r["status"] in ("ok", "would_process"))
        prop_err = sum(1 for r in results if r.get("status") == "error")
        total_images = sum(r.get("images", 0) for r in results)
        total_docs = sum(r.get("documents", 0) for r in results)
        total_imported = sum(r.get("imported", 0) for r in results)
        total_skipped = sum(r.get("skipped", 0) for r in results)
        low_conf = [r for r in results if r.get("parse_confidence") in ("low", "partial")]

        print(f"\n{'DRY RUN: ' if args.dry_run else ''}Import (Drive) complete.")
        print(f"  Properties: {prop_ok} ok, {prop_err} errors")
        print(f"  Images: {total_images}, Docs: {total_docs}")
        print(f"  Assets imported: {total_imported}, skipped (dedup): {total_skipped}")
        if low_conf:
            print(f"  Review needed ({len(low_conf)} low/partial confidence):")
            for r in low_conf:
                print(f"    - [{r.get('parse_confidence')}] {r.get('property_name')} :: {r.get('parse_errors')}")

        if not args.dry_run:
            client.table("import_batches").update({
                "status": "completed" if prop_err == 0 else "partial_failure",
                "stats": {"properties": prop_ok, "assets": total_imported, "skipped": total_skipped, "errors": prop_err, "images": total_images, "documents": total_docs},
                "completed_at": datetime.utcnow().isoformat(),
            }).eq("id", batch_id).execute()
        return 0 if prop_err == 0 else 1

    # ── Local folder source (unchanged legacy path) ──
    source_root = Path(args.source)
    if not source_root.is_dir():
        print(f"Source folder not found: {source_root}")
        return 2

    if args.verify:
        return _verify(client, source_root)

    batch_id = str(uuid.uuid4())
    print(f"Walking {source_root} (dry_run={args.dry_run})")
    if not args.dry_run:
        client.table("import_batches").insert({
            "id": batch_id, "source_root": str(source_root),
            "status": "running", "stats": {},
            "started_at": datetime.utcnow().isoformat(),
        }).execute()

    results = _walk_and_import(client, source_root, bucket, args.dry_run, batch_id)
    prop_ok = sum(1 for r in results if r["status"] in ("ok", "would_process"))
    prop_err = sum(1 for r in results if r.get("status") == "error")
    total_images = sum(r.get("images", 0) for r in results)
    total_docs = sum(r.get("documents", 0) for r in results)
    total_imported = sum(r.get("imported", 0) for r in results)
    total_skipped = sum(r.get("skipped", 0) for r in results)
    low_conf = [r for r in results if r.get("parse_confidence") in ("low", "partial")]

    print(f"\n{'DRY RUN: ' if args.dry_run else ''}Import complete.")
    print(f"  Properties: {prop_ok} ok, {prop_err} errors")
    print(f"  Images: {total_images}, Docs: {total_docs}")
    print(f"  Assets imported: {total_imported}, skipped (dedup): {total_skipped}")
    if low_conf:
        print(f"  Review needed ({len(low_conf)} low/partial confidence):")
        for r in low_conf:
            print(f"    - [{r.get('parse_confidence')}] {r.get('property_name')} :: {r.get('parse_errors')}")

    if not args.dry_run:
        client.table("import_batches").update({
            "status": "completed" if prop_err == 0 else "partial_failure",
            "stats": {"properties": prop_ok, "assets": total_imported, "skipped": total_skipped, "errors": prop_err, "images": total_images, "documents": total_docs},
            "completed_at": datetime.utcnow().isoformat(),
        }).eq("id", batch_id).execute()
    return 0 if prop_err == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())