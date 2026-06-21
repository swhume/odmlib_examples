"""Cross-format consistency tests: verify architectural invariants across both formats."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config_loader import MappingConfig
from spreadsheet_reader import SpreadsheetReader
from intermediate_builder import IntermediateBuilder
from validator import IntermediateValidator
from oid_generator import OIDGenerator
from value_transformer import ValueTransformer


GENDEFINE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(GENDEFINE_DIR, "data")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
MAPPINGS_DIR = os.path.join(GENDEFINE_DIR, "mappings")

ODMLIB_XLSX = os.path.join(DATA_DIR, "odmlib-define-metadata.xlsx")
ODMLIB_MAPPING = os.path.join(MAPPINGS_DIR, "odmlib-format.json")
STANDARD_SPEC_XLSX = os.path.join(FIXTURES_DIR, "standard-spec-test.xlsx")
STANDARD_SPEC_MAPPING = os.path.join(MAPPINGS_DIR, "standard-spec.json")
MAPPING_SCHEMA = os.path.join(MAPPINGS_DIR, "mapping_schema.json")


def _extract_intermediate(xlsx_path, mapping_path):
    config = MappingConfig(mapping_path)
    reader = SpreadsheetReader(config)
    raw_data = reader.read_workbook(xlsx_path)
    oid_gen = OIDGenerator()
    transformer = ValueTransformer(config.value_transforms, config.defaults)
    builder = IntermediateBuilder(config, oid_gen, transformer)
    intermediate = builder.build(raw_data)
    intermediate["source_file"] = xlsx_path
    return intermediate


class TestIntermediateJsonSchemaCompliance:
    def test_odmlib_format_validates(self):
        if not os.path.exists(ODMLIB_XLSX):
            pytest.skip("odmlib test data not available")
        intermediate = _extract_intermediate(ODMLIB_XLSX, ODMLIB_MAPPING)
        iv = IntermediateValidator()
        errors = iv.validate_schema(intermediate)
        assert errors == [], f"Schema errors for odmlib format: {errors}"

    def test_standard_spec_format_validates(self):
        if not os.path.exists(STANDARD_SPEC_XLSX):
            pytest.skip("Standard-Spec test fixture not available")
        intermediate = _extract_intermediate(STANDARD_SPEC_XLSX, STANDARD_SPEC_MAPPING)
        iv = IntermediateValidator()
        errors = iv.validate_schema(intermediate)
        assert errors == [], f"Schema errors for Standard-Spec format: {errors}"


class TestMappingSchemaCompliance:
    def test_odmlib_mapping_validates(self):
        config = MappingConfig(ODMLIB_MAPPING)
        assert config.mapping_name == "odmlib-format"
        assert config.define_version == "2.1"

    def test_standard_spec_mapping_validates(self):
        config = MappingConfig(STANDARD_SPEC_MAPPING)
        assert config.mapping_name == "standard-spec"
        assert config.define_version == "2.1"

    def test_all_mapping_files_in_directory_validate(self):
        """Every .json file in mappings/ (except schemas) should validate as a mapping."""
        schema_files = {"mapping_schema.json", "intermediate_schema.json"}
        for filename in os.listdir(MAPPINGS_DIR):
            if not filename.endswith(".json") or filename in schema_files:
                continue
            path = os.path.join(MAPPINGS_DIR, filename)
            config = MappingConfig(path)
            assert config.mapping_name, f"{filename} has no mapping_name"
            assert config.define_version, f"{filename} has no define_version"
