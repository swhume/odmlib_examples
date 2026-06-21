import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from value_transformer import ValueTransformer


# Shared test transform definitions matching gendefine-plan.md section 4.4
TRANSFORMS = {
    "core_to_mandatory": {
        "type": "lookup",
        "map": {"Req": "Yes", "Exp": "No", "Perm": "No"},
        "default": "No"
    },
    "repeating_yes_no": {
        "type": "lookup",
        "map": {"Yes": "Yes", "No": "No", "true": "Yes", "false": "No"},
        "default": "No"
    },
    "lookup_no_default": {
        "type": "lookup",
        "map": {"A": "Alpha", "B": "Beta"}
    },
    "order_to_int": {
        "type": "type_coercion",
        "target": "integer"
    },
    "score_to_float": {
        "type": "type_coercion",
        "target": "float"
    },
    "to_string": {
        "type": "type_coercion",
        "target": "string"
    },
    "where_clause_parse": {
        "type": "regex_parse",
        "pattern": "^(\\w+)\\s*(EQ|NE|LT|LE|GT|GE|IN|NOTIN)\\s*(.+)$",
        "output_fields": ["Variable", "Comparator", "Value"]
    }
}

DEFAULTS = {
    "Purpose": "Tabulation",
    "Repeating": "No",
    "Mandatory": "No"
}


class TestLookupTransform:
    """Tests for the lookup transform type."""

    @pytest.fixture
    def vt(self):
        return ValueTransformer(TRANSFORMS, DEFAULTS)

    def test_lookup_matching_value(self, vt):
        assert vt.transform("Req", "core_to_mandatory") == "Yes"

    def test_lookup_another_matching_value(self, vt):
        assert vt.transform("Perm", "core_to_mandatory") == "No"

    def test_lookup_default_fallback(self, vt):
        assert vt.transform("Unknown", "core_to_mandatory") == "No"

    def test_lookup_none_value_returns_default(self, vt):
        assert vt.transform(None, "core_to_mandatory") == "No"

    def test_lookup_no_default_and_no_match_returns_none(self, vt):
        assert vt.transform("C", "lookup_no_default") is None

    def test_lookup_no_default_and_match(self, vt):
        assert vt.transform("A", "lookup_no_default") == "Alpha"

    def test_lookup_numeric_value_stringified(self, vt):
        """Numeric cell values should be converted to string for lookup."""
        transforms = {
            "status": {
                "type": "lookup",
                "map": {"1": "Active", "2": "Inactive"},
                "default": "Unknown"
            }
        }
        vt2 = ValueTransformer(transforms, {})
        assert vt2.transform(1, "status") == "Active"


class TestTypeCoercion:
    """Tests for the type_coercion transform type."""

    @pytest.fixture
    def vt(self):
        return ValueTransformer(TRANSFORMS, DEFAULTS)

    def test_coerce_to_integer(self, vt):
        assert vt.transform("5", "order_to_int") == 5
        assert isinstance(vt.transform("5", "order_to_int"), int)

    def test_coerce_float_string_to_integer(self, vt):
        """openpyxl may return numeric values as floats."""
        assert vt.transform(3.0, "order_to_int") == 3

    def test_coerce_to_float(self, vt):
        assert vt.transform("3.14", "score_to_float") == pytest.approx(3.14)

    def test_coerce_to_string(self, vt):
        assert vt.transform(42, "to_string") == "42"

    def test_coerce_none_returns_none(self, vt):
        assert vt.transform(None, "order_to_int") is None

    def test_coerce_type_standalone_integer(self, vt):
        assert vt.coerce_type("7", "integer") == 7

    def test_coerce_type_standalone_float(self, vt):
        assert vt.coerce_type("2.5", "float") == pytest.approx(2.5)

    def test_coerce_type_standalone_string(self, vt):
        assert vt.coerce_type(100, "string") == "100"

    def test_coerce_type_none_returns_none(self, vt):
        assert vt.coerce_type(None, "integer") is None

    def test_coerce_type_invalid_target_raises(self, vt):
        with pytest.raises(ValueError, match="Unsupported coercion"):
            vt.coerce_type("x", "boolean")


class TestRegexParseTransform:
    """Tests for the regex_parse transform type."""

    @pytest.fixture
    def vt(self):
        return ValueTransformer(TRANSFORMS, DEFAULTS)

    def test_regex_parse_simple_expression(self, vt):
        result = vt.transform("TESTCD EQ SYSBP", "where_clause_parse")
        assert result == {"Variable": "TESTCD", "Comparator": "EQ", "Value": "SYSBP"}

    def test_regex_parse_different_comparator(self, vt):
        result = vt.transform("AGE GE 18", "where_clause_parse")
        assert result == {"Variable": "AGE", "Comparator": "GE", "Value": "18"}

    def test_regex_parse_in_operator_with_parens(self, vt):
        result = vt.transform("TESTCD IN (SYSBP, DIABP)", "where_clause_parse")
        assert result["Variable"] == "TESTCD"
        assert result["Comparator"] == "IN"
        assert result["Value"] == "(SYSBP, DIABP)"

    def test_regex_parse_no_match_returns_none(self, vt):
        result = vt.transform("not a valid expression", "where_clause_parse")
        assert result is None

    def test_regex_parse_none_value_returns_none(self, vt):
        result = vt.transform(None, "where_clause_parse")
        assert result is None


class TestApplyDefault:
    """Tests for the apply_default method."""

    @pytest.fixture
    def vt(self):
        return ValueTransformer(TRANSFORMS, DEFAULTS)

    def test_truthy_value_returned_as_is(self, vt):
        assert vt.apply_default("Analysis", "Purpose") == "Analysis"

    def test_none_returns_configured_default(self, vt):
        assert vt.apply_default(None, "Purpose") == "Tabulation"

    def test_empty_string_returns_configured_default(self, vt):
        assert vt.apply_default("", "Purpose") == "Tabulation"

    def test_no_configured_default_returns_none(self, vt):
        assert vt.apply_default(None, "NonExistent") is None

    def test_zero_is_falsy_returns_default(self, vt):
        """0 is falsy in Python; apply_default returns the default."""
        assert vt.apply_default(0, "Mandatory") == "No"


class TestTransformErrors:
    """Tests for error handling in transforms."""

    @pytest.fixture
    def vt(self):
        return ValueTransformer(TRANSFORMS, DEFAULTS)

    def test_unknown_transform_name_raises_key_error(self, vt):
        with pytest.raises(KeyError, match="Unknown transform"):
            vt.transform("value", "nonexistent_transform")

    def test_unsupported_transform_type_raises_value_error(self):
        transforms = {"bad": {"type": "unsupported_type"}}
        vt = ValueTransformer(transforms, {})
        with pytest.raises(ValueError, match="Unsupported transform type"):
            vt.transform("value", "bad")
