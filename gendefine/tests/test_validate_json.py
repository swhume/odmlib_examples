"""Tests for intermediate JSON validation (OID uniqueness and cross-references)."""

import os
import sys
import copy

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from validator import IntermediateValidator


def _valid_intermediate():
    """Return a valid intermediate JSON with cross-references."""
    return {
        "gendefine_version": "1.0",
        "source_mapping": "test",
        "study": {
            "oid": "ODM.TEST",
            "study_name": "TEST",
            "study_description": "Test study",
            "protocol_name": "TEST",
            "language": "en",
            "annotated_crf": "LF.acrf",
        },
        "metadata_version": {
            "oid": "MDV.TEST",
            "name": "MDV TEST",
            "description": "Data Definitions for TEST",
            "define_version": "2.1.0",
        },
        "standards": [
            {"oid": "STD.1", "name": "SDTMIG", "type": "IG", "version": "3.4", "status": "Final"},
        ],
        "datasets": [{
            "oid": "IG.DM",
            "name": "DM",
            "description": "Demographics",
            "structure": "One record per subject",
            "purpose": "Tabulation",
            "repeating": "No",
            "is_reference_data": "No",
            "archive_location_id": "LF.DM",
            "standard_oid": "STD.1",
            "comment_oid": "COM.DS1",
        }],
        "variables": [{
            "oid": "IT.DM.STUDYID",
            "dataset": "DM",
            "name": "STUDYID",
            "label": "Study Identifier",
            "data_type": "text",
            "sas_field_name": "STUDYID",
            "mandatory": "Yes",
            "order": 1,
            "codelist_oid": "CL.NY",
            "method_oid": "MT.1",
            "comment_oid": "COM.1",
        }],
        "value_levels": [{
            "vl_oid": "VL.VS.VSSTRESN",
            "item_oid": "IT.VS.VSSTRESN.SYSBP",
            "dataset": "VS",
            "name": "VSSTRESN",
            "data_type": "float",
            "mandatory": "No",
            "order": 1,
            "where_clause_oid": "WC.1",
            "codelist_oid": "CL.NY",
            "method_oid": "MT.1",
            "comment_oid": "COM.1",
        }],
        "where_clauses": [{
            "oid": "WC.1",
            "range_checks": [{
                "item_oid": "IT.VS.VSTESTCD",
                "comparator": "EQ",
                "check_values": ["SYSBP"],
            }]
        }],
        "codelists": [{
            "oid": "CL.NY",
            "name": "NY",
            "data_type": "text",
            "has_decode": False,
            "terms": [{"coded_value": "N"}, {"coded_value": "Y"}],
        }],
        "dictionaries": [],
        "methods": [{
            "oid": "MT.1",
            "name": "Method1",
            "type": "Computation",
            "description": "Derived",
        }],
        "comments": [
            {"oid": "COM.1", "description": "A comment"},
            {"oid": "COM.DS1", "description": "Dataset comment"},
        ],
        "documents": [
            {"id": "LF.acrf", "title": "aCRF", "href": "acrf.pdf"},
        ],
    }


class TestValidIntermediatePassesAll:
    def test_no_errors_or_warnings(self):
        data = _valid_intermediate()
        iv = IntermediateValidator()
        errors, warnings = iv.validate_all(data)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_warnings_for_unknown_range_check_item(self):
        """range_check item_oid referencing unknown variable is a warning, not error."""
        data = _valid_intermediate()
        iv = IntermediateValidator()
        _, warnings = iv.validate_all(data)
        # IT.VS.VSTESTCD is not in our variables list -> warning
        assert any("IT.VS.VSTESTCD" in w for w in warnings)


class TestOIDUniqueness:
    def test_duplicate_dataset_variable_oid(self):
        data = _valid_intermediate()
        # Add a variable with same OID as the dataset
        data["variables"].append({
            "oid": "IG.DM",  # Duplicate of dataset OID
            "dataset": "DM",
            "name": "DUP",
            "label": "Dup",
            "data_type": "text",
            "sas_field_name": "DUP",
            "mandatory": "No",
        })
        iv = IntermediateValidator()
        errors = iv.check_oid_uniqueness(data)
        assert len(errors) == 1
        assert "IG.DM" in errors[0]

    def test_duplicate_variable_oids(self):
        data = _valid_intermediate()
        data["variables"].append({
            "oid": "IT.DM.STUDYID",  # Duplicate
            "dataset": "DM",
            "name": "STUDYID2",
            "label": "Dup",
            "data_type": "text",
            "sas_field_name": "STUDYID2",
            "mandatory": "No",
        })
        iv = IntermediateValidator()
        errors = iv.check_oid_uniqueness(data)
        assert len(errors) == 1
        assert "IT.DM.STUDYID" in errors[0]

    def test_duplicate_codelist_oids(self):
        data = _valid_intermediate()
        data["codelists"].append({
            "oid": "CL.NY",  # Duplicate
            "name": "NY2",
            "data_type": "text",
            "has_decode": False,
            "terms": [],
        })
        iv = IntermediateValidator()
        errors = iv.check_oid_uniqueness(data)
        assert len(errors) == 1
        assert "CL.NY" in errors[0]

    def test_no_duplicates_in_valid_data(self):
        data = _valid_intermediate()
        iv = IntermediateValidator()
        errors = iv.check_oid_uniqueness(data)
        assert errors == []


class TestCrossReferences:
    def test_invalid_codelist_oid_in_variable(self):
        data = _valid_intermediate()
        data["variables"][0]["codelist_oid"] = "CL.NONEXISTENT"
        iv = IntermediateValidator()
        errors, _ = iv.check_cross_references(data)
        assert any("CL.NONEXISTENT" in e for e in errors)

    def test_invalid_method_oid_in_variable(self):
        data = _valid_intermediate()
        data["variables"][0]["method_oid"] = "MT.NONEXISTENT"
        iv = IntermediateValidator()
        errors, _ = iv.check_cross_references(data)
        assert any("MT.NONEXISTENT" in e for e in errors)

    def test_invalid_comment_oid_in_variable(self):
        data = _valid_intermediate()
        data["variables"][0]["comment_oid"] = "COM.NONEXISTENT"
        iv = IntermediateValidator()
        errors, _ = iv.check_cross_references(data)
        assert any("COM.NONEXISTENT" in e for e in errors)

    def test_invalid_where_clause_oid_in_value_level(self):
        data = _valid_intermediate()
        data["value_levels"][0]["where_clause_oid"] = "WC.NONEXISTENT"
        iv = IntermediateValidator()
        errors, _ = iv.check_cross_references(data)
        assert any("WC.NONEXISTENT" in e for e in errors)

    def test_invalid_standard_oid_in_dataset(self):
        data = _valid_intermediate()
        data["datasets"][0]["standard_oid"] = "STD.NONEXISTENT"
        iv = IntermediateValidator()
        errors, _ = iv.check_cross_references(data)
        assert any("STD.NONEXISTENT" in e for e in errors)

    def test_invalid_comment_oid_in_dataset(self):
        data = _valid_intermediate()
        data["datasets"][0]["comment_oid"] = "COM.NONEXISTENT"
        iv = IntermediateValidator()
        errors, _ = iv.check_cross_references(data)
        assert any("COM.NONEXISTENT" in e for e in errors)

    def test_invalid_codelist_oid_in_value_level(self):
        data = _valid_intermediate()
        data["value_levels"][0]["codelist_oid"] = "CL.NONEXISTENT"
        iv = IntermediateValidator()
        errors, _ = iv.check_cross_references(data)
        assert any("CL.NONEXISTENT" in e for e in errors)

    def test_invalid_valuelist_oid_in_variable(self):
        data = _valid_intermediate()
        data["variables"][0]["valuelist_oid"] = "VL.NONEXISTENT"
        iv = IntermediateValidator()
        errors, _ = iv.check_cross_references(data)
        assert any("VL.NONEXISTENT" in e for e in errors)

    def test_valid_valuelist_oid_reference(self):
        data = _valid_intermediate()
        data["variables"][0]["valuelist_oid"] = "VL.VS.VSSTRESN"
        iv = IntermediateValidator()
        errors, _ = iv.check_cross_references(data)
        # Should not have errors for VL.VS.VSSTRESN since it exists
        assert not any("VL.VS.VSSTRESN" in e for e in errors)

    def test_valid_cross_references(self):
        data = _valid_intermediate()
        iv = IntermediateValidator()
        errors, _ = iv.check_cross_references(data)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_dictionary_oid_counts_as_codelist(self):
        """Dictionary OIDs should satisfy codelist_oid references."""
        data = _valid_intermediate()
        data["dictionaries"] = [{
            "oid": "CL.MEDDRA",
            "name": "MedDRA",
            "data_type": "text",
            "dictionary": "MedDRA",
            "version": "23.0",
        }]
        data["variables"][0]["codelist_oid"] = "CL.MEDDRA"
        iv = IntermediateValidator()
        errors, _ = iv.check_cross_references(data)
        assert not any("CL.MEDDRA" in e for e in errors)


class TestValidateAll:
    def test_schema_errors_prevent_cross_ref_check(self):
        """If schema validation fails, cross-ref check is skipped."""
        data = {"gendefine_version": "9.9"}  # Invalid
        iv = IntermediateValidator()
        errors, warnings = iv.validate_all(data)
        assert len(errors) > 0
        assert warnings == []

    def test_valid_data_runs_all_checks(self):
        data = _valid_intermediate()
        iv = IntermediateValidator()
        errors, warnings = iv.validate_all(data)
        assert errors == []
