"""Tests for intermediate JSON schema validation."""

import json
import os
import sys
import copy

import pytest
import jsonschema

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "mappings", "intermediate_schema.json")


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def _minimal_valid():
    """Return a minimal valid intermediate JSON."""
    return {
        "gendefine_version": "1.0",
        "source_mapping": "test",
        "study": {
            "oid": "ODM.TEST",
            "study_name": "TEST",
            "study_description": "Test study",
            "protocol_name": "TEST",
        },
        "metadata_version": {
            "oid": "MDV.TEST",
            "name": "MDV TEST",
            "description": "Data Definitions for TEST",
            "define_version": "2.1.0",
        },
        "datasets": [],
        "variables": [],
    }


class TestValidIntermediateJSON:
    def test_minimal_valid(self, schema):
        data = _minimal_valid()
        jsonschema.validate(instance=data, schema=schema)

    def test_with_all_optional_sections_empty(self, schema):
        data = _minimal_valid()
        data["standards"] = []
        data["value_levels"] = []
        data["where_clauses"] = []
        data["codelists"] = []
        data["dictionaries"] = []
        data["methods"] = []
        data["comments"] = []
        data["documents"] = []
        jsonschema.validate(instance=data, schema=schema)

    def test_with_dataset_and_variable(self, schema):
        data = _minimal_valid()
        data["datasets"] = [{
            "oid": "IG.DM",
            "name": "DM",
            "description": "Demographics",
            "structure": "One record per subject",
            "purpose": "Tabulation",
            "repeating": "No",
            "is_reference_data": "No",
            "archive_location_id": "LF.DM",
        }]
        data["variables"] = [{
            "oid": "IT.DM.STUDYID",
            "dataset": "DM",
            "name": "STUDYID",
            "label": "Study Identifier",
            "data_type": "text",
            "sas_field_name": "STUDYID",
            "mandatory": "Yes",
        }]
        jsonschema.validate(instance=data, schema=schema)

    def test_variable_with_optional_fields(self, schema):
        data = _minimal_valid()
        data["datasets"] = [{
            "oid": "IG.DM", "name": "DM", "description": "d", "structure": "s",
            "purpose": "Tabulation", "repeating": "No", "is_reference_data": "No",
            "archive_location_id": "LF.DM",
        }]
        data["variables"] = [{
            "oid": "IT.DM.SEX",
            "dataset": "DM",
            "name": "SEX",
            "label": "Sex",
            "data_type": "text",
            "sas_field_name": "SEX",
            "mandatory": "No",
            "length": 1,
            "order": 2,
            "key_sequence": 1,
            "codelist_oid": "CL.SEX",
            "origin_type": "Collected",
            "origin_source": "Subject",
            "pages": "10",
            "method_oid": "MT.1",
            "comment_oid": "COM.1",
        }]
        jsonschema.validate(instance=data, schema=schema)

    def test_length_as_string(self, schema):
        data = _minimal_valid()
        data["variables"] = [{
            "oid": "IT.DM.X", "dataset": "DM", "name": "X", "label": "X",
            "data_type": "text", "sas_field_name": "X", "mandatory": "Yes",
            "length": "200",
        }]
        jsonschema.validate(instance=data, schema=schema)

    def test_full_codelist(self, schema):
        data = _minimal_valid()
        data["codelists"] = [{
            "oid": "CL.SEX",
            "name": "SEX",
            "data_type": "text",
            "has_decode": True,
            "nci_codelist_code": "C66731",
            "terms": [
                {"coded_value": "M", "decoded_value": "Male", "order": 1, "nci_term_code": "C20197"},
                {"coded_value": "F", "decoded_value": "Female", "order": 2},
            ]
        }]
        jsonschema.validate(instance=data, schema=schema)

    def test_where_clause(self, schema):
        data = _minimal_valid()
        data["where_clauses"] = [{
            "oid": "WC.1",
            "range_checks": [{
                "item_oid": "IT.VS.VSTESTCD",
                "comparator": "EQ",
                "check_values": ["SYSBP"],
            }]
        }]
        jsonschema.validate(instance=data, schema=schema)

    def test_method_with_null_pages(self, schema):
        data = _minimal_valid()
        data["methods"] = [{
            "oid": "MT.1",
            "name": "Method1",
            "type": "Computation",
            "description": "desc",
            "pages": None,
        }]
        jsonschema.validate(instance=data, schema=schema)

    def test_comment_with_null_pages(self, schema):
        data = _minimal_valid()
        data["comments"] = [{
            "oid": "COM.1",
            "description": "A comment",
            "pages": None,
        }]
        jsonschema.validate(instance=data, schema=schema)


class TestInvalidIntermediateJSON:
    def test_missing_gendefine_version(self, schema):
        data = _minimal_valid()
        del data["gendefine_version"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=schema)

    def test_wrong_gendefine_version(self, schema):
        data = _minimal_valid()
        data["gendefine_version"] = "2.0"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=schema)

    def test_missing_study(self, schema):
        data = _minimal_valid()
        del data["study"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=schema)

    def test_missing_study_oid(self, schema):
        data = _minimal_valid()
        del data["study"]["oid"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=schema)

    def test_missing_datasets(self, schema):
        data = _minimal_valid()
        del data["datasets"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=schema)

    def test_missing_variables(self, schema):
        data = _minimal_valid()
        del data["variables"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=schema)

    def test_invalid_mandatory_value(self, schema):
        data = _minimal_valid()
        data["variables"] = [{
            "oid": "IT.DM.X", "dataset": "DM", "name": "X", "label": "X",
            "data_type": "text", "sas_field_name": "X", "mandatory": "Maybe",
        }]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=schema)

    def test_invalid_repeating_value(self, schema):
        data = _minimal_valid()
        data["datasets"] = [{
            "oid": "IG.DM", "name": "DM", "description": "d", "structure": "s",
            "purpose": "Tabulation", "repeating": "Sometimes",
            "is_reference_data": "No", "archive_location_id": "LF.DM",
        }]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=schema)

    def test_order_as_string(self, schema):
        data = _minimal_valid()
        data["variables"] = [{
            "oid": "IT.DM.X", "dataset": "DM", "name": "X", "label": "X",
            "data_type": "text", "sas_field_name": "X", "mandatory": "Yes",
            "order": "first",
        }]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=schema)

    def test_where_clause_empty_range_checks(self, schema):
        data = _minimal_valid()
        data["where_clauses"] = [{
            "oid": "WC.1",
            "range_checks": [],
        }]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=schema)

    def test_additional_top_level_property(self, schema):
        data = _minimal_valid()
        data["extra_field"] = "not allowed"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=schema)

    def test_codelist_missing_has_decode(self, schema):
        data = _minimal_valid()
        data["codelists"] = [{
            "oid": "CL.X", "name": "X", "data_type": "text", "terms": [],
        }]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=schema)
