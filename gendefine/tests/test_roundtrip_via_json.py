"""Integration test: verify extract-only -> generate-only roundtrip matches full pipeline."""

import json
import os
import sys
import tempfile
import xml.etree.ElementTree as ET

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

# Standard-Spec test fixture
STANDARD_SPEC_XLSX = os.path.join(GENDEFINE_DIR, "tests", "fixtures", "standard-spec-test.xlsx")
STANDARD_SPEC_MAPPING = os.path.join(MAPPINGS_DIR, "standard-spec.json")


def _flatten_elements(path):
    """Return list of (tag, attribs, text) for all elements (excluding ODM root)."""
    tree = ET.parse(path)
    result = []
    for elem in tree.getroot().iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "ODM":
            continue
        result.append((tag, dict(sorted(elem.attrib.items())), (elem.text or "").strip()))
    return result


def _run_extract(config, xlsx_path):
    """Run extract step and return intermediate JSON dict."""
    reader = SpreadsheetReader(config)
    raw_data = reader.read_workbook(xlsx_path)
    oid_gen = OIDGenerator()
    transformer = ValueTransformer(config.value_transforms, config.defaults)
    builder = IntermediateBuilder(config, oid_gen, transformer)
    intermediate = builder.build(raw_data)
    intermediate["source_file"] = xlsx_path
    return intermediate


def _generate_xml(intermediate, lang="en"):
    """Run generate step and return path to output XML."""
    define_builder = DefineBuilder(intermediate, lang)
    odm = define_builder.build()
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        output_path = f.name
    odm.write_xml(output_path)
    return output_path


class TestOdmlibFormatRoundtrip:
    """Test roundtrip via intermediate JSON for odmlib format."""

    @pytest.fixture(scope="class")
    def roundtrip_paths(self):
        if not os.path.exists(INPUT_XLSX):
            pytest.skip("Test data not available: odmlib-define-metadata.xlsx")

        config = MappingConfig(ODMLIB_MAPPING)
        lang = config.global_settings.get("language", "en")

        # Full pipeline
        intermediate_direct = _run_extract(config, INPUT_XLSX)
        full_xml = _generate_xml(intermediate_direct, lang)

        # Roundtrip via JSON file (extract -> save -> load -> generate)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json_path = f.name
            json.dump(intermediate_direct, f, indent=2, default=str, ensure_ascii=False)

        with open(json_path) as f:
            intermediate_loaded = json.load(f)

        roundtrip_xml = _generate_xml(intermediate_loaded, lang)

        yield full_xml, roundtrip_xml, json_path

        os.unlink(full_xml)
        os.unlink(roundtrip_xml)
        os.unlink(json_path)

    def test_intermediate_json_validates(self, roundtrip_paths):
        _, _, json_path = roundtrip_paths
        with open(json_path) as f:
            data = json.load(f)
        iv = IntermediateValidator()
        errors = iv.validate_schema(data)
        assert errors == [], f"Schema errors: {errors}"

    def test_element_counts_match(self, roundtrip_paths):
        full_xml, roundtrip_xml, _ = roundtrip_paths
        full_flat = _flatten_elements(full_xml)
        rt_flat = _flatten_elements(roundtrip_xml)
        assert len(full_flat) == len(rt_flat), \
            f"Element count mismatch: full={len(full_flat)} roundtrip={len(rt_flat)}"

    def test_all_elements_match(self, roundtrip_paths):
        full_xml, roundtrip_xml, _ = roundtrip_paths
        full_flat = _flatten_elements(full_xml)
        rt_flat = _flatten_elements(roundtrip_xml)
        for i, (ff, rf) in enumerate(zip(full_flat, rt_flat)):
            ftag, fattrs, ftext = ff
            rtag, rattrs, rtext = rf
            assert ftag == rtag, f"Element {i}: tag mismatch full={ftag} rt={rtag}"
            assert fattrs == rattrs, f"Element {i} ({ftag}): attr mismatch"
            assert ftext == rtext, f"Element {i} ({ftag}): text mismatch"


class TestStandardSpecRoundtrip:
    """Test roundtrip via intermediate JSON for Standard-Spec format."""

    @pytest.fixture(scope="class")
    def roundtrip_paths(self):
        if not os.path.exists(STANDARD_SPEC_XLSX):
            pytest.skip("Standard-Spec test fixture not available")

        config = MappingConfig(STANDARD_SPEC_MAPPING)
        lang = config.global_settings.get("language", "en")

        # Full pipeline
        intermediate_direct = _run_extract(config, STANDARD_SPEC_XLSX)
        full_xml = _generate_xml(intermediate_direct, lang)

        # Roundtrip via JSON file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json_path = f.name
            json.dump(intermediate_direct, f, indent=2, default=str, ensure_ascii=False)

        with open(json_path) as f:
            intermediate_loaded = json.load(f)

        roundtrip_xml = _generate_xml(intermediate_loaded, lang)

        yield full_xml, roundtrip_xml, json_path

        os.unlink(full_xml)
        os.unlink(roundtrip_xml)
        os.unlink(json_path)

    def test_intermediate_json_validates(self, roundtrip_paths):
        _, _, json_path = roundtrip_paths
        with open(json_path) as f:
            data = json.load(f)
        iv = IntermediateValidator()
        errors = iv.validate_schema(data)
        assert errors == [], f"Schema errors: {errors}"

    def test_element_counts_match(self, roundtrip_paths):
        full_xml, roundtrip_xml, _ = roundtrip_paths
        full_flat = _flatten_elements(full_xml)
        rt_flat = _flatten_elements(roundtrip_xml)
        assert len(full_flat) == len(rt_flat), \
            f"Element count mismatch: full={len(full_flat)} roundtrip={len(rt_flat)}"

    def test_all_elements_match(self, roundtrip_paths):
        full_xml, roundtrip_xml, _ = roundtrip_paths
        full_flat = _flatten_elements(full_xml)
        rt_flat = _flatten_elements(roundtrip_xml)
        for i, (ff, rf) in enumerate(zip(full_flat, rt_flat)):
            ftag, fattrs, ftext = ff
            rtag, rattrs, rtext = rf
            assert ftag == rtag, f"Element {i}: tag mismatch full={ftag} rt={rtag}"
            assert fattrs == rattrs, f"Element {i} ({ftag}): attr mismatch"
            assert ftext == rtext, f"Element {i} ({ftag}): text mismatch"
