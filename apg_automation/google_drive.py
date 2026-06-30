from __future__ import annotations

from pathlib import Path


IMAGE_MIME_PREFIX = "image/"
DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/vnd.google-apps.document",
}


class GoogleDriveRepository:
    def __init__(self, *, service, listings_folder_id: str) -> None:
        self.service = service
        self.listings_folder_id = listings_folder_id

    def find_property_folder(self, property_name: str) -> dict | None:
        query = (
            f"'{self.listings_folder_id}' in parents and "
            "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        )
        response = (
            self.service.files()
            .list(q=query, fields="files(id,name)", pageSize=1000)
            .execute()
        )
        for folder in response.get("files", []):
            if folder["name"].strip().lower() == property_name.strip().lower():
                return self._folder_payload(folder)
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
