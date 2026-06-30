from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .content_extractor import ContentExtractor
from .queue_manager import QueueManager


@dataclass(frozen=True)
class PreparedPost:
    property_id: str
    property_name: str
    caption: str
    caption_document_name: str
    caption_details: str
    images: list[Path]
    requires_manual_review: bool = False
    violations: list[str] | None = None


class ReviewPipeline:
    def __init__(
        self,
        *,
        drive,
        caption_generator,
        tracker,
        download_root: Path = Path("downloads"),
        min_images: int = 3,
        timezone: str = "Asia/Manila",
    ) -> None:
        self.drive = drive
        self.queue = QueueManager(drive=drive, min_images=min_images)
        self.extractor = ContentExtractor(min_images=min_images)
        self.caption_generator = caption_generator
        self.tracker = tracker
        self.download_root = download_root
        self.min_images = min_images
        self.timezone = timezone

    def prepare(self, property_name: str) -> PreparedPost:
        queue = self.queue.build_queue([property_name])
        if property_name in queue.errors:
            raise ValueError(queue.errors[property_name])
        if not queue.ready:
            raise ValueError("Property not found")

        item = queue.ready[0]
        bundle = self._download_and_extract(item)
        review = self.caption_generator.generate(bundle.caption_details)
        return PreparedPost(
            property_id=bundle.property_id,
            property_name=bundle.property_name,
            caption=review.text,
            caption_document_name=item.document_names[0],
            caption_details=bundle.caption_details,
            images=bundle.images,
            requires_manual_review=review.requires_manual_review,
            violations=review.violations,
        )

    def log_post(self, property_name: str, post_url: str) -> None:
        if not post_url.startswith(("https://facebook.com/", "https://www.facebook.com/")):
            raise ValueError("Facebook URL must start with https://facebook.com/")
        self.tracker.record_success(
            property_name,
            post_url,
            datetime.now(ZoneInfo(self.timezone)),
        )

    def _download_and_extract(self, item):
        image_files = item.image_files[: self.min_images]
        document_file = item.document_files[0] if item.document_files else None
        if not image_files or document_file is None:
            raise ValueError("Missing Drive file metadata")

        property_dir = self.download_root / item.property_name
        image_paths = [
            self.drive.download_file(
                file_info["id"],
                property_dir / file_info["name"],
                mime_type=file_info.get("mimeType"),
            )
            for file_info in image_files
        ]
        document_path = self.drive.download_file(
            document_file["id"],
            property_dir / document_file["name"],
            mime_type=document_file.get("mimeType"),
        )
        return self.extractor.extract(
            property_id=item.folder_id,
            property_name=item.property_name,
            image_paths=image_paths,
            document_path=document_path,
        )
