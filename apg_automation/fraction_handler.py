"""
Fraction and number handling utilities for APG property folder name parsing.

Provides helpers for extracting, validating, and normalizing numeric
expressions that appear in real-world property folder names, including:
  - Integer and decimal sizes: "7,713", "22.7", "141"
  - Text-prefixed forms: "7,713 sqm", "22.7sqm"
  - Japanese-counter compounds: "0軒" (0-buildings), "22.7sqm 戸建て"
  - Multi-area values: "1708, 1853, 1697" (compound lot measurements)
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Numeric extraction
# ---------------------------------------------------------------------------

# Captures a single size value (integer or decimal, comma- or dot-separated).
# Group 1 = the full number as it appears in text.
_NUM_PATTERN = re.compile(r'\d[\d,]*(?:\.\d+)?')

# Captures ALL numbers in a string (for multi-area detection).
_ALL_NUMS_PATTERN = re.compile(r'\d[\d,]*(?:\.\d+)?')


def extract_size(text: str) -> tuple[str, str]:
    """Extract the first numeric size from *text*.

    Returns ``(size, remainder)`` where *remainder* is *text* with the
    extracted size removed (first occurrence only).

    Handles::

        "7,713 sqm"  →  ("7,713", "sqm")
        "22.7sqm"    →  ("22.7",  "sqm")
        "141 Don"    →  ("141",   "Don")
        "0軒"        →  ("0",     "軒")

    If no number is found, returns ``("", text)``.
    """
    m = _NUM_PATTERN.search(text)
    if not m:
        return "", text
    size = m.group(0)
    remainder = text[:m.start()] + text[m.end():]
    return size, remainder


def extract_all_sizes(text: str) -> list[str]:
    """Return every numeric token found in *text* (order-preserving).

    Trailing commas (from comma-separated lists) are stripped so that
    "1708, 1853, 1697" yields ["1708", "1853", "1697"] rather than
    ['1708,', '1853,', '1697'].
    """
    return [t.rstrip(",") for t in _ALL_NUMS_PATTERN.findall(text)]


def normalize_number(raw: str) -> str:
    """Strip thousands separators from a raw numeric string.

    "7,713" → "7713",  "22.7" → "22.7"
    """
    return raw.replace(",", "")


def parse_confidence(count_city: int, count_area: int, count_sqm: int) -> str:
    """Derive parse confidence from the number of detected fields.

    *high*  — at least two of the three fields are non-empty
    *partial* — exactly one field present
    *low*    — nothing detected
    """
    present = sum(1 for v in (count_city, count_area, count_sqm) if v)
    if present >= 2:
        return "high"
    if present == 1:
        return "partial"
    return "low"


# ---------------------------------------------------------------------------
# Japanese-counter handling
# ---------------------------------------------------------------------------

# Common Japanese counters that follow a number.
# These are NOT part of the area/location string.
_JAPANESE_COUNTERS = re.compile(
    r'(?:軒|棟|件|区画|戸|人|台|丁|番地|号室|階建て)'
)

# Patterns that indicate the number is a measurement rather than a counter
_MEASUREMENT_SUFFIXES = re.compile(
    r'(?:sqm|sq\.?m|㎡|m2|平米|平方メートル|SQM)',
    re.IGNORECASE,
)


def split_japanese_number_compound(token: str) -> tuple[str, str]:
    """Separate a Japanese number+counter token into (number, counter).

    Examples::

        "0軒"   →  ("0",   "軒")
        "22棟"  →  ("22",  "棟")
        "140人" →  ("140", "")

    If no recognised counter is found the full token is returned as the
    number with an empty counter.
    """
    m = _JAPANESE_COUNTERS.search(token)
    if m:
        return token[:m.start()], token[m.start():]
    return token, ""


def is_measurement_suffix(token: str) -> bool:
    """Return True when *token* looks like a measurement suffix rather than
    a location label (e.g. "sqm", "㎡", "平方メートル")."""
    return bool(_MEASUREMENT_SUFFIXES.search(token))


# ---------------------------------------------------------------------------
# Compound area handling
# ---------------------------------------------------------------------------

def is_compound_area(numbers: list[str], join_char: str = ",") -> bool:
    """Return True when *numbers* looks like a compound area string.

    Example: ["1708", "1853", "1697"] with join_char "," → compound.
    """
    return len(numbers) > 1


def primary_from_compound(numbers: list[str]) -> str:
    """Return the first (primary) value from a list of size numbers."""
    return numbers[0] if numbers else ""
