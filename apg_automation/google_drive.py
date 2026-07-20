from __future__ import annotations

from pathlib import Path
import re


IMAGE_MIME_PREFIX = "image/"
DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/vnd.google-apps.document",
}

# Matches drive.google.com/drive/folders/<ID> or drive.google.com/folderview?id=<ID>
_DRIVE_FOLDER_URL_RE = re.compile(
    r"(?:folders/|id=)([\w-]{20,})"
)


class GoogleDriveRepository:
    def __init__(self, *, service, listings_folder_id: str) -> None:
        self.service = service
        self.listings_folder_id = listings_folder_id

    def find_property_folder(self, property_name: str) -> dict | None:
        """Search recursively through the listings folder for a property by name."""
        return self._search_folder_recursive(
            self.listings_folder_id,
            property_name.strip().lower(),
            depth=0,
            max_depth=5,
        )

    def _search_folder_recursive(
        self,
        folder_id: str,
        target_name: str,
        *,
        depth: int,
        max_depth: int,
    ) -> dict | None:
        if depth > max_depth:
            return None
        query = (
            f"'{folder_id}' in parents and "
            "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        )
        response = (
            self.service.files()
            .list(q=query, fields="files(id,name)", pageSize=1000)
            .execute()
        )
        for folder in response.get("files", []):
            if folder["name"].strip().lower() == target_name:
                return self._folder_payload(folder)
        # Not found at this level — recurse into subfolders
        for folder in response.get("files", []):
            result = self._search_folder_recursive(
                folder["id"],
                target_name,
                depth=depth + 1,
                max_depth=max_depth,
            )
            if result is not None:
                return result
        return None

    def _folder_payload(self, folder: dict) -> dict:
        files = self.list_folder_files(folder["id"])
        image_files = [
            item for item in files if item.get("mimeType", "").startswith(IMAGE_MIME_PREFIX)
        ]
        document_files = [
            item for item in files if item.get("mimeType") in DOCUMENT_MIME_TYPES
        ]
        return {
            "id": folder["id"],
            "images": [item["name"] for item in image_files],
            "documents": [item["name"] for item in document_files],
            "image_files": image_files,
            "document_files": document_files,
        }

    def list_folder_files(self, folder_id: str) -> list[dict]:
        response = (
            self.service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="files(id,name,mimeType,size)",
                pageSize=1000,
            )
            .execute()
        )
        return response.get("files", [])

    def list_property_folders(self) -> list[dict]:
        """Scan subfolders of the root listings folder, returning each with asset counts."""
        query = (
            f"'{self.listings_folder_id}' in parents and "
            "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        )
        response = (
            self.service.files()
            .list(q=query, fields="files(id,name)", pageSize=1000)
            .execute()
        )
        results = []
        for folder in response.get("files", []):
            files_in_folder = self.list_folder_files(folder["id"])
            image_count = sum(
                1 for f in files_in_folder
                if f.get("mimeType", "").startswith(IMAGE_MIME_PREFIX)
            )
            doc_count = sum(
                1 for f in files_in_folder
                if f.get("mimeType") in DOCUMENT_MIME_TYPES
            )
            errors = []
            if image_count < 3:
                errors.append(f"Only {image_count} image(s) found (minimum 3 required)")
            if doc_count < 1:
                errors.append("No caption document found")
            results.append({
                "id": folder["id"],
                "name": folder["name"],
                "image_count": image_count,
                "has_caption_doc": doc_count >= 1,
                "doc_count": doc_count,
                "valid": len(errors) == 0,
                "errors": errors,
            })
        return results

    def count_assets(self, folder_id: str) -> dict:
        """Count images and caption documents in a Drive folder."""
        files = self.list_folder_files(folder_id)
        image_count = sum(
            1 for f in files
            if f.get("mimeType", "").startswith(IMAGE_MIME_PREFIX)
        )
        doc_count = sum(
            1 for f in files
            if f.get("mimeType") in DOCUMENT_MIME_TYPES
        )
        return {
            "image_count": image_count,
            "has_caption_doc": doc_count >= 1,
            "errors": [],
        }

    @staticmethod
    def resolve_folder_id(value: str) -> str | None:
        """Resolve a folder ID from a Drive URL, raw ID, or property name.
        
        Returns the folder ID if found, or None if it cannot be determined.
        For property names, returns the name itself (caller calls find_property_folder).
        """
        stripped = value.strip()
        if not stripped:
            return None
        # If it's a drive.google.com URL, extract the folder ID
        m = _DRIVE_FOLDER_URL_RE.search(stripped)
        if m:
            return m.group(1)
        # If it looks like a Drive folder ID (long alphanumeric+underscore+hyphen)
        if re.match(r"^[\w-]{20,}$", stripped):
            return stripped
        # Otherwise it's likely a property name — return as-is for name-based lookup
        return stripped

    def download_file(
        self,
        file_id: str,
        destination: Path,
        *,
        mime_type: str | None = None,
    ) -> Path:
        from googleapiclient.http import MediaIoBaseDownload

        destination.parent.mkdir(parents=True, exist_ok=True)
        if mime_type == "application/vnd.google-apps.document":
            request = self.service.files().export_media(
                fileId=file_id,
                mimeType="text/plain",
            )
            destination = destination.with_suffix(".txt")
        else:
            request = self.service.files().get_media(fileId=file_id)
        with destination.open("wb") as handle:
            downloader = MediaIoBaseDownload(handle, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        return destination


def build_drive_service():
    from googleapiclient.discovery import build

    from .google_auth import build_google_credentials

    return build("drive", "v3", credentials=build_google_credentials())
