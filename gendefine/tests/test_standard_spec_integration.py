"""Integration tests for the Standard-Spec format (end-to-end pipeline)."""

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
from validator import DefineValidator
from oid_generator import OIDGenerator
from value_transformer import ValueTransformer


GENDEFINE_DIR = os.path.join(os.path.dirname(__file__), "..")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
MAPPINGS_DIR = os.path.join(GENDEFINE_DIR, "mappings")
SCHEMA_DIR = os.path.join(GENDEFINE_DIR, "..", "schema", "cdisc-define-2.1")
STANDARD_SPEC_XLSX = os.path.join(FIXTURES_DIR, "standard-spec-test.xlsx")
MAPPING_FILE = os.path.join(MAPPINGS_DIR, "standard-spec.json")


def _get_oids(path, element_name):
    tree = ET.parse(path)
    oids = set()
    for elem in tree.getroot().iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == element_name and "OID" in elem.attrib:
            oids.add(elem.attrib["OID"])
    return oids


def _count_elements(path):
    tree = ET.parse(path)
    counts = {}
    for elem in tree.getroot().iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        counts[tag] = counts.get(tag, 0) + 1
    return counts


@pytest.fixture(scope="module")
def pipeline():
    if not os.path.exists(STANDARD_SPEC_XLSX):
        pytest.skip("Standard-Spec test fixture not available")

    config = MappingConfig(MAPPING_FILE)
    reader = SpreadsheetReader(config)
    raw_data = reader.read_workbook(STANDARD_SPEC_XLSX)

    oid_gen = OIDGenerator()
    transformer = ValueTransformer(config.value_transforms, config.defaults)
    builder = IntermediateBuilder(config, oid_gen, transformer)
    intermediate = builder.build(raw_data)

    lang = config.global_settings.get("language", "en")
    define_builder = DefineBuilder(intermediate, lang)
    odm = define_builder.build()

    tmp = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
    xml_path = tmp.name
    tmp.close()
    odm.write_xml(xml_path)
    yield intermediate, odm, xml_path
    os.unlink(xml_path)


class TestFullPipelineStandardSpec:
    def test_output_is_valid_xml(self, pipeline):
        _, _, xml_path = pipeline
        tree = ET.parse(xml_path)
        assert tree.getroot() is not None

    def test_oids_follow_pattern_generation(self, pipeline):
        _, _, xml_path = pipeline
        # ItemGroupDef OIDs start with IG.
        for oid in _get_oids(xml_path, "ItemGroupDef"):
            assert oid.startswith("IG.")
        # MethodDef OIDs start with MT.
        for oid in _get_oids(xml_path, "MethodDef"):
            assert oid.startswith("MT.")

    def test_datasets_count(self, pipeline):
        intermediate, _, _ = pipeline
        assert len(intermediate["datasets"]) == 3

    def test_variables_count(self, pipeline):
        intermediate, _, _ = pipeline
        assert len(intermediate["variables"]) == 16


class TestWhereClausesGenerated:
    def test_where_clause_defs_present(self, pipeline):
        _, _, xml_path = pipeline
        counts = _count_elements(xml_path)
        assert counts.get("WhereClauseDef", 0) > 0

    def test_range_checks_have_correct_structure(self, pipeline):
        _, _, xml_path = pipeline
        tree = ET.parse(xml_path)
        for elem in tree.getroot().iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag == "RangeCheck":
                assert "Comparator" in elem.attrib
                assert "SoftHard" in elem.attrib
                # ItemOID may be namespaced (def:ItemOID)
                attrib_local = {k.split("}")[-1] if "}" in k else k: v
                                for k, v in elem.attrib.items()}
                assert "ItemOID" in attrib_local
                # Must have at least one CheckValue child
                check_values = [
                    c for c in elem
                    if (c.tag.split("}")[-1] if "}" in c.tag else c.tag) == "CheckValue"
                ]
                assert len(check_values) >= 1


class TestCodelistStubsGenerated:
    def test_codelist_stubs_in_intermediate(self, pipeline):
        intermediate, _, _ = pipeline
        cl_names = {cl["name"] for cl in intermediate["codelists"]}
        assert "SEX" in cl_names
        assert "VSTESTCD" in cl_names

    def test_codelist_stubs_not_in_xml(self, pipeline):
        """Stubs with empty terms should not appear in XML (would violate XSD)."""
        _, _, xml_path = pipeline
        counts = _count_elements(xml_path)
        # Codelist stubs have no terms, so they are excluded from XML output
        assert counts.get("CodeList", 0) == 0


class TestSchemaValidationStandardSpec:
    def test_schema_validation_passes(self, pipeline):
        _, _, xml_path = pipeline
        schema_path = os.path.join(SCHEMA_DIR, "define2-1-0.xsd")
        if not os.path.exists(schema_path):
            pytest.skip("Define-XML v2.1 schema not available")
        dv = DefineValidator()
        errors = dv.validate_schema(xml_path, schema_path)
        assert not errors, f"Schema validation errors: {errors}"
