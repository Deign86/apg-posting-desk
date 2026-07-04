from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class PropertyQueueItem:
    id: str
    property_name: str


@dataclass(frozen=True)
class ContentBundle:
    property_id: str
    property_name: str
    images: list[Path]
    caption_details: str


@dataclass(frozen=True)
class CaptionReview:
    text: str
    violations: list[str] = field(default_factory=list)
    requires_manual_review: bool = False

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.text == other and not self.requires_manual_review
        return super().__eq__(other)


@dataclass(frozen=True)
class QueueItem:
    property_name: str
    folder_id: str
    image_names: list[str]
    document_names: list[str]
    image_files: list[dict] = field(default_factory=list)
    document_files: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class QueueBuildResult:
    ready: list[QueueItem]
    errors: dict[str, str]
