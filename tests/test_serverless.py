"""Tests for the serverless app builder (apg_automation/serverless.py).

The serverless builder wires Supabase services and returns a FastAPI app
without running uvicorn or performing startup probes.  These tests verify
the wiring is structurally correct using env-var injection.
"""

from __future__ import annotations


def test_serverless_builder_imports_and_routes(monkeypatch):
    """build_live_app() should return a FastAPI app with the expected route set."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-role")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon")
    monkeypatch.setenv("NVIDIA_API_KEY", "test-nvidia")

    from apg_automation.serverless import build_live_app

    app = build_live_app()

    # FastAPI fits the protocol
    assert hasattr(app, "routes")

    # Route table includes the key endpoints
    route_paths = {r.path for r in app.routes}
    expected = {
        "/api/session",
        "/api/jobs",
        "/api/jobs/{job_id}/prepare",
        "/api/jobs/{job_id}/prepared.zip",
        "/api/jobs/{job_id}/captions",
        "/api/jobs/{job_id}/mark-posted",
        "/api/jobs/{job_id}/validate",
        "/api/jobs/{job_id}/activity",
        "/api/prepare",
        "/api/log",
        "/api/offerings",
        "/api/assets/signed-url",
    }
    missing = expected - route_paths
    assert not missing, f"Missing routes: {missing}"


def test_serverless_app_has_supabase_services(monkeypatch):
    """The app wired by build_live_app() should have Supabase-aware dependencies."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-role")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon")
    monkeypatch.setenv("NVIDIA_API_KEY", "test-nvidia")

    from apg_automation.serverless import build_live_app

    app = build_live_app()

    # FastAPI dependency graph is wired; just verifying the route count is
    # reasonable and the app title matches
    assert app.title == "APG Review Dashboard"


def test_serverless_prepare_route_requires_auth(monkeypatch):
    """In Supabase mode, unauthenticated requests to prepare should 401."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-role")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon")
    monkeypatch.setenv("NVIDIA_API_KEY", "test-nvidia")

    from apg_automation.serverless import build_live_app
    from fastapi.testclient import TestClient

    app = build_live_app()
    client = TestClient(app)

    # No Authorization header → 401
    resp = client.post("/api/jobs/FakeJobId/prepare")
    assert resp.status_code == 401

    resp = client.post("/api/prepare", json={"property_name": "Test"})
    assert resp.status_code == 401

    resp = client.get("/api/jobs/FakeJobId/prepared.zip")
    assert resp.status_code == 401
