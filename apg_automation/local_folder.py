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
        if not self.folder.exists():
            return None

        # Exact name match on the root folder
        target = self.folder if self.folder.name == property_name else None

        # If no exact match and root folder IS a property folder itself, use it
        if target is None:
            files = [p for p in self.folder.iterdir() if p.is_file()]
            has_images = any(p.suffix.lower() in IMAGE_SUFFIXES for p in files)
            has_docs = any(p.suffix.lower() in DOCUMENT_SUFFIXES for p in files)
            if has_images and has_docs:
                target = self.folder

        # If still no match, try one level of subfolders
        if target is None and self.folder.is_dir():
            for child in self.folder.iterdir():
                if child.is_dir() and child.name.lower() == property_name.lower():
                    target = child
                    break

        if target is None or not target.exists():
            return None

        files = [path for path in target.iterdir() if path.is_file()]
        images = [path for path in files if path.suffix.lower() in IMAGE_SUFFIXES]
        documents = [path for path in files if path.suffix.lower() in DOCUMENT_SUFFIXES]

        return {
            "id": str(target),
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
