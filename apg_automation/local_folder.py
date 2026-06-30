from __future__ import annotations

import mimetypes
import shutil
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
DOCUMENT_SUFFIXES = {".docx", ".pdf", ".txt"}


class LocalFolderRepository:
    def __init__(self, folder: str | Path) -> None:
        self.folder = Path(folder)

    def find_property_folder(self, property_name: str) -> dict | None:
        if not self.folder.exists() or self.folder.name != property_name:
            return None

        files = [path for path in self.folder.iterdir() if path.is_file()]
        images = [path for path in files if path.suffix.lower() in IMAGE_SUFFIXES]
        documents = [path for path in files if path.suffix.lower() in DOCUMENT_SUFFIXES]

        return {
            "id": str(self.folder),
            "images": [path.name for path in images],
            "documents": [path.name for path in documents],
            "image_files": [self._file_payload(path) for path in images],
            "document_files": [self._file_payload(path) for path in documents],
        }

    def download_file(
        self,
        file_id: str,
        destination: Path,
        *,
        mime_type: str | None = None,
    ) -> Path:
        source = Path(file_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        return destination

    def _file_payload(self, path: Path) -> dict:
        mime_type, _ = mimetypes.guess_type(path.name)
        return {
            "id": str(path),
            "name": path.name,
            "mimeType": mime_type or "application/octet-stream",
        }
