from pathlib import Path

from apg_automation.local_folder import LocalFolderRepository


def test_local_folder_repository_discovers_images_and_caption_document(tmp_path):
    folder = tmp_path / "Novaliches, 440 Bagbag"
    folder.mkdir()
    for name in ["2.png", "3.png", "4.png", "5.png", "caption ref.jpeg"]:
        (folder / name).write_bytes(b"image")
    (folder / "Untitled doc.docx").write_bytes(b"docx")

    repo = LocalFolderRepository(folder)

    found = repo.find_property_folder("Novaliches, 440 Bagbag")

    assert found["id"] == str(folder)
    assert found["images"] == ["2.png", "3.png", "4.png", "5.png", "caption ref.jpeg"]
    assert found["documents"] == ["Untitled doc.docx"]


def test_local_folder_repository_matches_fixture_folder_by_content(tmp_path):
    """When the requested name differs but the folder IS a property folder, match it."""
    folder = tmp_path / "Novaliches, 440 Bagbag"
    folder.mkdir()
    for name in ["2.png", "3.png", "4.png"]:
        (folder / name).write_bytes(b"image")
    (folder / "caption.docx").write_bytes(b"docx")

    repo = LocalFolderRepository(folder)

    # Request a different name; folder should still match because it has images + docs
    found = repo.find_property_folder("Some Other Name")

    assert found is not None
    assert found["id"] == str(folder)
    assert len(found["images"]) == 3
    assert found["documents"] == ["caption.docx"]


def test_local_folder_repository_finds_subfolder_by_name(tmp_path):
    """A root folder containing a named property subfolder should find it."""
    root = tmp_path / "APR LISTING"
    root.mkdir()
    sub = root / "Makati, 100 sqm"
    sub.mkdir()
    (sub / "1.jpg").write_bytes(b"img")
    (sub / "details.txt").write_text("details", encoding="utf-8")

    repo = LocalFolderRepository(root)

    found = repo.find_property_folder("Makati, 100 sqm")

    assert found is not None
    assert found["id"] == str(sub)
    assert found["images"] == ["1.jpg"]
    assert found["documents"] == ["details.txt"]


def test_local_folder_repository_returns_none_for_empty_root(tmp_path):
    """A root with no images/documents and no matching subfolder returns None."""
    root = tmp_path / "Empty"
    root.mkdir()

    repo = LocalFolderRepository(root)

    assert repo.find_property_folder("Nonexistent") is None


def test_local_folder_repository_copies_file_to_destination(tmp_path):
    folder = tmp_path / "Property"
    folder.mkdir()
    (folder / "2.png").write_bytes(b"image")
    repo = LocalFolderRepository(folder)
    destination = tmp_path / "downloads" / "2.png"

    path = repo.download_file(str(folder / "2.png"), destination)

    assert path == destination
    assert destination.read_bytes() == b"image"
