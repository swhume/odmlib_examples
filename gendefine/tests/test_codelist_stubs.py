"""Tests for codelist stub generation in intermediate_builder.py"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from intermediate_builder import IntermediateBuilder
from config_loader import MappingConfig
from oid_generator import OIDGenerator
from value_transformer import ValueTransformer


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
MAPPINGS_DIR = os.path.join(os.path.dirname(__file__), "..", "mappings")


def _make_builder(mapping_file=None):
    if mapping_file is None:
        mapping_file = os.path.join(MAPPINGS_DIR, "standard-spec.json")
    config = MappingConfig(mapping_file)
    oid_gen = OIDGenerator()
    transformer = ValueTransformer(config.value_transforms, config.defaults)
    return IntermediateBuilder(config, oid_gen, transformer)


class TestCodelistReferencesCollected:
    def test_collects_from_variables(self):
        builder = _make_builder()
        variables = [
            {"codelist_oid": "CL.SEX"},
            {"codelist_oid": "CL.AESEV"},
            {"name": "AGE"},  # no codelist
        ]
        stubs = builder._build_codelist_stubs(variables, [])
        names = [s["name"] for s in stubs]
        assert "AESEV" in names
        assert "SEX" in names

    def test_collects_from_value_levels(self):
        builder = _make_builder()
        value_levels = [
            {"codelist_oid": "CL.VSTESTCD"},
        ]
        stubs = builder._build_codelist_stubs([], value_levels)
        assert len(stubs) == 1
        assert stubs[0]["name"] == "VSTESTCD"


class TestUniqueCodelistNames:
    def test_duplicate_names_produce_single_stub(self):
        builder = _make_builder()
        variables = [
            {"codelist_oid": "CL.SEX"},
            {"codelist_oid": "CL.SEX"},
            {"codelist_oid": "CL.SEX"},
        ]
        stubs = builder._build_codelist_stubs(variables, [])
        assert len(stubs) == 1

    def test_combined_sources_deduplicated(self):
        builder = _make_builder()
        variables = [{"codelist_oid": "CL.SEX"}]
        value_levels = [{"codelist_oid": "CL.SEX"}]
        stubs = builder._build_codelist_stubs(variables, value_levels)
        assert len(stubs) == 1


class TestStubStructure:
    def test_stub_has_oid_name_datatype_no_terms(self):
        builder = _make_builder()
        variables = [{"codelist_oid": "CL.SEX"}]
        stubs = builder._build_codelist_stubs(variables, [])
        stub = stubs[0]
        assert stub["oid"] == "CL.SEX"
        assert stub["name"] == "SEX"
        assert stub["data_type"] == "text"
        assert stub["terms"] == []
        assert stub["has_decode"] is False

    def test_empty_references_produce_no_stubs(self):
        builder = _make_builder()
        stubs = builder._build_codelist_stubs([], [])
        assert stubs == []

    def test_variables_without_codelist_ignored(self):
        builder = _make_builder()
        variables = [{"name": "AGE"}, {"name": "SEX"}]
        stubs = builder._build_codelist_stubs(variables, [])
        assert stubs == []
