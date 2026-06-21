"""Tests for intermediate_builder.py"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from intermediate_builder import IntermediateBuilder
from config_loader import MappingConfig
from oid_generator import OIDGenerator
from value_transformer import ValueTransformer


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _make_builder(mapping_file=None):
    if mapping_file is None:
        mapping_file = os.path.join(FIXTURES_DIR, "test-mapping.json")
    config = MappingConfig(mapping_file)
    oid_gen = OIDGenerator()
    transformer = ValueTransformer(config.value_transforms, config.defaults)
    return IntermediateBuilder(config, oid_gen, transformer)


class TestBuildStudy:
    def test_study_metadata_from_study_worksheet(self):
        builder = _make_builder()
        raw_data = {"Study": {"StudyName": "TESTSTUDY", "StudyDescription": "A study",
                              "ProtocolName": "TESTSTUDY", "Language": "en",
                              "Annotated CRF": "LF.acrf"}}
        result = builder.build(raw_data)
        assert result["study"]["oid"] == "ODM.TESTSTUDY"
        assert result["study"]["study_name"] == "TESTSTUDY"
        assert result["study"]["study_description"] == "A study"
        assert result["study"]["protocol_name"] == "TESTSTUDY"
        assert result["study"]["language"] == "en"

    def test_metadata_version_derived_from_study(self):
        builder = _make_builder()
        raw_data = {"Study": {"StudyName": "ABC123"}}
        result = builder.build(raw_data)
        assert result["metadata_version"]["oid"] == "MDV.ABC123"
        assert result["metadata_version"]["name"] == "MDV ABC123"
        assert result["metadata_version"]["description"] == "Data Definitions for ABC123"


class TestBuildDatasets:
    def test_dataset_with_oid_from_column(self):
        builder = _make_builder()
        raw_data = {
            "Study": {"StudyName": "TEST"},
            "Datasets": [
                {"OID": "IG.DM", "Dataset": "DM", "Description": "Demographics",
                 "Class": "SPECIAL PURPOSE", "Structure": "One rec per subject",
                 "Purpose": "Tabulation", "Repeating": "No", "Reference Data": "No"}
            ]
        }
        result = builder.build(raw_data)
        ds = result["datasets"][0]
        assert ds["oid"] == "IG.DM"
        assert ds["name"] == "DM"
        assert ds["description"] == "Demographics"
        assert ds["class_name"] == "SPECIAL PURPOSE"
        assert ds["purpose"] == "Tabulation"
        assert ds["archive_location_id"] == "LF.DM"

    def test_optional_attributes_included_when_present(self):
        builder = _make_builder()
        raw_data = {
            "Study": {"StudyName": "TEST"},
            "Datasets": [
                {"OID": "IG.DM", "Dataset": "DM", "Description": "Demo",
                 "Structure": "s", "Purpose": "Tab", "Repeating": "No",
                 "Reference Data": "No", "Comment": "COM.1",
                 "IsNonStandard": "Yes", "StandardOID": "STD.1", "HasNoData": "Yes"}
            ]
        }
        result = builder.build(raw_data)
        ds = result["datasets"][0]
        assert ds["comment_oid"] == "COM.1"
        assert ds["is_non_standard"] == "Yes"
        assert ds["standard_oid"] == "STD.1"
        assert ds["has_no_data"] == "Yes"


class TestBuildVariables:
    def test_variable_grouped_by_dataset(self):
        builder = _make_builder()
        raw_data = {
            "Study": {"StudyName": "TEST"},
            "Variables": [
                {"OID": "IT.DM.STUDYID", "Order": 1, "Dataset": "DM",
                 "Variable": "STUDYID", "Label": "Study ID", "Data Type": "text",
                 "Length": 7, "Mandatory": "Yes"},
                {"OID": "IT.DM.USUBJID", "Order": 2, "Dataset": "DM",
                 "Variable": "USUBJID", "Label": "Subject ID", "Data Type": "text",
                 "Length": 10, "Mandatory": "Yes"},
            ]
        }
        result = builder.build(raw_data)
        assert len(result["variables"]) == 2
        assert result["variables"][0]["dataset"] == "DM"
        assert result["variables"][1]["dataset"] == "DM"
        assert result["variables"][0]["order"] == 1

    def test_default_values_for_missing_optional_attrs(self):
        builder = _make_builder()
        raw_data = {
            "Study": {"StudyName": "TEST"},
            "Variables": [
                {"OID": "IT.DM.STUDYID", "Dataset": "DM", "Variable": "STUDYID",
                 "Label": "Study ID", "Data Type": "text", "Mandatory": "Yes"}
            ]
        }
        result = builder.build(raw_data)
        var = result["variables"][0]
        assert "length" not in var
        assert "display_format" not in var
        assert "codelist_oid" not in var


class TestBuildWhereClauses:
    def test_grouped_by_oid_multiple_rangechecks(self):
        builder = _make_builder()
        raw_data = {
            "Study": {"StudyName": "TEST"},
            "WhereClauses": [
                {"OID": "WC.1", "Dataset": "VS", "Variable": "VSTESTCD",
                 "Comparator": "EQ", "Value": "SYSBP"},
                {"OID": "WC.1", "Dataset": "VS", "Variable": "VSPOS",
                 "Comparator": "EQ", "Value": "STANDING"},
            ]
        }
        result = builder.build(raw_data)
        assert len(result["where_clauses"]) == 1
        wc = result["where_clauses"][0]
        assert wc["oid"] == "WC.1"
        assert len(wc["range_checks"]) == 2
        assert wc["range_checks"][0]["item_oid"] == "IT.VS.VSTESTCD"
        assert wc["range_checks"][1]["item_oid"] == "IT.VS.VSPOS"


class TestBuildCodelists:
    def test_grouped_by_name_with_decoded_values(self):
        builder = _make_builder()
        raw_data = {
            "Study": {"StudyName": "TEST"},
            "CodeLists": [
                {"OID": "CL.SEX", "Name": "SEX", "Data Type": "text",
                 "Term": "M", "Decoded Value": "Male", "Order": 1,
                 "NCI Codelist Code": "C66731", "NCI Term Code": "C20197"},
                {"OID": "CL.SEX", "Name": "SEX", "Data Type": "text",
                 "Term": "F", "Decoded Value": "Female", "Order": 2,
                 "NCI Term Code": "C16576"},
            ]
        }
        result = builder.build(raw_data)
        assert len(result["codelists"]) == 1
        cl = result["codelists"][0]
        assert cl["name"] == "SEX"
        assert cl["has_decode"] is True
        assert len(cl["terms"]) == 2
        assert cl["nci_codelist_code"] == "C66731"

    def test_enumerated_items_without_decode(self):
        builder = _make_builder()
        raw_data = {
            "Study": {"StudyName": "TEST"},
            "CodeLists": [
                {"OID": "CL.NY", "Name": "NY", "Data Type": "text",
                 "Term": "N", "Decoded Value": None, "Order": 1},
                {"OID": "CL.NY", "Name": "NY", "Data Type": "text",
                 "Term": "Y", "Decoded Value": None, "Order": 2},
            ]
        }
        result = builder.build(raw_data)
        cl = result["codelists"][0]
        assert cl["has_decode"] is False


class TestBuildMethods:
    def test_method_with_formal_expression(self):
        builder = _make_builder()
        raw_data = {
            "Study": {"StudyName": "TEST"},
            "Methods": [
                {"OID": "MT.1", "Name": "Derivation", "Type": "Computation",
                 "Description": "Derived from source",
                 "Expression Context": "Python", "Expression Code": "x + y"}
            ]
        }
        result = builder.build(raw_data)
        m = result["methods"][0]
        assert m["expression_context"] == "Python"
        assert m["expression_code"] == "x + y"


class TestBuildComments:
    def test_comment_with_document_ref(self):
        builder = _make_builder()
        raw_data = {
            "Study": {"StudyName": "TEST"},
            "Comments": [
                {"OID": "COM.1", "Description": "See CRF", "Document": "LF.crf", "Pages": "1-5"}
            ]
        }
        result = builder.build(raw_data)
        c = result["comments"][0]
        assert c["oid"] == "COM.1"
        assert c["document"] == "LF.crf"
        assert c["pages"] == "1-5"


class TestGenerateOidHelper:
    def test_avoids_double_prefix(self):
        assert IntermediateBuilder._generate_oid(["COM", "COM.STUDY.DATA"]) == "COM.STUDY.DATA"
        assert IntermediateBuilder._generate_oid(["MT", "MT.METHOD1"]) == "MT.METHOD1"

    def test_adds_prefix_when_not_present(self):
        assert IntermediateBuilder._generate_oid(["COM", "STUDY.DATA"]) == "COM.STUDY.DATA"
        assert IntermediateBuilder._generate_oid(["MT", "METHOD1"]) == "MT.METHOD1"

    def test_three_descriptors(self):
        assert IntermediateBuilder._generate_oid(["IT", "DM", "STUDYID"]) == "IT.DM.STUDYID"

    def test_uppercase(self):
        assert IntermediateBuilder._generate_oid(["it", "dm", "studyid"]) == "IT.DM.STUDYID"
