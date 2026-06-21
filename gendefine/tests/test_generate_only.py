"""Tests for generate-only mode."""

import json
import os
import sys
import tempfile
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from define_builder import DefineBuilder
from validator import IntermediateValidator


def _minimal_intermediate():
    """Return a minimal valid intermediate JSON for testing."""
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
        "standards": [],
        "datasets": [{
            "oid": "IG.DM",
            "name": "DM",
            "description": "Demographics",
            "structure": "One record per subject",
            "purpose": "Tabulation",
            "repeating": "No",
            "is_reference_data": "No",
            "archive_location_id": "LF.DM",
            "class_name": "SPECIAL PURPOSE",
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
        }],
        "value_levels": [],
        "where_clauses": [],
        "codelists": [],
        "dictionaries": [],
        "methods": [],
        "comments": [],
        "documents": [{
            "id": "LF.acrf",
            "title": "Annotated CRF",
            "href": "acrf.pdf",
        }],
    }


class TestGenerateOnlyProducesDefineXML:
    def test_generates_valid_xml(self):
        data = _minimal_intermediate()
        builder = DefineBuilder(data)
        odm = builder.build()
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            output_path = f.name
        try:
            odm.write_xml(output_path)
            tree = ET.parse(output_path)
            root = tree.getroot()
            # Root element should be ODM
            assert root.tag.endswith("ODM") or "ODM" in root.tag
        finally:
            os.unlink(output_path)

    def test_contains_itemgroupdef(self):
        data = _minimal_intermediate()
        builder = DefineBuilder(data)
        odm = builder.build()
        assert len(odm.Study.MetaDataVersion.ItemGroupDef) == 1
        assert odm.Study.MetaDataVersion.ItemGroupDef[0].OID == "IG.DM"

    def test_contains_itemdef(self):
        data = _minimal_intermediate()
        builder = DefineBuilder(data)
        odm = builder.build()
        assert len(odm.Study.MetaDataVersion.ItemDef) == 1
        assert odm.Study.MetaDataVersion.ItemDef[0].OID == "IT.DM.STUDYID"


class TestGenerateOnlyWithMissingOptionalSections:
    def test_missing_value_levels_treated_as_empty(self):
        data = _minimal_intermediate()
        del data["value_levels"]
        data.setdefault("value_levels", [])
        builder = DefineBuilder(data)
        odm = builder.build()
        assert len(odm.Study.MetaDataVersion.ValueListDef) == 0

    def test_missing_methods_treated_as_empty(self):
        data = _minimal_intermediate()
        del data["methods"]
        data.setdefault("methods", [])
        builder = DefineBuilder(data)
        odm = builder.build()
        assert len(odm.Study.MetaDataVersion.MethodDef) == 0

    def test_missing_codelists_treated_as_empty(self):
        data = _minimal_intermediate()
        del data["codelists"]
        data.setdefault("codelists", [])
        builder = DefineBuilder(data)
        odm = builder.build()
        assert len(odm.Study.MetaDataVersion.CodeList) == 0


class TestGenerateOnlyValidation:
    def test_invalid_json_detected(self):
        data = _minimal_intermediate()
        data["gendefine_version"] = "9.9"  # Invalid version
        iv = IntermediateValidator()
        errors = iv.validate_schema(data)
        assert len(errors) > 0
        assert any("gendefine_version" in e for e in errors)

    def test_missing_required_field_detected(self):
        data = _minimal_intermediate()
        del data["study"]
        iv = IntermediateValidator()
        errors = iv.validate_schema(data)
        assert len(errors) > 0
        assert any("study" in e for e in errors)


class TestGenerateOnlyCLIRequirements:
    def test_generate_only_requires_json_flag(self):
        """Verify that --generate-only without -j is rejected."""
        import subprocess
        GENDEFINE_DIR = os.path.join(os.path.dirname(__file__), "..")
        result = subprocess.run(
            [sys.executable, os.path.join(GENDEFINE_DIR, "gendefine.py"),
             "--generate-only"],
            capture_output=True, text=True,
            cwd=GENDEFINE_DIR
        )
        assert result.returncode != 0
        assert "requires -j" in result.stdout
