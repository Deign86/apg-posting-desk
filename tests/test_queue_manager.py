from apg_automation.queue_manager import QueueManager


class FakeDrive:
    def __init__(self, folders):
        self.folders = folders

    def find_property_folder(self, property_name):
        return self.folders.get(property_name)


def test_queue_manager_accepts_only_complete_property_folders():
    drive = FakeDrive(
        {
            "Complete Unit": {
                "id": "folder-1",
                "images": ["1.jpg", "2.png", "3.jpg"],
                "documents": ["caption.txt"],
            },
            "Missing Images": {
                "id": "folder-2",
                "images": ["1.jpg", "2.jpg"],
                "documents": ["caption.txt"],
            },
        }
    )
    manager = QueueManager(drive=drive, min_images=3)

    result = manager.build_queue(["Complete Unit", "Missing Images", "Unknown"])

    assert [item.property_name for item in result.ready] == ["Complete Unit"]
    assert result.errors["Missing Images"] == "Insufficient images"
    assert result.errors["Unknown"] == "Property not found"
