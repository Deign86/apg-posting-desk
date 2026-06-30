from __future__ import annotations

from pathlib import Path

from .models import ContentBundle

SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


class ContentExtractor:
    def __init__(self, *, min_images: int = 3) -> None:
        self.min_images = min_images

    def extract(
        self,
        *,
        property_id: str,
        property_name: str,
        image_paths: list[Path],
        document_path: Path,
    ) -> ContentBundle:
        images = [Path(path) for path in image_paths]
        valid_images = [
            path for path in images if path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
        ]
        if len(valid_images) < self.min_images:
            raise ValueError("Insufficient valid images")

        caption_details = self.extract_document_text(Path(document_path))
        if not caption_details.strip():
            raise ValueError("Caption document is empty")

        return ContentBundle(
            property_id=property_id,
            property_name=property_name,
            images=valid_images,
            caption_details=caption_details.strip(),
        )

    def extract_document_text(self, document_path: Path) -> str:
        suffix = document_path.suffix.lower()
        if suffix == ".txt":
            return document_path.read_text(encoding="utf-8")
        if suffix == ".docx":
            from docx import Document

            document = Document(str(document_path))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        if suffix == ".pdf":
            from PyPDF2 import PdfReader

            reader = PdfReader(str(document_path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        raise ValueError(f"Unsupported caption document type: {suffix}")
