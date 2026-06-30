from pathlib import Path

from apg_automation.models import CaptionReview
from apg_automation.review_pipeline import ReviewPipeline


class FakeDrive:
    def __init__(self, source_dir):
        self.source_dir = Path(source_dir)

    def find_property_folder(self, property_name):
        return {
            "id": "folder-1",
            "images": ["1.jpg", "2.jpg", "3.jpg"],
            "documents": ["caption.txt"],
            "image_files": [
                {"id": "1", "name": "1.jpg", "mimeType": "image/jpeg"},
                {"id": "2", "name": "2.jpg", "mimeType": "image/jpeg"},
                {"id": "3", "name": "3.jpg", "mimeType": "image/jpeg"},
            ],
            "document_files": [
                {"id": "caption", "name": "caption.txt", "mimeType": "text/plain"}
            ],
        }

    def download_file(self, file_id, destination, *, mime_type=None):
        source_name = "caption.txt" if file_id == "caption" else f"{file_id}.jpg"
        source = self.source_dir / source_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        return destination


class FakeCaptionGenerator:
    def __init__(self):
        self.details = []

    def generate(self, caption_details):
        self.details.append(caption_details)
        return CaptionReview("Clean professional caption.")


class FakeTracker:
    def __init__(self):
        self.records = []

    def record_success(self, property_name, post_url, posted_at):
        self.records.append((property_name, post_url, posted_at))


def test_review_pipeline_prepares_caption_and_assets_for_manual_posting(tmp_path):
    for index in range(1, 4):
        (tmp_path / f"{index}.jpg").write_bytes(b"image")
    (tmp_path / "caption.txt").write_text("Three-bedroom home near schools.", encoding="utf-8")
    captioner = FakeCaptionGenerator()
    pipeline = ReviewPipeline(
        drive=FakeDrive(tmp_path),
        caption_generator=captioner,
        tracker=FakeTracker(),
        download_root=tmp_path / "downloads",
    )

    prepared = pipeline.prepare("Sample Property")

    assert prepared.property_name == "Sample Property"
    assert prepared.caption == "Clean professional caption."
    assert prepared.caption_document_name == "caption.txt"
    assert prepared.caption_details == "Three-bedroom home near schools."
    assert [path.name for path in prepared.images] == ["1.jpg", "2.jpg", "3.jpg"]
    assert captioner.details == ["Three-bedroom home near schools."]


def test_review_pipeline_logs_human_supplied_facebook_url(tmp_path):
    tracker = FakeTracker()
    pipeline = ReviewPipeline(
        drive=FakeDrive(tmp_path),
        caption_generator=FakeCaptionGenerator(),
        tracker=tracker,
        download_root=tmp_path / "downloads",
    )

    pipeline.log_post("Sample Property", "https://facebook.com/live-post")

    assert tracker.records[0][0:2] == (
        "Sample Property",
        "https://facebook.com/live-post",
    )
