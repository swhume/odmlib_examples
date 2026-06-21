import json
import os
import tempfile

import pytest
from jsonschema import ValidationError

# Ensure the gendefine package directory is importable
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config_loader import MappingConfig

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
VALID_MAPPING = os.path.join(FIXTURES_DIR, "test-mapping.json")


class TestMappingConfigLoad:
    """Tests for loading and validating mapping files."""

    def test_load_valid_mapping(self):
        config = MappingConfig(VALID_MAPPING)
        assert config.mapping_name == "test-format"

    def test_load_nonexistent_file_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            MappingConfig("/nonexistent/path/mapping.json")

    def test_load_malformed_json_raises_decode_error(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ not valid json !!!")
            f.flush()
            try:
                with pytest.raises(json.JSONDecodeError):
                    MappingConfig(f.name)
            finally:
                os.unlink(f.name)

    def test_missing_required_field_raises_validation_error(self):
        """A mapping file missing the required 'mapping_name' field should fail."""
        incomplete = {
            "mapping_version": "1.0",
            # "mapping_name" is missing
            "description": "test",
            "define_version": "2.1",
            "global_settings": {"language": "en"},
            "worksheets": {
                "Study": {
                    "target": "study_metadata",
                    "format": "attribute_value",
                    "column_map": {"Name": {"maps_to": "StudyName"}}
                }
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(incomplete, f)
            f.flush()
            try:
                with pytest.raises(ValidationError):
                    MappingConfig(f.name)
            finally:
                os.unlink(f.name)

    def test_invalid_worksheet_format_raises_validation_error(self):
        """A worksheet format value not in the enum should fail."""
        bad_format = {
            "mapping_version": "1.0",
            "mapping_name": "test",
            "description": "test",
            "define_version": "2.1",
            "global_settings": {"language": "en"},
            "worksheets": {
                "Study": {
                    "target": "study_metadata",
                    "format": "invalid_format",
                    "column_map": {"Name": {"maps_to": "StudyName"}}
                }
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(bad_format, f)
            f.flush()
            try:
                with pytest.raises(ValidationError):
                    MappingConfig(f.name)
            finally:
                os.unlink(f.name)

    def test_empty_worksheets_raises_validation_error(self):
        """worksheets must have at least one entry."""
        empty_ws = {
            "mapping_version": "1.0",
            "mapping_name": "test",
            "description": "test",
            "define_version": "2.1",
            "global_settings": {"language": "en"},
            "worksheets": {}
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(empty_ws, f)
            f.flush()
            try:
                with pytest.raises(ValidationError):
                    MappingConfig(f.name)
            finally:
                os.unlink(f.name)

    def test_column_map_entry_without_maps_to_or_ignore_raises_error(self):
        """A column_map entry with neither maps_to nor ignore_for_define should fail."""
        bad_column = {
            "mapping_version": "1.0",
            "mapping_name": "test",
            "description": "test",
            "define_version": "2.1",
            "global_settings": {"language": "en"},
            "worksheets": {
                "Study": {
                    "target": "study_metadata",
                    "format": "attribute_value",
                    "column_map": {
                        "Name": {"optional": True}
                    }
                }
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(bad_column, f)
            f.flush()
            try:
                with pytest.raises(ValidationError):
                    MappingConfig(f.name)
            finally:
                os.unlink(f.name)

    def test_column_map_ignore_for_define_without_maps_to_is_valid(self):
        """A column_map entry with ignore_for_define: true and no maps_to should be valid."""
        ignore_col = {
            "mapping_version": "1.0",
            "mapping_name": "test",
            "description": "test",
            "define_version": "2.1",
            "global_settings": {"language": "en"},
            "worksheets": {
                "Study": {
                    "target": "study_metadata",
                    "format": "attribute_value",
                    "column_map": {
                        "Notes": {"ignore_for_define": True}
                    }
                }
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(ignore_col, f)
            f.flush()
            try:
                config = MappingConfig(f.name)
                assert config.mapping_name == "test"
            finally:
                os.unlink(f.name)


class TestMappingConfigAccessors:
    """Tests for accessor methods on a loaded mapping."""

    @pytest.fixture
    def config(self):
        return MappingConfig(VALID_MAPPING)

    def test_mapping_name(self, config):
        assert config.mapping_name == "test-format"

    def test_mapping_version(self, config):
        assert config.mapping_version == "1.0"

    def test_description(self, config):
        assert config.description == "Minimal test mapping for unit tests"

    def test_define_version(self, config):
        assert config.define_version == "2.1"

    def test_global_settings(self, config):
        gs = config.global_settings
        assert gs["language"] == "en"
        assert gs["default_purpose"] == "Tabulation"
        assert gs["annotated_crf_leaf_id"] == "LF.acrf"
        assert gs["oid_generation_strategy"] == "pattern"

    def test_worksheet_names(self, config):
        names = config.worksheet_names
        assert "Study" in names
        assert "Datasets" in names
        assert "Variables" in names

    def test_get_worksheet_config_known(self, config):
        ws = config.get_worksheet_config("Study")
        assert ws is not None
        assert ws["format"] == "attribute_value"
        assert ws["target"] == "study_metadata"

    def test_get_worksheet_config_unknown(self, config):
        assert config.get_worksheet_config("NonExistent") is None

    def test_get_worksheet_config_tabular(self, config):
        ws = config.get_worksheet_config("Variables")
        assert ws["format"] == "tabular"
        assert ws["target"] == ["ItemDef", "ItemRef"]

    def test_get_oid_pattern_known(self, config):
        assert config.get_oid_pattern("ItemGroupDef") == "IG.{Dataset}"
        assert config.get_oid_pattern("ItemDef") == "IT.{Dataset}.{Variable}"

    def test_get_oid_pattern_unknown(self, config):
        assert config.get_oid_pattern("UnknownType") is None

    def test_get_value_transform_known(self, config):
        vt = config.get_value_transform("core_to_mandatory")
        assert vt is not None
        assert vt["type"] == "lookup"
        assert vt["map"]["Req"] == "Yes"

    def test_get_value_transform_unknown(self, config):
        assert config.get_value_transform("nonexistent") is None

    def test_get_default_known(self, config):
        assert config.get_default("Purpose") == "Tabulation"
        assert config.get_default("Mandatory") == "No"

    def test_get_default_unknown(self, config):
        assert config.get_default("UnknownAttr") is None

    def test_oid_patterns_property(self, config):
        patterns = config.oid_patterns
        assert "ItemGroupDef" in patterns
        assert "leaf" in patterns

    def test_value_transforms_property(self, config):
        transforms = config.value_transforms
        assert "core_to_mandatory" in transforms
        assert "where_clause_parse" in transforms

    def test_defaults_property(self, config):
        defaults = config.defaults
        assert defaults["Purpose"] == "Tabulation"
        assert defaults["DefineVersion"] == "2.1.0"
