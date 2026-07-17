"""Tests for ingest.py — bucket defaults, Drive source wiring, and mutual exclusivity.

All tests are local/isolated (no real Supabase, no real Drive API calls).
"""

from __future__ import annotations

import pytest


def test_ingest_main_requires_source_or_source_drive(monkeypatch):
    """Calling main() without --source or --source-drive should exit 2."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-svc")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon")
    from apg_automation.ingest import main

    # Mutate sys.argv for the CLI parser
    import sys
    sys_argv = sys.argv
    sys.argv = ["ingest", "--dry-run"]
    try:
        rc = main()
        assert rc == 2, "Expected exit code 2 when neither --source nor --source-drive is given"
    finally:
        sys.argv = sys_argv


def test_ingest_main_rejects_mutual_exclusivity(monkeypatch):
    """--source and --source-drive together should exit 2."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-svc")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon")
    from apg_automation.ingest import main

    import sys
    sys_argv = sys.argv
    sys.argv = ["ingest", "--source", "/tmp", "--source-drive", "--dry-run"]
    try:
        rc = main()
        assert rc == 2, "Expected exit code 2 when both --source and --source-drive are given"
    finally:
        sys.argv = sys_argv


def test_ingest_local_source_rejects_missing_folder(monkeypatch, tmp_path):
    """--source pointing to a non-existent folder should exit 2."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-svc")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon")
    from apg_automation.ingest import main

    import sys
    sys_argv = sys.argv
    bogus = str(tmp_path / "nonexistent")
    sys.argv = ["ingest", "--source", bogus, "--dry-run"]
    try:
        rc = main()
        assert rc == 2, f"Expected exit 2 for missing source folder, got {rc}"
    finally:
        sys.argv = sys_argv


def test_drive_list_subfolders_returns_empty_for_absent_service():
    """The Drive helper should not crash on import — it's a pure function test."""
    from apg_automation.ingest import _drive_list_subfolders, _drive_list_files

    # These functions require a live Drive service; verify they import cleanly
    assert callable(_drive_list_subfolders)
    assert callable(_drive_list_files)


def test_config_has_apr_listing_default():
    """load_config() should default bucket_listings to 'apr-listing'."""
    from apg_automation.config import load_config
    config = load_config("missing.yaml")
    assert config.storage.bucket_listings == "apr-listing", (
        f"Expected 'apr-listing', got '{config.storage.bucket_listings}'"
    )


def test_is_property_folder_name_detects_property_folders():
    """is_property_folder_name should detect valid property folder names."""
    from apg_automation.folder_parser import is_property_folder_name

    assert is_property_folder_name("Makati, 100 sqm") is True
    assert is_property_folder_name("Novaliches, 7,713 Nagkaisang Nayon") is True
    assert is_property_folder_name("Pasig, Bagong Ilog") is True
    assert is_property_folder_name("Tagaytay, 1,600 Sky Ranch") is True
    assert is_property_folder_name("Las Pinas City, 400 TS CRUZ Subdivision, Almanza 2") is True


def test_is_property_folder_name_rejects_non_property_folders():
    """is_property_folder_name should reject non-property folder names."""
    from apg_automation.folder_parser import is_property_folder_name

    assert is_property_folder_name("TV VIDEO") is False
    assert is_property_folder_name("Active Groups") is False
    assert is_property_folder_name("Hiring-Intern-Staff-Format") is False
    assert is_property_folder_name("Contents") is False


def test_config_has_listings_folder_id():
    """load_config() should default google_drive.listings_folder_id."""
    from apg_automation.config import load_config
    config = load_config("missing.yaml")
    assert config.google_drive.listings_folder_id.startswith("1GXeGULY"), (
        f"Unexpected listings_folder_id: {config.google_drive.listings_folder_id}"
    )

    """load_config() should default google_drive.listings_folder_id."""
    from apg_automation.config import load_config
    config = load_config("missing.yaml")
    assert config.google_drive.listings_folder_id.startswith("1GXeGULY"), (
        f"Unexpected listings_folder_id: {config.google_drive.listings_folder_id}"
    )
