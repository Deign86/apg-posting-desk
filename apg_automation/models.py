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


@dataclass(frozen=True)
class PropertyRef:
    """Lightweight canonical property reference."""
    id: str
    normalized_title: str
    slug: str
    category: str = ""
    transaction_type: str = ""
    location_city: str = ""
    location_area: str = ""
    size_sqm: str = ""
    status: str = "active"


@dataclass(frozen=True)
class AssetRef:
    """Canonical asset reference from property_assets table."""
    id: str
    property_id: str
    kind: str
    original_filename: str
    display_name: str
    object_path: str
    mime_type: str
    size_bytes: int
    width: int
    height: int
    current_version: int
    approval_state: str
    visibility: str
    public_object_path: str


@dataclass(frozen=True)
class PostingJobAsset:
    """Ordered/selected asset for a posting job."""
    id: str | int
    job_id: str
    asset_id: str
    display_order: int = 0
    selected: bool = True
    caption_override: str = ""


@dataclass(frozen=True)
class FolderParsedResult:
    """Result of parsing a raw property folder name."""
    raw_title: str
    location_city: str = ""
    location_area: str = ""
    size_sqm: str = ""
    normalized_title: str = ""
    slug: str = ""
    errors: list[str] = field(default_factory=list)

