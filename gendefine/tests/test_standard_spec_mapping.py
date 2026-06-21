"""Integration tests for Standard-Spec format mapping (Phase 3)."""

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
from oid_generator import OIDGenerator
from value_transformer import ValueTransformer


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
MAPPINGS_DIR = os.path.join(os.path.dirname(__file__), "..", "mappings")
SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "schema", "cdisc-define-2.1")


@pytest.fixture
def standard_spec_mapping():
    return os.path.join(MAPPINGS_DIR, "standard-spec.json")


@pytest.fixture
def standard_spec_xlsx():
    return os.path.join(FIXTURES_DIR, "standard-spec-test.xlsx")


@pytest.fixture
def pipeline_result(standard_spec_mapping, standard_spec_xlsx):
    """Run the full pipeline and return intermediate + odm."""
    config = MappingConfig(standard_spec_mapping)
    reader = SpreadsheetReader(config)
    raw_data = reader.read_workbook(standard_spec_xlsx)

    oid_gen = OIDGenerator()
    transformer = ValueTransformer(config.value_transforms, config.defaults)
    builder = IntermediateBuilder(config, oid_gen, transformer)
    intermediate = builder.build(raw_data)

    define_builder = DefineBuilder(intermediate, "en")
    odm = define_builder.build()

    return intermediate, odm


class TestMappingValidation:
    def test_standard_spec_mapping_validates_against_schema(self, standard_spec_mapping):
        config = MappingConfig(standard_spec_mapping)
        assert config.mapping_name == "standard-spec"
        assert config.define_version == "2.1"

    def test_oid_generation_strategy_is_pattern(self, standard_spec_mapping):
        config = MappingConfig(standard_spec_mapping)
        assert config.global_settings["oid_generation_strategy"] == "pattern"

    def test_where_clause_source_is_inline(self, standard_spec_mapping):
        config = MappingConfig(standard_spec_mapping)
        assert config.global_settings["where_clause_source"] == "inline"


class TestSpreadsheetReading:
    def test_reads_standard_worksheet(self, standard_spec_mapping, standard_spec_xlsx):
        config = MappingConfig(standard_spec_mapping)
        reader = SpreadsheetReader(config)
        raw_data = reader.read_workbook(standard_spec_xlsx)
        assert "Standard" in raw_data
        assert raw_data["Standard"]["StudyName"] == "SDTM-TEST"

    def test_reads_all_mapped_worksheets(self, standard_spec_mapping, standard_spec_xlsx):
        config = MappingConfig(standard_spec_mapping)
        reader = SpreadsheetReader(config)
        raw_data = reader.read_workbook(standard_spec_xlsx)
        assert "Datasets" in raw_data
        assert "Variables" in raw_data
        assert "ValueLevel" in raw_data
        assert "Methods" in raw_data
        assert "Comments" in raw_data
        assert "Documents" in raw_data


class TestIntermediateStructure:
    def test_study_metadata(self, pipeline_result):
        intermediate, _ = pipeline_result
        assert intermediate["study"]["study_name"] == "SDTM-TEST"
        assert intermediate["study"]["oid"] == "ODM.SDTM-TEST"

    def test_standards_generated_from_study(self, pipeline_result):
        intermediate, _ = pipeline_result
        assert len(intermediate["standards"]) == 1
        std = intermediate["standards"][0]
        assert std["name"] == "SDTMIG"
        assert std["version"] == "3.4"
        assert std["oid"] == "STD.1"

    def test_datasets_count(self, pipeline_result):
        intermediate, _ = pipeline_result
        assert len(intermediate["datasets"]) == 3
        names = [d["name"] for d in intermediate["datasets"]]
        assert "DM" in names
        assert "AE" in names
        assert "VS" in names

    def test_dataset_oids_follow_pattern(self, pipeline_result):
        intermediate, _ = pipeline_result
        for ds in intermediate["datasets"]:
            assert ds["oid"].startswith("IG.")
            assert ds["oid"] == f"IG.{ds['name']}".upper()

    def test_variables_count(self, pipeline_result):
        intermediate, _ = pipeline_result
        assert len(intermediate["variables"]) == 16

    def test_variable_oids_follow_pattern(self, pipeline_result):
        intermediate, _ = pipeline_result
        for var in intermediate["variables"]:
            expected = f"IT.{var['dataset']}.{var['name']}".upper()
            assert var["oid"] == expected

    def test_core_to_mandatory_transform(self, pipeline_result):
        intermediate, _ = pipeline_result
        vars_by_name = {}
        for v in intermediate["variables"]:
            vars_by_name[(v["dataset"], v["name"])] = v
        assert vars_by_name[("DM", "STUDYID")]["mandatory"] == "Yes"  # Req -> Yes
        assert vars_by_name[("DM", "AGE")]["mandatory"] == "No"       # Exp -> No

    def test_key_variables_assigned(self, pipeline_result):
        intermediate, _ = pipeline_result
        dm_vars = {v["name"]: v for v in intermediate["variables"] if v["dataset"] == "DM"}
        assert dm_vars["STUDYID"]["key_sequence"] == 1
        assert dm_vars["USUBJID"]["key_sequence"] == 2
        assert "key_sequence" not in dm_vars["SEX"]

    def test_value_levels_count(self, pipeline_result):
        intermediate, _ = pipeline_result
        assert len(intermediate["value_levels"]) == 3

    def test_where_clauses_from_inline(self, pipeline_result):
        intermediate, _ = pipeline_result
        wcs = intermediate["where_clauses"]
        assert len(wcs) == 3  # SYSBP, DIABP, PULSE AND VISITNUM

    def test_where_clause_compound(self, pipeline_result):
        intermediate, _ = pipeline_result
        # Find the compound where clause (PULSE AND VISITNUM)
        compound = [wc for wc in intermediate["where_clauses"]
                    if len(wc["range_checks"]) == 2]
        assert len(compound) == 1
        assert compound[0]["range_checks"][0]["item_oid"] == "IT.VS.VSTESTCD"
        assert compound[0]["range_checks"][1]["item_oid"] == "IT.VS.VISITNUM"

    def test_codelist_stubs_generated(self, pipeline_result):
        intermediate, _ = pipeline_result
        cl_names = [cl["name"] for cl in intermediate["codelists"]]
        assert "SEX" in cl_names
        assert "AESEV" in cl_names
        assert "VSTESTCD" in cl_names
        assert "VSTEST" in cl_names
        # All stubs have empty terms (not emitted in XML, but present in intermediate)
        for cl in intermediate["codelists"]:
            assert cl["terms"] == []
            assert cl["data_type"] == "text"

    def test_methods_with_pattern_oids(self, pipeline_result):
        intermediate, _ = pipeline_result
        assert len(intermediate["methods"]) == 2
        oids = [m["oid"] for m in intermediate["methods"]]
        assert "MT.DERIVE_SYSBP" in oids
        assert "MT.DERIVE_DIABP" in oids

    def test_comments_with_pattern_oids(self, pipeline_result):
        intermediate, _ = pipeline_result
        assert len(intermediate["comments"]) == 1
        assert intermediate["comments"][0]["oid"] == "COM.1"

    def test_documents(self, pipeline_result):
        intermediate, _ = pipeline_result
        assert len(intermediate["documents"]) == 2

    def test_default_purpose_applied(self, pipeline_result):
        intermediate, _ = pipeline_result
        for ds in intermediate["datasets"]:
            assert ds["purpose"] == "Tabulation"

    def test_informational_columns_excluded(self, pipeline_result):
        """Developer Notes and Variant should not appear in intermediate output."""
        intermediate, _ = pipeline_result
        for var in intermediate["variables"]:
            assert "developer_notes" not in var
            assert "variant" not in var


class TestDefineXMLGeneration:
    def test_generates_valid_xml(self, pipeline_result):
        _, odm = pipeline_result
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            tmpfile = f.name
        try:
            odm.write_xml(tmpfile)
            tree = ET.parse(tmpfile)
            root = tree.getroot()
            assert root is not None
        finally:
            os.unlink(tmpfile)

    def test_expected_element_counts(self, pipeline_result):
        _, odm = pipeline_result
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            tmpfile = f.name
        try:
            odm.write_xml(tmpfile)
            tree = ET.parse(tmpfile)
            root = tree.getroot()
            counts = {}
            for elem in root.iter():
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                counts[tag] = counts.get(tag, 0) + 1

            # Verify key element counts
            assert counts.get("ItemGroupDef", 0) == 3   # DM, AE, VS
            assert counts.get("Standard", 0) == 1        # SDTMIG
            assert counts.get("MethodDef", 0) == 2       # DERIVE_SYSBP, DERIVE_DIABP
            assert counts.get("CommentDef", 0) == 1
            assert counts.get("WhereClauseDef", 0) == 3  # 3 unique where clauses
            assert counts.get("ValueListDef", 0) == 1    # VL for VSSTRESN
        finally:
            os.unlink(tmpfile)

    def test_oids_follow_patterns(self, pipeline_result):
        _, odm = pipeline_result
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            tmpfile = f.name
        try:
            odm.write_xml(tmpfile)
            tree = ET.parse(tmpfile)
            root = tree.getroot()
            ns = {"odm": "http://www.cdisc.org/ns/odm/v1.3",
                  "def": "http://www.cdisc.org/ns/def/v2.1"}

            # Check ItemGroupDef OIDs
            for igd in root.iter("{http://www.cdisc.org/ns/odm/v1.3}ItemGroupDef"):
                oid = igd.get("OID")
                assert oid.startswith("IG.")

            # Check MethodDef OIDs
            for md in root.iter("{http://www.cdisc.org/ns/odm/v1.3}MethodDef"):
                oid = md.get("OID")
                assert oid.startswith("MT.")
        finally:
            os.unlink(tmpfile)

    def test_schema_validation(self, pipeline_result):
        """Validate against Define-XML v2.1 XSD if available.

        Note: Codelist stubs (empty terms) are excluded from the XML since they
        violate the XSD. Variables may reference codelists that don't appear in
        the output — this is a known limitation when codelist terms are not
        populated. The schema validation should still pass because empty CodeList
        elements are not emitted.
        """
        schema_path = os.path.join(SCHEMA_DIR, "define2-1-0.xsd")
        if not os.path.exists(schema_path):
            pytest.skip("Define-XML v2.1 schema not available")

        _, odm = pipeline_result
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            tmpfile = f.name
        try:
            odm.write_xml(tmpfile)
            from validator import DefineValidator
            validator = DefineValidator()
            errors = validator.validate_schema(tmpfile, schema_path)
            assert not errors, f"Schema validation errors: {errors}"
        finally:
            os.unlink(tmpfile)


class TestSubclass:
    def test_subclass_in_datasets(self, pipeline_result):
        intermediate, _ = pipeline_result
        ae_ds = [d for d in intermediate["datasets"] if d["name"] == "AE"][0]
        assert ae_ds["subclass_name"] == "Adverse Event"
