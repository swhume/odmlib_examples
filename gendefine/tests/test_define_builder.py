"""Tests for define_builder.py"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from define_builder import DefineBuilder


def _minimal_intermediate():
    """Return a minimal intermediate JSON structure for testing."""
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
        "datasets": [],
        "variables": [],
        "value_levels": [],
        "where_clauses": [],
        "codelists": [],
        "dictionaries": [],
        "methods": [],
        "comments": [],
        "documents": [],
    }


class TestCreateODM:
    def test_odm_root_attributes(self):
        intermediate = _minimal_intermediate()
        builder = DefineBuilder(intermediate)
        odm = builder.build()
        assert odm.FileOID == "ODM.DEFINE21.TEST.001"
        assert odm.ODMVersion == "1.3.2"
        assert odm.FileType == "Snapshot"
        assert odm.Originator == "Sam Hume"
        assert odm.SourceSystem == "odmlib"


class TestCreateStudy:
    def test_study_with_global_variables(self):
        intermediate = _minimal_intermediate()
        builder = DefineBuilder(intermediate)
        odm = builder.build()
        assert odm.Study.OID == "ODM.TEST"
        assert odm.Study.GlobalVariables.StudyName._content == "TEST"
        assert odm.Study.GlobalVariables.StudyDescription._content == "Test study"
        assert odm.Study.GlobalVariables.ProtocolName._content == "TEST"


class TestCreateItemGroupDef:
    def test_itemgroupdef_with_description_and_itemref(self):
        intermediate = _minimal_intermediate()
        intermediate["datasets"] = [{
            "oid": "IG.DM",
            "name": "DM",
            "description": "Demographics",
            "class_name": "SPECIAL PURPOSE",
            "structure": "One record per subject",
            "purpose": "Tabulation",
            "repeating": "No",
            "is_reference_data": "No",
            "archive_location_id": "LF.DM",
        }]
        intermediate["variables"] = [{
            "oid": "IT.DM.STUDYID",
            "dataset": "DM",
            "name": "STUDYID",
            "label": "Study Identifier",
            "data_type": "text",
            "sas_field_name": "STUDYID",
            "mandatory": "Yes",
            "order": 1,
        }]
        builder = DefineBuilder(intermediate)
        odm = builder.build()
        igds = odm.Study.MetaDataVersion.ItemGroupDef
        assert len(igds) == 1
        assert igds[0].OID == "IG.DM"
        assert igds[0].Name == "DM"
        assert igds[0].Domain == "DM"
        assert igds[0].Description.TranslatedText[0]._content == "Demographics"
        assert igds[0].Class.Name == "SPECIAL PURPOSE"
        # ItemRef added
        assert len(igds[0].ItemRef) == 1
        assert igds[0].ItemRef[0].ItemOID == "IT.DM.STUDYID"


class TestCreateItemDef:
    def test_itemdef_with_origin_and_codelistref(self):
        intermediate = _minimal_intermediate()
        intermediate["datasets"] = [{
            "oid": "IG.DM", "name": "DM", "description": "Demo",
            "structure": "s", "purpose": "Tab", "repeating": "No",
            "is_reference_data": "No", "archive_location_id": "LF.DM",
        }]
        intermediate["variables"] = [{
            "oid": "IT.DM.SEX",
            "dataset": "DM",
            "name": "SEX",
            "label": "Sex",
            "data_type": "text",
            "sas_field_name": "SEX",
            "mandatory": "No",
            "length": 1,
            "codelist_oid": "CL.SEX",
            "origin_type": "Collected",
            "origin_source": "Subject",
            "pages": "10",
        }]
        builder = DefineBuilder(intermediate)
        odm = builder.build()
        items = odm.Study.MetaDataVersion.ItemDef
        assert len(items) == 1
        item = items[0]
        assert item.OID == "IT.DM.SEX"
        assert item.DataType == "text"
        assert item.CodeListRef.CodeListOID == "CL.SEX"
        assert len(item.Origin) == 1
        assert item.Origin[0].Type == "Collected"
        assert item.Origin[0].Source == "Subject"


class TestCreateCodeList:
    def test_codelist_with_codelist_items(self):
        intermediate = _minimal_intermediate()
        intermediate["codelists"] = [{
            "oid": "CL.SEX",
            "name": "SEX",
            "data_type": "text",
            "has_decode": True,
            "nci_codelist_code": "C66731",
            "terms": [
                {"coded_value": "M", "decoded_value": "Male", "order": 1, "nci_term_code": "C20197"},
                {"coded_value": "F", "decoded_value": "Female", "order": 2, "nci_term_code": "C16576"},
            ]
        }]
        builder = DefineBuilder(intermediate)
        odm = builder.build()
        cls = odm.Study.MetaDataVersion.CodeList
        assert len(cls) == 1
        cl = cls[0]
        assert cl.OID == "CL.SEX"
        assert len(cl.CodeListItem) == 2
        assert cl.CodeListItem[0].CodedValue == "M"
        assert cl.CodeListItem[0].Decode.TranslatedText[0]._content == "Male"
        # NCI Codelist Alias at the end
        assert len(cl.Alias) == 1
        assert cl.Alias[0].Name == "C66731"

    def test_codelist_with_enumerated_items(self):
        intermediate = _minimal_intermediate()
        intermediate["codelists"] = [{
            "oid": "CL.NY",
            "name": "NY",
            "data_type": "text",
            "has_decode": False,
            "terms": [
                {"coded_value": "N", "order": 1, "nci_term_code": "C49487"},
                {"coded_value": "Y", "order": 2, "nci_term_code": "C49488"},
            ]
        }]
        builder = DefineBuilder(intermediate)
        odm = builder.build()
        cl = odm.Study.MetaDataVersion.CodeList[0]
        assert len(cl.EnumeratedItem) == 2
        assert cl.EnumeratedItem[0].CodedValue == "N"
        assert cl.EnumeratedItem[0].Alias[0].Name == "C49487"


class TestCreateMethodDef:
    def test_methoddef_with_formal_expression(self):
        intermediate = _minimal_intermediate()
        intermediate["methods"] = [{
            "oid": "MT.1",
            "name": "Derivation",
            "type": "Computation",
            "description": "Derived method",
            "expression_context": "Python",
            "expression_code": "x + y",
        }]
        builder = DefineBuilder(intermediate)
        odm = builder.build()
        methods = odm.Study.MetaDataVersion.MethodDef
        assert len(methods) == 1
        assert methods[0].OID == "MT.1"
        assert methods[0].Description.TranslatedText[0]._content == "Derived method"
        assert methods[0].FormalExpression[0].Context == "Python"


class TestCreateWhereClauseDef:
    def test_whereclausedef_with_rangecheck(self):
        intermediate = _minimal_intermediate()
        intermediate["where_clauses"] = [{
            "oid": "WC.1",
            "range_checks": [{
                "item_oid": "IT.VS.VSTESTCD",
                "comparator": "EQ",
                "check_values": ["SYSBP"],
            }]
        }]
        builder = DefineBuilder(intermediate)
        odm = builder.build()
        wcds = odm.Study.MetaDataVersion.WhereClauseDef
        assert len(wcds) == 1
        assert wcds[0].OID == "WC.1"
        assert len(wcds[0].RangeCheck) == 1
        rc = wcds[0].RangeCheck[0]
        assert rc.ItemOID == "IT.VS.VSTESTCD"
        assert rc.Comparator == "EQ"
        assert rc.CheckValue[0]._content == "SYSBP"
