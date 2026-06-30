from pathlib import Path

import pytest

from apg_automation.models import CaptionReview
from apg_automation.local_folder import LocalFolderRepository
from apg_automation.review_pipeline import ReviewPipeline


class FakeCaptionGenerator:
    def generate(self, caption_details):
        assert caption_details.strip()
        return CaptionReview("Clean professional caption.")


class FakeTracker:
    def __init__(self):
        self.records = []

    def record_success(self, property_name, post_url, posted_at):
        self.records.append((property_name, post_url, posted_at))


def test_novaliches_fixture_runs_through_local_pipeline(tmp_path):
    folder = Path("Novaliches, 440 Bagbag")
    if not folder.exists():
        pytest.skip("Novaliches fixture folder is not present")

    tracker = FakeTracker()
    pipeline = ReviewPipeline(
        drive=LocalFolderRepository(folder),
        caption_generator=FakeCaptionGenerator(),
        tracker=tracker,
        download_root=tmp_path / "downloads",
    )

    prepared = pipeline.prepare("Novaliches, 440 Bagbag")
    pipeline.log_post("Novaliches, 440 Bagbag", "https://facebook.com/post-1")

    assert prepared.caption == "Clean professional caption."
    assert len(prepared.images) >= 3
    assert tracker.records[0][0:2] == (
        "Novaliches, 440 Bagbag",
        "https://facebook.com/post-1",
    )
