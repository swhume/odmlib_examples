"""Tests for where_clause_parser.py"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from where_clause_parser import WhereClauseParser


class TestParseSimple:
    def test_simple_eq_expression(self):
        parser = WhereClauseParser()
        result = parser.parse("TESTCD EQ SYSBP", "VS")
        assert len(result) == 1
        assert result[0]["variable"] == "TESTCD"
        assert result[0]["comparator"] == "EQ"
        assert result[0]["value"] == "SYSBP"
        assert result[0]["dataset"] == "VS"

    def test_simple_ne_expression(self):
        parser = WhereClauseParser()
        result = parser.parse("STATUS NE ACTIVE", "DM")
        assert result[0]["comparator"] == "NE"
        assert result[0]["value"] == "ACTIVE"

    def test_simple_lt_expression(self):
        parser = WhereClauseParser()
        result = parser.parse("AGE LT 65", "DM")
        assert result[0]["comparator"] == "LT"
        assert result[0]["value"] == "65"

    def test_simple_ge_expression(self):
        parser = WhereClauseParser()
        result = parser.parse("VISITNUM GE 2", "VS")
        assert result[0]["comparator"] == "GE"


class TestParseCompound:
    def test_compound_and_expression(self):
        parser = WhereClauseParser()
        result = parser.parse("TESTCD EQ SYSBP AND POSITION EQ STANDING", "VS")
        assert len(result) == 2
        assert result[0]["variable"] == "TESTCD"
        assert result[0]["comparator"] == "EQ"
        assert result[0]["value"] == "SYSBP"
        assert result[1]["variable"] == "POSITION"
        assert result[1]["comparator"] == "EQ"
        assert result[1]["value"] == "STANDING"

    def test_compound_three_conditions(self):
        parser = WhereClauseParser()
        result = parser.parse("A EQ 1 AND B EQ 2 AND C EQ 3", "DS")
        assert len(result) == 3


class TestParseIN:
    def test_in_operator(self):
        parser = WhereClauseParser()
        result = parser.parse("TESTCD IN (SYSBP, DIABP)", "VS")
        assert len(result) == 1
        assert result[0]["variable"] == "TESTCD"
        assert result[0]["comparator"] == "IN"
        assert result[0]["value"] == ["SYSBP", "DIABP"]

    def test_notin_operator(self):
        parser = WhereClauseParser()
        result = parser.parse("TESTCD NOTIN (TEMP, WEIGHT)", "VS")
        assert len(result) == 1
        assert result[0]["comparator"] == "NOTIN"
        assert result[0]["value"] == ["TEMP", "WEIGHT"]

    def test_in_with_single_value(self):
        parser = WhereClauseParser()
        result = parser.parse("TESTCD IN (SYSBP)", "VS")
        assert result[0]["value"] == ["SYSBP"]


class TestParseEdgeCases:
    def test_extra_whitespace(self):
        parser = WhereClauseParser()
        result = parser.parse("  TESTCD   EQ   SYSBP  ", "VS")
        assert len(result) == 1
        assert result[0]["variable"] == "TESTCD"
        assert result[0]["value"] == "SYSBP"

    def test_empty_expression_returns_empty(self):
        parser = WhereClauseParser()
        assert parser.parse("", "VS") == []
        assert parser.parse(None, "VS") == []
        assert parser.parse("   ", "VS") == []

    def test_malformed_expression_returns_partial(self):
        parser = WhereClauseParser()
        result = parser.parse("TESTCD EQ SYSBP AND BADCONDITION", "VS")
        # First condition should parse, second should be skipped with warning
        assert len(result) == 1
        assert result[0]["variable"] == "TESTCD"


class TestBuildWhereClauseDefs:
    def test_builds_unique_oids_per_expression(self):
        parser = WhereClauseParser()
        rows = [
            {"where_clause_expr": "TESTCD EQ SYSBP", "dataset": "VS"},
            {"where_clause_expr": "TESTCD EQ DIABP", "dataset": "VS"},
        ]
        wcs, expr_map = parser.build_where_clause_defs(rows, "WC.{Dataset}.{Variable}.{Value}")
        assert len(wcs) == 2
        assert wcs[0]["oid"] != wcs[1]["oid"]
        assert len(expr_map) == 2

    def test_duplicate_expressions_produce_single_def(self):
        parser = WhereClauseParser()
        rows = [
            {"where_clause_expr": "TESTCD EQ SYSBP", "dataset": "VS"},
            {"where_clause_expr": "TESTCD EQ SYSBP", "dataset": "VS"},
        ]
        wcs, expr_map = parser.build_where_clause_defs(rows, "WC.{Dataset}.{Variable}.{Value}")
        assert len(wcs) == 1
        assert len(expr_map) == 1

    def test_range_checks_structure(self):
        parser = WhereClauseParser()
        rows = [
            {"where_clause_expr": "TESTCD EQ SYSBP AND POSITION EQ STANDING", "dataset": "VS"},
        ]
        wcs, _ = parser.build_where_clause_defs(rows, "WC.{Dataset}.{Variable}.{Value}")
        assert len(wcs) == 1
        assert len(wcs[0]["range_checks"]) == 2
        assert wcs[0]["range_checks"][0]["item_oid"] == "IT.VS.TESTCD"
        assert wcs[0]["range_checks"][1]["item_oid"] == "IT.VS.POSITION"

    def test_empty_rows_return_empty(self):
        parser = WhereClauseParser()
        wcs, expr_map = parser.build_where_clause_defs([], "WC.{Dataset}.{Variable}.{Value}")
        assert wcs == []
        assert expr_map == {}
