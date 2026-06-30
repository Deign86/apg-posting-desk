from __future__ import annotations

from typing import Protocol

from .models import QueueBuildResult, QueueItem


class DriveFolderLookup(Protocol):
    def find_property_folder(self, property_name: str) -> dict | None:
        raise NotImplementedError


class QueueManager:
    def __init__(self, *, drive: DriveFolderLookup, min_images: int = 3) -> None:
        self.drive = drive
        self.min_images = min_images

    def build_queue(self, property_names: list[str]) -> QueueBuildResult:
        ready: list[QueueItem] = []
        errors: dict[str, str] = {}

        for property_name in property_names:
            folder = self.drive.find_property_folder(property_name)
            if folder is None:
                errors[property_name] = "Property not found"
                continue

            images = list(folder.get("images", []))
            documents = list(folder.get("documents", []))
            if len(images) < self.min_images:
                errors[property_name] = "Insufficient images"
                continue
            if not documents:
                errors[property_name] = "Missing caption document"
                continue

            ready.append(
                QueueItem(
                    property_name=property_name,
                    folder_id=folder["id"],
                    image_names=images,
                    document_names=documents,
                    image_files=list(folder.get("image_files", [])),
                    document_files=list(folder.get("document_files", [])),
                )
            )

        return QueueBuildResult(ready=ready, errors=errors)
