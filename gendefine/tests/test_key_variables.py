"""Tests for key variables processing in intermediate_builder.py"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from intermediate_builder import IntermediateBuilder
from config_loader import MappingConfig
from oid_generator import OIDGenerator
from value_transformer import ValueTransformer


MAPPINGS_DIR = os.path.join(os.path.dirname(__file__), "..", "mappings")


def _make_builder():
    config = MappingConfig(os.path.join(MAPPINGS_DIR, "standard-spec.json"))
    oid_gen = OIDGenerator()
    transformer = ValueTransformer(config.value_transforms, config.defaults)
    return IntermediateBuilder(config, oid_gen, transformer)


class TestKeyVariablesParsing:
    def test_key_variables_parsed_to_ordered_list(self):
        builder = _make_builder()
        raw_data = {
            "Standard": {"StudyName": "TEST"},
            "Datasets": [
                {"Dataset": "DM", "Description": "Demo", "Class": "SPECIAL PURPOSE",
                 "Structure": "s", "Repeating": "No", "Reference Data": "No",
                 "Key Variables": "STUDYID, USUBJID"},
            ],
            "Variables": [
                {"Order": 1, "Dataset": "DM", "Variable": "STUDYID",
                 "Label": "Study ID", "Data Type": "text", "Core": "Req"},
                {"Order": 2, "Dataset": "DM", "Variable": "USUBJID",
                 "Label": "Subject ID", "Data Type": "text", "Core": "Req"},
                {"Order": 3, "Dataset": "DM", "Variable": "SEX",
                 "Label": "Sex", "Data Type": "text", "Core": "Req"},
            ],
        }
        result = builder.build(raw_data)
        vars_by_name = {v["name"]: v for v in result["variables"]}
        assert vars_by_name["STUDYID"]["key_sequence"] == 1
        assert vars_by_name["USUBJID"]["key_sequence"] == 2

    def test_key_sequence_assigned_correctly_1_indexed(self):
        builder = _make_builder()
        raw_data = {
            "Standard": {"StudyName": "TEST"},
            "Datasets": [
                {"Dataset": "VS", "Description": "Vital Signs", "Class": "FINDINGS",
                 "Structure": "s", "Repeating": "Yes", "Reference Data": "No",
                 "Key Variables": "STUDYID, USUBJID, VSTESTCD, VISITNUM"},
            ],
            "Variables": [
                {"Order": 1, "Dataset": "VS", "Variable": "VSTESTCD",
                 "Label": "Test Code", "Data Type": "text", "Core": "Req"},
                {"Order": 2, "Dataset": "VS", "Variable": "VISITNUM",
                 "Label": "Visit Number", "Data Type": "float", "Core": "Exp"},
                {"Order": 3, "Dataset": "VS", "Variable": "STUDYID",
                 "Label": "Study ID", "Data Type": "text", "Core": "Req"},
                {"Order": 4, "Dataset": "VS", "Variable": "USUBJID",
                 "Label": "Subject ID", "Data Type": "text", "Core": "Req"},
            ],
        }
        result = builder.build(raw_data)
        vars_by_name = {v["name"]: v for v in result["variables"]}
        assert vars_by_name["STUDYID"]["key_sequence"] == 1
        assert vars_by_name["USUBJID"]["key_sequence"] == 2
        assert vars_by_name["VSTESTCD"]["key_sequence"] == 3
        assert vars_by_name["VISITNUM"]["key_sequence"] == 4

    def test_variable_not_in_key_list_has_no_key_sequence(self):
        builder = _make_builder()
        raw_data = {
            "Standard": {"StudyName": "TEST"},
            "Datasets": [
                {"Dataset": "DM", "Description": "Demo", "Class": "SPECIAL PURPOSE",
                 "Structure": "s", "Repeating": "No", "Reference Data": "No",
                 "Key Variables": "STUDYID, USUBJID"},
            ],
            "Variables": [
                {"Order": 1, "Dataset": "DM", "Variable": "SEX",
                 "Label": "Sex", "Data Type": "text", "Core": "Req"},
            ],
        }
        result = builder.build(raw_data)
        assert "key_sequence" not in result["variables"][0]

    def test_empty_key_variables_no_key_sequence(self):
        builder = _make_builder()
        raw_data = {
            "Standard": {"StudyName": "TEST"},
            "Datasets": [
                {"Dataset": "DM", "Description": "Demo", "Class": "SPECIAL PURPOSE",
                 "Structure": "s", "Repeating": "No", "Reference Data": "No"},
            ],
            "Variables": [
                {"Order": 1, "Dataset": "DM", "Variable": "STUDYID",
                 "Label": "Study ID", "Data Type": "text", "Core": "Req"},
            ],
        }
        result = builder.build(raw_data)
        assert "key_sequence" not in result["variables"][0]
