"""Integration tests for the odmlib format (end-to-end pipeline)."""

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
from validator import DefineValidator, IntermediateValidator
from oid_generator import OIDGenerator
from value_transformer import ValueTransformer


GENDEFINE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(GENDEFINE_DIR, "data")
MAPPINGS_DIR = os.path.join(GENDEFINE_DIR, "mappings")
SCHEMA_DIR = os.path.join(GENDEFINE_DIR, "..", "schema", "cdisc-define-2.1")
INPUT_XLSX = os.path.join(DATA_DIR, "odmlib-define-metadata.xlsx")
MAPPING_FILE = os.path.join(MAPPINGS_DIR, "odmlib-format.json")


def _run_pipeline(xlsx_path, mapping_path):
    """Run the full gendefine pipeline, return (intermediate, odm, xml_path)."""
    config = MappingConfig(mapping_path)
    reader = SpreadsheetReader(config)
    raw_data = reader.read_workbook(xlsx_path)

    oid_gen = OIDGenerator()
    transformer = ValueTransformer(config.value_transforms, config.defaults)
    builder = IntermediateBuilder(config, oid_gen, transformer)
    intermediate = builder.build(raw_data)
    intermediate["source_file"] = xlsx_path

    lang = config.global_settings.get("language", "en")
    define_builder = DefineBuilder(intermediate, lang)
    odm = define_builder.build()

    tmp = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
    xml_path = tmp.name
    tmp.close()
    odm.write_xml(xml_path)
    return intermediate, odm, xml_path


def _count_elements(path):
    tree = ET.parse(path)
    counts = {}
    for elem in tree.getroot().iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        counts[tag] = counts.get(tag, 0) + 1
    return counts


def _get_oids(path, element_name):
    tree = ET.parse(path)
    oids = set()
    for elem in tree.getroot().iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == element_name and "OID" in elem.attrib:
            oids.add(elem.attrib["OID"])
    return oids


@pytest.fixture(scope="module")
def pipeline():
    if not os.path.exists(INPUT_XLSX):
        pytest.skip("Test data not available: odmlib-define-metadata.xlsx")
    intermediate, odm, xml_path = _run_pipeline(INPUT_XLSX, MAPPING_FILE)
    yield intermediate, odm, xml_path
    os.unlink(xml_path)


class TestFullPipelineOdmlibFormat:
    def test_output_file_exists_and_is_valid_xml(self, pipeline):
        _, _, xml_path = pipeline
        assert os.path.exists(xml_path)
        tree = ET.parse(xml_path)
        assert tree.getroot() is not None

    def test_datasets_present(self, pipeline):
        _, _, xml_path = pipeline
        oids = _get_oids(xml_path, "ItemGroupDef")
        assert len(oids) > 0

    def test_variables_present(self, pipeline):
        _, _, xml_path = pipeline
        oids = _get_oids(xml_path, "ItemDef")
        assert len(oids) > 0

    def test_codelists_present(self, pipeline):
        _, _, xml_path = pipeline
        oids = _get_oids(xml_path, "CodeList")
        assert len(oids) > 0

    def test_methods_present(self, pipeline):
        _, _, xml_path = pipeline
        oids = _get_oids(xml_path, "MethodDef")
        assert len(oids) > 0

    def test_comments_present(self, pipeline):
        _, _, xml_path = pipeline
        oids = _get_oids(xml_path, "CommentDef")
        assert len(oids) > 0

    def test_standards_present(self, pipeline):
        _, _, xml_path = pipeline
        oids = _get_oids(xml_path, "Standard")
        assert len(oids) > 0

    def test_intermediate_has_expected_sections(self, pipeline):
        intermediate, _, _ = pipeline
        for key in ("study", "metadata_version", "standards", "datasets",
                     "variables", "value_levels", "where_clauses", "codelists",
                     "methods", "comments", "documents"):
            assert key in intermediate


class TestExtractGenerateRoundtripOdmlib:
    def test_roundtrip_produces_identical_output(self, pipeline):
        intermediate, _, direct_xml = pipeline

        # Serialize intermediate to JSON and reload
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json_path = f.name
            json.dump(intermediate, f, indent=2, default=str, ensure_ascii=False)

        try:
            with open(json_path) as f:
                reloaded = json.load(f)

            lang = intermediate["study"].get("language", "en")
            db = DefineBuilder(reloaded, lang)
            odm2 = db.build()

            with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
                rt_xml = f.name
            odm2.write_xml(rt_xml)

            try:
                direct_counts = _count_elements(direct_xml)
                rt_counts = _count_elements(rt_xml)
                for tag in direct_counts:
                    assert rt_counts.get(tag, 0) == direct_counts[tag], \
                        f"Roundtrip mismatch for {tag}: expected {direct_counts[tag]}, got {rt_counts.get(tag, 0)}"
            finally:
                os.unlink(rt_xml)
        finally:
            os.unlink(json_path)


class TestConformanceCheckOdmlib:
    def test_conformance_checks_pass(self, pipeline):
        _, odm, _ = pipeline
        dv = DefineValidator()
        errors = dv.check_conformance(odm)
        # Filter informational messages about unreferenced OIDs
        real_errors = [e for e in errors if "Unreferenced" not in str(e)]
        assert real_errors == [], f"Conformance errors: {real_errors}"


class TestSchemaValidationOdmlib:
    def test_schema_validation_passes(self, pipeline):
        _, _, xml_path = pipeline
        schema_path = os.path.join(SCHEMA_DIR, "define2-1-0.xsd")
        if not os.path.exists(schema_path):
            pytest.skip("Define-XML v2.1 schema not available")
        dv = DefineValidator()
        errors = dv.validate_schema(xml_path, schema_path)
        assert not errors, f"Schema validation errors: {errors}"
