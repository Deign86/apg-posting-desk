"""Tests for fraction_handler — number parsing in property folder names."""
from __future__ import annotations

import pytest
from apg_automation.fraction_handler import (
    extract_all_sizes,
    extract_size,
    is_compound_area,
    is_measurement_suffix,
    normalize_number,
    parse_confidence,
    primary_from_compound,
    split_japanese_number_compound,
)


class TestExtractSize:
    def test_integer_sqm(self):
        size, rem = extract_size("7,713 sqm")
        assert size == "7,713"
        assert "sqm" in rem

    def test_decimal_no_separator(self):
        size, rem = extract_size("22.7sqm")
        assert size == "22.7"

    def test_bare_integer(self):
        size, rem = extract_size("141 Don")
        assert size == "141"

    def test_no_number_returns_empty(self):
        size, rem = extract_size("no numbers here")
        assert size == ""
        assert rem == "no numbers here"

    def test_empty_string(self):
        size, rem = extract_size("")
        assert size == ""
        assert rem == ""

    def test_japanese_counter_token(self):
        """'0軒' should yield size='0', remainder='軒' — NOT raise."""
        size, rem = extract_size("0軒")
        assert size == "0"
        assert rem == "軒"

    def test_japanese_counter_with_value(self):
        size, rem = extract_size("22棟")
        assert size == "22"
        assert rem == "棟"


class TestExtractAllSizes:
    def test_single_value(self):
        assert extract_all_sizes("7,713 sqm") == ["7,713"]

    def test_multiple_values_compound(self):
        result = extract_all_sizes("1708, 1853, 1697 sqm")
        assert result == ["1708", "1853", "1697"]

    def test_no_values(self):
        assert extract_all_sizes("no numbers") == []


class TestNormalizeNumber:
    def test_thousands_separator(self):
        assert normalize_number("7,713") == "7713"

    def test_decimal_preserved(self):
        assert normalize_number("22.7") == "22.7"

    def test_empty(self):
        assert normalize_number("") == ""


class TestParseConfidence:
    def test_high_confidence(self):
        assert parse_confidence(1, 1, 1) == "high"
        assert parse_confidence(0, 1, 1) == "high"

    def test_partial_confidence(self):
        assert parse_confidence(1, 0, 0) == "partial"

    def test_low_confidence(self):
        assert parse_confidence(0, 0, 0) == "low"


class TestJapaneseCounterSplit:
    def test_split_counter(self):
        num, counter = split_japanese_number_compound("0軒")
        assert num == "0"
        assert counter == "軒"

    def test_no_counter(self):
        num, counter = split_japanese_number_compound("22棟")
        assert num == "22"
        assert counter == "棟"

    def test_no_recognised_counter(self):
        num, counter = split_japanese_number_compound("Bacoor")
        assert num == "Bacoor"
        assert counter == ""


class TestIsMeasurementSuffix:
    def test_sqm(self):
        assert is_measurement_suffix("sqm") is True

    def test_japanese_measurement(self):
        assert is_measurement_suffix("平方メートル") is True

    def test_location_label(self):
        assert is_measurement_suffix("Nagkaisang Nayon") is False


class TestCompoundArea:
    def test_is_compound(self):
        assert is_compound_area(["1708", "1853", "1697"]) is True

    def test_is_not_compound(self):
        assert is_compound_area(["7713"]) is False

    def test_primary(self):
        assert primary_from_compound(["1708", "1853"]) == "1708"

    def test_primary_empty(self):
        assert primary_from_compound([]) == ""
