import re


class ValueTransformer:
    """Applies value transforms defined in the mapping configuration.

    Supports three transform types:
    - lookup: map a value through a lookup table with an optional default
    - type_coercion: convert a value to integer, float, or string
    - regex_parse: parse a value with a regex pattern, returning a dict of captured fields

    Also provides default-value substitution for required attributes.
    """

    def __init__(self, transforms: dict, defaults: dict):
        """Initialize with transform definitions and defaults from the mapping config.

        :param transforms: the "value_transforms" section of the mapping (may be empty)
        :param defaults: the "defaults" section of the mapping (may be empty)
        """
        self._transforms = transforms
        self._defaults = defaults

    def transform(self, value, transform_name: str):
        """Apply a named transform to a value.

        :param value: the raw cell value to transform
        :param transform_name: name of a transform defined in the mapping configuration
        :returns: the transformed value
        :raises KeyError: if transform_name is not found in the configured transforms
        :raises ValueError: if the transform type is not recognized
        """
        if transform_name not in self._transforms:
            raise KeyError(f"Unknown transform: '{transform_name}'")
        transform_def = self._transforms[transform_name]
        transform_type = transform_def["type"]

        if transform_type == "lookup":
            return self._apply_lookup(value, transform_def)
        elif transform_type == "type_coercion":
            return self.coerce_type(value, transform_def["target"])
        elif transform_type == "regex_parse":
            return self._apply_regex_parse(value, transform_def)
        else:
            raise ValueError(f"Unsupported transform type: '{transform_type}'")

    def apply_default(self, value, attribute_name: str):
        """Return value if truthy, otherwise return the configured default.

        :param value: the value to check
        :param attribute_name: the attribute name to look up in defaults
        :returns: value if truthy, else the configured default, else None
        """
        if value:
            return value
        return self._defaults.get(attribute_name)

    def coerce_type(self, value, target_type: str):
        """Convert value to the target type.

        :param value: the value to convert
        :param target_type: one of "integer", "float", "string"
        :returns: the converted value, or None if value is None
        :raises ValueError: if target_type is not recognized
        """
        if value is None:
            return None
        if target_type == "integer":
            return int(value)
        elif target_type == "float":
            return float(value)
        elif target_type == "string":
            return str(value)
        else:
            raise ValueError(f"Unsupported coercion target type: '{target_type}'")

    def _apply_lookup(self, value, transform_def: dict):
        """Apply a lookup transform: map value through the lookup table.

        :param value: the raw value to look up
        :param transform_def: the transform definition containing 'map' and optional 'default'
        :returns: the mapped value, the default, or None
        """
        lookup_map = transform_def.get("map", {})
        default = transform_def.get("default")
        if value is None:
            return default
        str_value = str(value)
        if str_value in lookup_map:
            return lookup_map[str_value]
        return default

    def _apply_regex_parse(self, value, transform_def: dict):
        """Apply a regex parse transform: match pattern and return captured groups.

        :param value: the string value to parse
        :param transform_def: the transform definition containing 'pattern' and 'output_fields'
        :returns: dict mapping output_fields to captured groups, or None if no match
        """
        if value is None:
            return None
        pattern = transform_def["pattern"]
        output_fields = transform_def["output_fields"]
        match = re.match(pattern, str(value))
        if match is None:
            return None
        groups = match.groups()
        result = {}
        for i, field_name in enumerate(output_fields):
            if i < len(groups):
                result[field_name] = groups[i]
        return result
