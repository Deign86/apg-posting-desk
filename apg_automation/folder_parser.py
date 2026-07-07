from __future__ import annotations
import re
from pathlib import Path

def parse_property_folder_name(raw_name: str) -> dict:
    name = raw_name.strip()
    errors: list[str] = []
    cleaned = re.sub(r'^[_,.\s-]+', '', name)
    city = ''
    remainder = cleaned
    if ',' in cleaned:
        parts = [p.strip() for p in cleaned.split(',', 1)]
        city = parts[0]
        remainder = parts[1] if len(parts) > 1 else ''
    else:
        city = cleaned
        remainder = ''
    sqm = ''
    extra_areas: list[str] = []
    all_nums = re.findall(r'\d[\d,]*(?:\.\d+)?', remainder)
    sqm_match = re.search(r'(\d[\d,]*(?:\.\d+)?)', remainder)
    if sqm_match:
        sqm = sqm_match.group(1)
        remainder = remainder.replace(sqm_match.group(0), '', 1).strip()
        extra_areas = all_nums[1:] if len(all_nums) > 1 else []
    area = remainder.strip()
    area = re.sub(r'\bSQM\b|\bsqm\b|SQ\.\s*M\.', '', area, flags=re.IGNORECASE).strip()
    area = re.sub(r'\s*[--]\s*(Commerical|Warehouse|Office|Condo|House|Lot|Residential|Industrial)', '', area, flags=re.IGNORECASE).strip()
    area = re.sub(r'[\(\)]', '', area).strip()
    area = re.sub(r'\s+', ' ', area).strip()
    norm_parts: list[str] = []
    if city:
        norm_parts.append(city)
    if area:
        norm_parts.append(area)
    if sqm:
        norm_parts.append(f"{sqm} sqm")
    normalized_title = ', '.join(norm_parts) if norm_parts else cleaned
    slug = normalized_title.lower()
    slug = re.sub(r'[,\s]+', '-', slug)
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    if not city and not area and not sqm:
        errors.append(f"Could not parse any structure from: {raw_name!r}")
    present = sum(1 for v in (city, area, sqm) if v)
    if present >= 3:
        parse_confidence = "high"
    elif present >= 1:
        parse_confidence = "partial"
    else:
        parse_confidence = "low"
    if extra_areas:
        errors.append("multiple_area_values")
        parse_confidence = "partial"
    return {
        "location_city": city,
        "location_area": area,
        "size_sqm": sqm,
        "extra_areas": extra_areas,
        "parse_confidence": parse_confidence,
        "raw_title": raw_name.strip(),
        "normalized_title": normalized_title or cleaned,
        "slug": slug or "unnamed-property",
        "errors": errors,
    }

def classify_category(raw_category: str) -> tuple[str, str]:
    name = raw_category.strip().upper()
    slug = name.lower().replace(" ", "-").replace("_", "-")
    slug = re.sub(r'-+', '-', slug).strip('-')
    return name, slug

def classify_transaction_type(raw: str) -> str:
    upper = raw.strip().upper()
    if any(kw in upper for kw in ("LEASE", "RENT", "LEASING")):
        return "lease"
    if "SALE" in upper:
        return "sale"
    if "SOLD" in upper:
        return "sold"
    if "VIRTUAL" in upper:
        return "virtual"
    return raw.strip().lower()

def is_property_folder(folder_path: Path) -> bool:
    if not folder_path.is_dir():
        return False
    for f in folder_path.iterdir():
        if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png"):
            return True
    return False

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
SUPPORTED_DOCUMENT_EXTENSIONS = {".docx", ".pdf", ".txt"}