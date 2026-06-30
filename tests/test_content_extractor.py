from pathlib import Path

from apg_automation.content_extractor import ContentExtractor


def test_content_extractor_builds_bundle_from_images_and_text_document(tmp_path):
    image_paths = []
    for index in range(3):
        image = tmp_path / f"photo-{index}.jpg"
        image.write_bytes(b"image")
        image_paths.append(image)
    details = tmp_path / "caption.txt"
    details.write_text("Three-bedroom home near schools.", encoding="utf-8")

    extractor = ContentExtractor(min_images=3)
    bundle = extractor.extract(
        property_id="prop-1",
        property_name="Sample Property",
        image_paths=image_paths,
        document_path=details,
    )

    assert bundle.property_id == "prop-1"
    assert bundle.property_name == "Sample Property"
    assert bundle.caption_details == "Three-bedroom home near schools."
    assert bundle.images == [Path(path) for path in image_paths]
