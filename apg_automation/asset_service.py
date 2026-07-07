from __future__ import annotations

from datetime import datetime
from hashlib import sha256 as _sha256
from pathlib import Path
from typing import Any


def _ext(filename: str) -> str:
    return Path(filename).suffix.lower()


def _image_dims(file_bytes: bytes) -> tuple[int, int]:
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(file_bytes))
        return img.size
    except Exception:
        return 0, 0


class AssetService:
    """Privileged write operations on shared canonical assets.

    Uses the SAME Supabase project as apg-website: assets, property_asset_relations,
    property_asset_versions, activity_log, offerings, and the apg-public / apg-private
    buckets. Storage keys are nested and versioned:
      properties/{offering_id}/images/{asset_id}/original.{ext}
      properties/{offering_id}/images/{asset_id}/v{n}/original.{ext}
      properties/{offering_id}/documents/{asset_id}/original.{ext}
    Edits create NEW VERSIONS (never overwrite). assets.id stays stable across versions
    so property_asset_relations, posting_job_assets, and offerings.cover_asset_id never
    break. All methods use the service-role client; the browser never gets that key.
    """

    def __init__(self, client, *, bucket_private: str = "apg-private",
                 bucket_public: str = "apg-public", signed_url_ttl: int = 3600) -> None:
        self.client = client
        self.bucket_private = bucket_private
        self.bucket_public = bucket_public
        self.signed_url_ttl = signed_url_ttl

    @classmethod
    def from_config(cls, config):
        from .supabase_client import build_supabase_client
        client = build_supabase_client(
            url=config.supabase.url, service_role_key=config.supabase.service_role_key
        )
        return cls(
            client,
            bucket_private=config.storage.bucket_private,
            bucket_public=config.storage.bucket_public,
            signed_url_ttl=config.storage.signed_url_ttl_seconds,
        )

    # ── path helpers ──
    @staticmethod
    def _subdir(asset_type: str) -> str:
        return "documents" if asset_type in ("brochure", "floor_plan", "document") else "images"

    def _original_path(self, offering_id: str, asset_id: str, asset_type: str, ext: str) -> str:
        return f"properties/{offering_id}/{self._subdir(asset_type)}/{asset_id}/original{ext or ''}"

    def _version_path(self, offering_id: str, asset_id: str, asset_type: str, version: int, ext: str) -> str:
        return f"properties/{offering_id}/{self._subdir(asset_type)}/{asset_id}/v{version}/original{ext or ''}"

    # ── Upload ──
    def upload_asset(self, *, offering_id: str, asset_type: str = "image",
                     filename: str, file_bytes: bytes, mime_type: str | None = None,
                     is_public: bool = True, actor_uid: str | None = None,
                     gallery_role: str = "gallery", display_order: int = 0) -> dict[str, Any]:
        if asset_type not in ("image", "brochure", "floor_plan", "document", "video"):
            raise ValueError(f"Invalid asset_type: {asset_type}")
        h = _sha256(file_bytes).hexdigest()
        size = len(file_bytes)
        width, height = _image_dims(file_bytes) if asset_type == "image" else (0, 0)
        import uuid
        asset_id = str(uuid.uuid4())
        ext = _ext(filename)
        bucket = self.bucket_public if is_public else self.bucket_private
        object_path = self._original_path(offering_id, asset_id, asset_type, ext)
        self.client.storage.from_(bucket).upload(
            object_path, file_bytes, {"content-type": mime_type or "application/octet-stream"}
        )
        payload = {
            "id": asset_id, "asset_type": asset_type, "mime_type": mime_type or "application/octet-stream",
            "size_bytes": size, "original_name": filename, "storage_path": object_path,
            "storage_bucket": bucket, "width": width, "height": height,
            "is_public": is_public, "ingestion_status": "active", "current_version": 1,
            "created_by": actor_uid,
        }
        self.client.table("assets").insert(payload).execute()
        self._add_relation(offering_id, asset_id, gallery_role=gallery_role, display_order=display_order)
        self._add_version(asset_id, 1, bucket, object_path, derivative="original",
                          width=width, height=height, size=size, sha=h, actor_uid=actor_uid)
        self._audit("asset", asset_id, "uploaded", actor_uid, {"filename": filename, "offering_id": offering_id})
        return payload

    # ── Replace = new version of the SAME asset (non-destructive) ──
    def replace_asset(self, *, asset_id: str, offering_id: str,
                      filename: str, file_bytes: bytes, mime_type: str | None = None,
                      actor_uid: str | None = None) -> dict[str, Any]:
        old = self._get_asset(asset_id)
        if old is None:
            raise ValueError(f"Asset not found: {asset_id}")
        h = _sha256(file_bytes).hexdigest()
        size = len(file_bytes)
        asset_type = old.get("asset_type", "image")
        width, height = _image_dims(file_bytes) if asset_type == "image" else (0, 0)
        ext = _ext(filename)
        next_version = int(old.get("current_version", 1)) + 1
        bucket = old.get("storage_bucket", self.bucket_private)
        object_path = self._version_path(offering_id, asset_id, asset_type, next_version, ext)
        self.client.storage.from_(bucket).upload(
            object_path, file_bytes, {"content-type": mime_type or old.get("mime_type")}
        )
        self.client.table("property_asset_versions").update({"is_current": False}).eq("asset_id", asset_id).eq("is_current", True).execute()
        self._add_version(asset_id, next_version, bucket, object_path, derivative="original",
                          width=width, height=height, size=size, sha=h, actor_uid=actor_uid)
        self.client.table("assets").update({
            "storage_path": object_path, "current_version": next_version,
            "size_bytes": size, "width": width, "height": height,
            "mime_type": mime_type or old.get("mime_type"), "original_name": filename,
        }).eq("id", asset_id).execute()
        self._audit("asset", asset_id, "replaced", actor_uid, {"version": next_version})
        return self._get_asset(asset_id) or {}

    # ── State transitions ──
    def archive_asset(self, asset_id: str, *, actor_uid: str | None = None) -> dict[str, Any]:
        self.client.table("assets").update({"ingestion_status": "archived"}).eq("id", asset_id).execute()
        self._audit("asset", asset_id, "archived", actor_uid, {})
        return self._get_asset(asset_id) or {}

    def restore_asset(self, asset_id: str, *, actor_uid: str | None = None) -> dict[str, Any]:
        self.client.table("assets").update({"ingestion_status": "active"}).eq("id", asset_id).execute()
        self._audit("asset", asset_id, "restored", actor_uid, {})
        return self._get_asset(asset_id) or {}

    def set_public(self, asset_id: str, *, is_public: bool = True, actor_uid: str | None = None) -> dict[str, Any]:
        self.client.table("assets").update({"is_public": is_public}).eq("id", asset_id).execute()
        self._audit("asset", asset_id, "visibility_changed", actor_uid, {"is_public": is_public})
        return self._get_asset(asset_id) or {}

    def approve_asset(self, asset_id: str, *, actor_uid: str | None = None) -> dict[str, Any]:
        self.client.table("assets").update({
            "ingestion_status": "active",
            "approved_by": actor_uid,
            "approved_at": datetime.utcnow().isoformat(),
        }).eq("id", asset_id).execute()
        self._audit("asset", asset_id, "approved", actor_uid, {})
        return self._get_asset(asset_id) or {}

    # ── Gallery role / order ──
    def set_gallery_order(self, offering_id: str, ordered_asset_ids: list[str], *, actor_uid: str | None = None) -> list[dict]:
        for idx, aid in enumerate(ordered_asset_ids):
            self.client.table("property_asset_relations").update({"display_order": idx}).eq("offering_id", offering_id).eq("asset_id", aid).execute()
        self._audit("offering", offering_id, "gallery_reordered", actor_uid, {"order": ordered_asset_ids})
        return self._list_relations(offering_id)

    def set_cover(self, offering_id: str, asset_id: str, *, actor_uid: str | None = None) -> dict:
        self.client.table("property_asset_relations").update({"is_cover": False}).eq("offering_id", offering_id).execute()
        self.client.table("property_asset_relations").update({"is_cover": True, "gallery_role": "hero"}).eq("offering_id", offering_id).eq("asset_id", asset_id).execute()
        self.client.table("offerings").update({"cover_asset_id": asset_id}).eq("id", offering_id).execute()
        self._audit("offering", offering_id, "cover_set", actor_uid, {"asset_id": asset_id})
        return {"offering_id": offering_id, "cover_asset_id": asset_id}

    # ── internals ──
    def _get_asset(self, asset_id: str) -> dict | None:
        res = self.client.table("assets").select("*").eq("id", asset_id).limit(1).execute()
        return res.data[0] if res and res.data else None

    def _add_relation(self, offering_id: str, asset_id: str, *, gallery_role: str = "gallery", display_order: int = 0) -> None:
        self.client.table("property_asset_relations").insert({
            "offering_id": offering_id, "asset_id": asset_id,
            "gallery_role": gallery_role, "display_order": display_order, "is_cover": False,
        }).execute()

    def _add_version(self, asset_id: str, version_number: int, bucket: str, object_path: str,
                     *, derivative: str = "original", width: int = 0, height: int = 0,
                     size: int = 0, sha: str | None = None, actor_uid: str | None = None) -> None:
        self.client.table("property_asset_versions").insert({
            "asset_id": asset_id, "version_number": version_number,
            "storage_bucket": bucket, "object_path": object_path,
            "derivative_kind": derivative, "width": width, "height": height,
            "size_bytes": size, "sha256": sha, "is_current": True, "created_by": actor_uid,
        }).execute()

    def _list_relations(self, offering_id: str) -> list[dict]:
        res = self.client.table("property_asset_relations").select("*, asset:assets(*)").eq("offering_id", offering_id).order("display_order").execute()
        return res.data or []

    def _audit(self, entity: str, entity_id: str, action: str, actor_uid: str | None, meta: dict) -> None:
        try:
            self.client.table("activity_log").insert({
                "user_id": actor_uid, "action": action, "entity": entity,
                "entity_id": str(entity_id), "meta": meta,
            }).execute()
        except Exception:
            pass