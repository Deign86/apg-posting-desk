from __future__ import annotations

from pathlib import Path

from .supabase_client import build_supabase_client


class SupabaseAssetRepository:
    """Read-side repository adapter implementing the DriveFolderLookup Protocol.

    Returns the same {id, images, documents, image_files, document_files} dict
    shape as LocalFolderRepository and GoogleDriveRepository, so the existing
    QueueManager / ReviewPipeline / ContentExtractor work unchanged.

    Queries the SHARED Supabase project (same as apg-website):
      - offerings (property/listing records)
      - assets (canonical file records)
      - property_asset_relations (gallery role + display order)
      - apg-public / apg-private Storage buckets

    The Windows folder is never read at runtime.
    """

    def __init__(
        self,
        client=None,
        *,
        bucket_private: str = "apg-private",
        bucket_public: str = "apg-public",
        signed_url_ttl: int = 3600,
        min_images: int = 3,
    ) -> None:
        self.client = client or build_supabase_client()
        self.bucket_private = bucket_private
        self.bucket_public = bucket_public
        self.signed_url_ttl = signed_url_ttl
        self.min_images = min_images

    # â”€â”€ DriveFolderLookup Protocol â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def find_property_folder(self, property_name: str) -> dict | None:
        """Look up an offering by title/slug, return its assets via relations."""
        offering = self._find_offering(property_name)
        if offering is None:
            return None
        assets = self._list_offering_assets(offering["id"])
        images = [a for a in assets if a.get("asset_type") == "image"]
        documents = [a for a in assets if a.get("asset_type") in ("document", "brochure")]
        return {
            "id": offering["id"],
            "images": [a.get("original_name", "") for a in images],
            "documents": [a.get("original_name", "") for a in documents],
            "image_files": [
                {
                    "id": a["id"],
                    "name": a.get("original_name", ""),
                    "mimeType": a.get("mime_type", ""),
                    "storage_path": a.get("storage_path", ""),
                    "storage_bucket": a.get("storage_bucket", self.bucket_public),
                }
                for a in images
            ],
            "document_files": [
                {
                    "id": a["id"],
                    "name": a.get("original_name", ""),
                    "mimeType": a.get("mime_type", ""),
                    "storage_path": a.get("storage_path", ""),
                    "storage_bucket": a.get("storage_bucket", self.bucket_private),
                }
                for a in documents
            ],
        }

    def download_file(
        self,
        file_id: str,
        destination: Path,
        *,
        mime_type: str | None = None,
    ) -> Path:
        """Download an asset's bytes from Storage to a local path.
        file_id is the asset UUID from the shared assets table.
        Uses the asset's storage_bucket to determine which bucket to read from.
        """
        asset = self._get_asset(file_id)
        if asset is None:
            raise ValueError(f"Asset not found: {file_id}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        storage_path = asset["storage_path"]
        bucket = asset.get("storage_bucket", self.bucket_public)
        with destination.open("wb") as f:
            res = self.client.storage.from_(bucket).download(storage_path)
            if isinstance(res, bytes):
                f.write(res)
            else:
                f.write(b"".join(res))
        return destination

    def get_signed_url(self, asset_id: str, *, expires_in: int | None = None) -> str:
        """Mint a short-lived signed URL for operator review.
        For public assets, returns the public URL directly (matches website's getPublicUrl).
        For private assets, creates a signed URL with short TTL.
        """
        asset = self._get_asset(asset_id)
        if asset is None:
            raise ValueError(f"Asset not found: {asset_id}")
        storage_path = asset["storage_path"]
        bucket = asset.get("storage_bucket", self.bucket_public)
        if asset.get("is_public", True) and bucket == self.bucket_public:
            result = self.client.storage.from_(bucket).get_public_url(storage_path)
            if isinstance(result, dict):
                return result.get("publicUrl", "")
            return getattr(result, "publicUrl", "")
        ttl = self.signed_url_ttl if expires_in is None else expires_in
        result = self.client.storage.from_(bucket).create_signed_url(storage_path, ttl)
        if isinstance(result, dict):
            return result.get("signedURL", "")
        return getattr(result, "signedURL", "")

    # â”€â”€ Internal queries (shared schema: offerings, assets, relations) â”€â”€

    def _find_offering(self, name: str) -> dict | None:
        """Match by slug first, then by title (case-insensitive).
        Only returns non-deleted offerings.
        """
        slug = name.strip().lower().replace(" ", "-").replace(",", "")
        res = (
            self.client.table("offerings")
            .select("*").eq("slug", slug).is_("deleted_at", "null").limit(1).execute()
        )
        rows = res.data if res and res.data else []
        if rows:
            return rows[0]
        res = (
            self.client.table("offerings")
            .select("*").ilike("title", name.strip()).is_("deleted_at", "null").limit(1).execute()
        )
        rows = res.data if res and res.data else []
        return rows[0] if rows else None

    def _get_asset(self, asset_id: str) -> dict | None:
        res = (
            self.client.table("assets").select("*").eq("id", asset_id).limit(1).execute()
        )
        rows = res.data if res and res.data else []
        return rows[0] if rows else None

    def _list_offering_assets(self, offering_id: str) -> list[dict]:
        """List assets for an offering via property_asset_relations.
        Joins the assets table and orders by display_order
        (matching the website's usePropertyGallery hook).
        Only returns active (non-archived) assets.
        """
        res = (
            self.client.table("property_asset_relations")
            .select("*, asset:assets(*)")
            .eq("offering_id", offering_id)
            .order("display_order")
            .execute()
        )
        rows = res.data if res and res.data else []
        assets = []
        for row in rows:
            asset = row.get("asset")
            if asset and isinstance(asset, dict):
                if asset.get("ingestion_status") != "archived":
                    assets.append(asset)
        return assets