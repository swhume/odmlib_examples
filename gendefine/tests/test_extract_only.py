"""Tests for extract-only mode."""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config_loader import MappingConfig
from spreadsheet_reader import SpreadsheetReader
from intermediate_builder import IntermediateBuilder
from define_builder import DefineBuilder
from validator import IntermediateValidator
from oid_generator import OIDGenerator
from value_transformer import ValueTransformer

GENDEFINE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(GENDEFINE_DIR, "data")
MAPPINGS_DIR = os.path.join(GENDEFINE_DIR, "mappings")
INPUT_XLSX = os.path.join(DATA_DIR, "odmlib-define-metadata.xlsx")
ODMLIB_MAPPING = os.path.join(MAPPINGS_DIR, "odmlib-format.json")


def _requires_test_data():
    if not os.path.exists(INPUT_XLSX):
        pytest.skip("Test data not available: odmlib-define-metadata.xlsx")


@pytest.fixture(scope="module")
def extracted_json():
    """Run extract step and return the intermediate JSON dict + path."""
    _requires_test_data()
    config = MappingConfig(ODMLIB_MAPPING)
    reader = SpreadsheetReader(config)
    raw_data = reader.read_workbook(INPUT_XLSX)

    oid_gen = OIDGenerator()
    transformer = ValueTransformer(config.value_transforms, config.defaults)
    builder = IntermediateBuilder(config, oid_gen, transformer)
    intermediate = builder.build(raw_data)
    intermediate["source_file"] = INPUT_XLSX

    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    json.dump(intermediate, tmp, indent=2, default=str, ensure_ascii=False)
    tmp.close()

    yield intermediate, tmp.name
    os.unlink(tmp.name)


class TestExtractOnlyProducesValidJSON:
    def test_json_file_written(self, extracted_json):
        _, path = extracted_json
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert data["gendefine_version"] == "1.0"

    def test_validates_against_schema(self, extracted_json):
        data, _ = extracted_json
        iv = IntermediateValidator()
        errors = iv.validate_schema(data)
        assert errors == [], f"Schema errors: {errors}"


class TestExtractionProvenance:
    def test_source_mapping_populated(self, extracted_json):
        data, _ = extracted_json
        assert data["source_mapping"] == "odmlib-format"

    def test_source_file_populated(self, extracted_json):
        data, _ = extracted_json
        assert data["source_file"] == INPUT_XLSX


class TestExtractionCounts:
    def test_has_datasets(self, extracted_json):
        data, _ = extracted_json
        assert len(data["datasets"]) > 0

    def test_has_variables(self, extracted_json):
        data, _ = extracted_json
        assert len(data["variables"]) > 0

    def test_has_codelists(self, extracted_json):
        data, _ = extracted_json
        assert len(data["codelists"]) > 0

    def test_has_methods(self, extracted_json):
        data, _ = extracted_json
        assert len(data["methods"]) > 0

    def test_has_comments(self, extracted_json):
        data, _ = extracted_json
        assert len(data["comments"]) > 0

    def test_has_documents(self, extracted_json):
        data, _ = extracted_json
        assert len(data["documents"]) > 0

    def test_has_value_levels(self, extracted_json):
        data, _ = extracted_json
        assert len(data["value_levels"]) > 0

    def test_has_where_clauses(self, extracted_json):
        data, _ = extracted_json
        assert len(data["where_clauses"]) > 0


class TestExtractOnlyCLIRequirements:
    def test_extract_only_requires_json_flag(self):
        """Verify that --extract-only without -j is rejected."""
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(GENDEFINE_DIR, "gendefine.py"),
             "--extract-only", "-e", "dummy.xlsx", "-m", "dummy.json"],
            capture_output=True, text=True,
            cwd=GENDEFINE_DIR
        )
        assert result.returncode != 0
        assert "requires -j" in result.stdout

    def test_extract_only_requires_excel_and_mapping(self):
        """Verify that --extract-only without -e and -m is rejected."""
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(GENDEFINE_DIR, "gendefine.py"),
             "--extract-only", "-j", "output.json"],
            capture_output=True, text=True,
            cwd=GENDEFINE_DIR
        )
        assert result.returncode != 0
        assert "requires -e" in result.stdout
