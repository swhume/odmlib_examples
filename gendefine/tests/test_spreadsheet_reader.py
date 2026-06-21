"""Tests for spreadsheet_reader.py"""

import os
import sys
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openpyxl import Workbook
from spreadsheet_reader import SpreadsheetReader
from config_loader import MappingConfig


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _create_test_workbook(tmp_path, sheets_data):
    """Helper: create a test workbook with specified sheet data.

    sheets_data is a dict of sheet_name -> list of rows (each row is a list of values).
    First row of tabular sheets is the header.
    """
    wb = Workbook()
    first = True
    for sheet_name, rows in sheets_data.items():
        if first:
            ws = wb.active
            ws.title = sheet_name
            first = False
        else:
            ws = wb.create_sheet(sheet_name)
        for row in rows:
            ws.append(row)
    path = str(tmp_path / "test.xlsx")
    wb.save(path)
    return path


class TestReadTabularSheet:
    def test_reads_correct_rows_and_columns(self, tmp_path):
        xlsx_path = _create_test_workbook(tmp_path, {
            "Datasets": [
                ["OID", "Dataset", "Description"],
                ["IG.DM", "DM", "Demographics"],
                ["IG.AE", "AE", "Adverse Events"],
            ]
        })
        config = MappingConfig(os.path.join(FIXTURES_DIR, "test-mapping.json"))
        reader = SpreadsheetReader(config)
        result = reader.read_workbook(xlsx_path)
        assert "Datasets" in result
        rows = result["Datasets"]
        assert len(rows) == 2
        assert rows[0]["OID"] == "IG.DM"
        assert rows[0]["Dataset"] == "DM"
        assert rows[0]["Description"] == "Demographics"
        assert rows[1]["OID"] == "IG.AE"

    def test_empty_worksheet_produces_empty_list(self, tmp_path):
        xlsx_path = _create_test_workbook(tmp_path, {
            "Datasets": [
                ["OID", "Dataset", "Description"],
            ]
        })
        config = MappingConfig(os.path.join(FIXTURES_DIR, "test-mapping.json"))
        reader = SpreadsheetReader(config)
        result = reader.read_workbook(xlsx_path)
        assert result["Datasets"] == []


class TestReadAttributeValueSheet:
    def test_reads_key_value_pairs(self, tmp_path):
        xlsx_path = _create_test_workbook(tmp_path, {
            "Study": [
                ["StudyName", "TESTNAME"],
                ["StudyDescription", "A test study"],
                ["ProtocolName", "TESTNAME"],
            ]
        })
        config = MappingConfig(os.path.join(FIXTURES_DIR, "test-mapping.json"))
        reader = SpreadsheetReader(config)
        result = reader.read_workbook(xlsx_path)
        assert "Study" in result
        data = result["Study"]
        assert data["StudyName"] == "TESTNAME"
        assert data["StudyDescription"] == "A test study"
        assert data["ProtocolName"] == "TESTNAME"


class TestUnmappedWorksheets:
    def test_unmapped_worksheets_skipped(self, tmp_path):
        xlsx_path = _create_test_workbook(tmp_path, {
            "Study": [
                ["StudyName", "TEST"],
            ],
            "UnknownSheet": [
                ["Col1", "Col2"],
                ["a", "b"],
            ],
        })
        config = MappingConfig(os.path.join(FIXTURES_DIR, "test-mapping.json"))
        reader = SpreadsheetReader(config)
        result = reader.read_workbook(xlsx_path)
        assert "Study" in result
        assert "UnknownSheet" not in result


class TestColumnMapping:
    def test_raw_column_names_preserved(self, tmp_path):
        """SpreadsheetReader returns raw column names, not mapped names."""
        xlsx_path = _create_test_workbook(tmp_path, {
            "Variables": [
                ["OID", "Order", "Dataset", "Variable"],
                ["IT.DM.STUDYID", 1, "DM", "STUDYID"],
            ]
        })
        config = MappingConfig(os.path.join(FIXTURES_DIR, "test-mapping.json"))
        reader = SpreadsheetReader(config)
        result = reader.read_workbook(xlsx_path)
        row = result["Variables"][0]
        # Raw column names from spreadsheet header
        assert row["OID"] == "IT.DM.STUDYID"
        assert row["Order"] == 1
        assert row["Dataset"] == "DM"
        assert row["Variable"] == "STUDYID"
