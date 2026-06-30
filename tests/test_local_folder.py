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


def test_local_folder_repository_copies_file_to_destination(tmp_path):
    folder = tmp_path / "Property"
    folder.mkdir()
    (folder / "2.png").write_bytes(b"image")
    repo = LocalFolderRepository(folder)
    destination = tmp_path / "downloads" / "2.png"

    path = repo.download_file(str(folder / "2.png"), destination)

    assert path == destination
    assert destination.read_bytes() == b"image"
