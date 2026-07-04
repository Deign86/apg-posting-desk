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


def build_client(tmp_path, demo_role="admin"):
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
    headers = {}
    if demo_role is not None:
        headers["X-Demo-Role"] = demo_role
    return TestClient(app, headers=headers), tracker


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


def test_session_returns_admin_role_with_demo_header(tmp_path):
    client, _ = build_client(tmp_path, demo_role="admin")

    response = client.get("/api/session")

    assert response.status_code == 200
    assert response.json() == {
        "user": {
            "uid": "demo",
            "email": "demo@apg.local",
            "role": "admin",
            "display_name": "Demo Admin",
        },
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


def test_get_job_returns_job_by_id(tmp_path):
    from apg_automation.job_store import InMemoryJobStore
    store = InMemoryJobStore()
    created = store.create(property_name="Test", assigned_by="A", operator="B", due_date="2026-07-01", drive_url="x")
    job = store.get_job(created["id"])
    assert job is not None
    assert job.property_name == "Test"


def test_get_job_returns_none_for_missing_id():
    from apg_automation.job_store import InMemoryJobStore
    store = InMemoryJobStore()
    assert store.get_job("NONEXIST") is None


def test_update_status_changes_job_status():
    from apg_automation.job_store import InMemoryJobStore
    store = InMemoryJobStore()
    created = store.create(property_name="T", assigned_by="A", operator="B", due_date="2026-07-01", drive_url="x")
    updated = store.update_status(created["id"], "waiting_approval")
    assert updated["status"] == "waiting_approval"


def test_add_activity_and_get_activity():
    from apg_automation.job_store import InMemoryJobStore
    store = InMemoryJobStore()
    created = store.create(property_name="T", assigned_by="A", operator="B", due_date="2026-07-01", drive_url="x")
    store.add_activity(created["id"], {"at": "10:30", "text": "Job created"})
    store.add_activity(created["id"], {"at": "10:35", "text": "Validated"})
    activity = store.get_activity(created["id"])
    assert len(activity) == 2
    assert activity[0]["text"] == "Job created"


def test_set_prepared_stores_caption_data():
    from apg_automation.job_store import InMemoryJobStore
    store = InMemoryJobStore()
    created = store.create(property_name="T", assigned_by="A", operator="B", due_date="2026-07-01", drive_url="x")
    store.set_prepared(created["id"], {"caption": "Clean caption.", "images": [{"name": "1.jpg", "url": "/x/1.jpg"}]})
    job = store.get_job(created["id"])
    assert job.caption == "Clean caption."


def test_validate_route_returns_ok_for_valid_job(tmp_path):
    client, _ = build_client(tmp_path)
    create = client.post("/api/jobs", json={
        "property_name": "Sample Property",
        "assigned_by": "Ma'am Jean",
        "operator": "Deign",
        "due_date": "2026-06-30",
        "drive_url": "https://drive.google.com/demo",
    })
    job_id = create.json()["id"]
    resp = client.post(f"/api/jobs/{job_id}/validate")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_validate_route_returns_404_for_missing_job(tmp_path):
    client, _ = build_client(tmp_path)
    resp = client.post("/api/jobs/NONEXIST/validate")
    assert resp.status_code == 404


def test_prepare_route_returns_prepared_data(tmp_path):
    client, _ = build_client(tmp_path)
    create = client.post("/api/jobs", json={
        "property_name": "Sample Property",
        "assigned_by": "Ma'am Jean",
        "operator": "Deign",
        "due_date": "2026-06-30",
        "drive_url": "https://drive.google.com/demo",
    })
    job_id = create.json()["id"]
    resp = client.post(f"/api/jobs/{job_id}/prepare")
    assert resp.status_code == 200
    data = resp.json()
    assert "caption" in data
    assert "images" in data
    assert len(data["images"]) == 3


def test_prepare_route_returns_404_for_missing_job(tmp_path):
    client, _ = build_client(tmp_path)
    resp = client.post("/api/jobs/NONEXIST/prepare")
    assert resp.status_code == 404


def test_captions_route_returns_variants(tmp_path):
    client, _ = build_client(tmp_path)
    create = client.post("/api/jobs", json={
        "property_name": "Sample Property",
        "assigned_by": "Ma'am Jean",
        "operator": "Deign",
        "due_date": "2026-06-30",
        "drive_url": "https://drive.google.com/demo",
    })
    job_id = create.json()["id"]
    resp = client.post(f"/api/jobs/{job_id}/captions")
    assert resp.status_code == 200
    data = resp.json()
    assert "variants" in data
    assert isinstance(data["variants"], list)
    assert len(data["variants"]) >= 1


def test_activity_route_returns_activity_list(tmp_path):
    client, _ = build_client(tmp_path)
    create = client.post("/api/jobs", json={
        "property_name": "Sample Property",
        "assigned_by": "Ma'am Jean",
        "operator": "Deign",
        "due_date": "2026-06-30",
        "drive_url": "https://drive.google.com/demo",
    })
    job_id = create.json()["id"]
    resp = client.get(f"/api/jobs/{job_id}/activity")
    assert resp.status_code == 200
    assert "activity" in resp.json()
    assert isinstance(resp.json()["activity"], list)


def test_activity_route_returns_404_for_missing_job(tmp_path):
    client, _ = build_client(tmp_path)
    resp = client.get("/api/jobs/NONEXIST/activity")
    assert resp.status_code == 404


def test_session_returns_user_role_without_demo_header(tmp_path):
    client, _ = build_client(tmp_path, demo_role=None)
    response = client.get("/api/session")
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "user"
    assert response.json()["user"]["display_name"] == "Demo User"


def test_create_job_returns_403_for_user_role(tmp_path):
    client, _ = build_client(tmp_path, demo_role="user")
    response = client.post("/api/jobs", json={
        "property_name": "Test",
        "assigned_by": "A",
        "operator": "B",
        "due_date": "2026-07-01",
        "drive_url": "x",
    })
    assert response.status_code == 403


def test_create_job_returns_201_for_admin_role(tmp_path):
    client, _ = build_client(tmp_path, demo_role="admin")
    response = client.post("/api/jobs", json={
        "property_name": "Test",
        "assigned_by": "A",
        "operator": "B",
        "due_date": "2026-07-01",
        "drive_url": "x",
    })
    assert response.status_code == 201


def test_queue_next_returns_403_for_user_role(tmp_path):
    client, _ = build_client(tmp_path, demo_role="user")
    response = client.post("/api/queue/next")
    assert response.status_code == 403


def test_user_role_can_access_non_admin_endpoints(tmp_path):
    client, _ = build_client(tmp_path, demo_role="user")
    assert client.get("/api/session").status_code == 200
    assert client.get("/api/jobs").status_code == 200
    assert client.post("/api/prepare", json={"property_name": "Sample Property"}).status_code == 200
    assert client.post("/api/log", json={
        "property_name": "Sample Property",
        "facebook_url": "https://facebook.com/test",
    }).status_code == 200
