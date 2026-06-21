import json
import os

import jsonschema


class MappingConfig:
    """Loads and provides access to a JSON mapping configuration."""

    # mapping_schema.json lives in the mappings/ directory alongside mapping files
    _SCHEMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mappings")
    _SCHEMA_FILE = os.path.join(_SCHEMA_DIR, "mapping_schema.json")

    def __init__(self, mapping_file: str):
        """Load and validate the mapping file against the mapping schema.

        :param mapping_file: path to the JSON mapping configuration file
        :raises FileNotFoundError: if the mapping file does not exist
        :raises json.JSONDecodeError: if the file is not valid JSON
        :raises jsonschema.ValidationError: if the mapping fails schema validation
        """
        with open(mapping_file) as f:
            self._data = json.load(f)
        self._validate()

    def _validate(self):
        """Validate the loaded mapping data against the mapping schema."""
        with open(self._SCHEMA_FILE) as f:
            schema = json.load(f)
        jsonschema.validate(instance=self._data, schema=schema)

    @property
    def mapping_name(self) -> str:
        return self._data["mapping_name"]

    @property
    def mapping_version(self) -> str:
        return self._data["mapping_version"]

    @property
    def description(self) -> str:
        return self._data["description"]

    @property
    def define_version(self) -> str:
        return self._data["define_version"]

    @property
    def global_settings(self) -> dict:
        return self._data["global_settings"]

    @property
    def worksheets(self) -> dict:
        """Return the full worksheets mapping dictionary."""
        return self._data["worksheets"]

    @property
    def worksheet_names(self) -> list[str]:
        """Return list of configured worksheet names."""
        return list(self._data["worksheets"].keys())

    @property
    def oid_patterns(self) -> dict:
        """Return the oid_patterns dictionary, or empty dict if not present."""
        return self._data.get("oid_patterns", {})

    @property
    def value_transforms(self) -> dict:
        """Return the value_transforms dictionary, or empty dict if not present."""
        return self._data.get("value_transforms", {})

    @property
    def defaults(self) -> dict:
        """Return the defaults dictionary, or empty dict if not present."""
        return self._data.get("defaults", {})

    def get_worksheet_config(self, sheet_name: str) -> dict | None:
        """Return the worksheet mapping for a given sheet name, or None."""
        return self._data["worksheets"].get(sheet_name)

    def get_oid_pattern(self, element_type: str) -> str | None:
        """Return the OID pattern for an element type, or None."""
        return self._data.get("oid_patterns", {}).get(element_type)

    def get_value_transform(self, transform_name: str) -> dict | None:
        """Return a value transform definition by name."""
        return self._data.get("value_transforms", {}).get(transform_name)

    def get_default(self, attribute_name: str) -> str | None:
        """Return the default value for an attribute, or None."""
        return self._data.get("defaults", {}).get(attribute_name)
