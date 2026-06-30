from pathlib import Path

from fastapi.testclient import TestClient

from apg_automation.models import CaptionReview
from apg_automation.web_app import create_app


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
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((self.source_dir / source_name).read_bytes())
        return destination


class FakeCaptionGenerator:
    def generate(self, caption_details):
        return CaptionReview("Clean professional caption.")


class FakeTracker:
    def __init__(self):
        self.records = []

    def record_success(self, property_name, post_url, posted_at):
        self.records.append((property_name, post_url, posted_at))


def build_client(tmp_path):
    for index in range(1, 4):
        (tmp_path / f"{index}.jpg").write_bytes(b"image")
    (tmp_path / "caption.txt").write_text("Three-bedroom home near schools.", encoding="utf-8")
    tracker = FakeTracker()
    app = create_app(
        drive=FakeDrive(tmp_path),
        caption_generator=FakeCaptionGenerator(),
        tracker=tracker,
        download_root=tmp_path / "prepared",
    )
    return TestClient(app), tracker


def test_prepare_route_returns_caption_and_asset_urls(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.post("/api/prepare", json={"property_name": "Sample Property"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["property_name"] == "Sample Property"
    assert payload["caption"] == "Clean professional caption."
    assert payload["caption_document_name"] == "caption.txt"
    assert payload["caption_details"] == "Three-bedroom home near schools."
    assert len(payload["images"]) == 3
    assert payload["download_zip_url"].startswith("/api/preparations/")


def test_log_route_records_human_supplied_facebook_url(tmp_path):
    client, tracker = build_client(tmp_path)

    response = client.post(
        "/api/log",
        json={
            "property_name": "Sample Property",
            "facebook_url": "https://facebook.com/live-post",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "logged"}
    assert tracker.records[0][0:2] == (
        "Sample Property",
        "https://facebook.com/live-post",
    )


def test_session_route_returns_demo_role_profile_and_firebase_project(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get("/api/session")

    assert response.status_code == 200
    assert response.json() == {
        "user": {
            "uid": "demo",
            "email": "demo@apg.local",
            "role": "admin",
            "display_name": "Demo Admin",
        },
        "firebase_project_id": "apg-posting-desk-deign-2026",
    }


def test_jobs_route_lists_operational_queue_counts(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get("/api/jobs")

    assert response.status_code == 200
    assert response.json() == {
        "jobs": [],
        "counts": {
            "assigned_today": 0,
            "waiting_approval": 0,
            "ready_to_post": 0,
            "posted_today": 0,
        },
    }


def test_create_job_route_accepts_intake_payload(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.post(
        "/api/jobs",
        json={
            "property_name": "Office Space - Ortigas CBD",
            "assigned_by": "Ma'am Jean",
            "operator": "Miguel",
            "due_date": "2026-06-30",
            "drive_url": "https://drive.google.com/drive/folders/sample-ortigas",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["property_name"] == "Office Space - Ortigas CBD"
    assert payload["assigned_by"] == "Ma'am Jean"
    assert payload["operator"] == "Miguel"
    assert payload["status"] == "assigned"


def test_mark_posted_route_requires_manual_publish_contract(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.post(
        "/api/jobs/APG-0629-001/mark-posted",
        json={"facebook_url": "https://facebook.com/example-post"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "posted"
