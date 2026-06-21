import re


class OIDGenerator:
    """Generates and tracks OIDs from pattern templates.

    Supports two modes:
    - Pattern-based generation: substitute placeholders in a pattern string
      (e.g., "IT.{Dataset}.{Variable}" with {"Dataset": "DM", "Variable": "STUDYID"})
    - Column-sourced passthrough: register OIDs read directly from a spreadsheet column

    All OIDs are uppercased per CDISC convention. Uniqueness is enforced across
    both generated and registered OIDs.
    """

    # Match {placeholder} tokens in OID patterns
    _PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")

    def __init__(self):
        """Initialize with empty OID registry."""
        self._oids: set[str] = set()

    def generate(self, pattern: str, values: dict) -> str:
        """Generate an OID by substituting placeholders in the pattern.

        Placeholders use {FieldName} syntax. All values are converted to strings
        before substitution. The resulting OID is uppercased.

        :param pattern: OID pattern with {placeholder} tokens
        :param values: dict mapping placeholder names to substitution values
        :returns: the generated OID string
        :raises KeyError: if a placeholder in the pattern has no matching key in values
        :raises ValueError: if the generated OID already exists in the registry
        """
        # Verify all placeholders have corresponding values before substituting
        placeholders = self._PLACEHOLDER_RE.findall(pattern)
        for ph in placeholders:
            if ph not in values:
                raise KeyError(
                    f"OID pattern '{pattern}' requires placeholder '{{{ph}}}' "
                    f"but it was not found in values: {list(values.keys())}"
                )
        oid = self._PLACEHOLDER_RE.sub(
            lambda m: str(values[m.group(1)]), pattern
        ).upper()
        self._register_with_context(oid, pattern, values)
        return oid

    def register(self, oid: str) -> None:
        """Register an externally-provided OID (from a spreadsheet column).

        The OID is uppercased before registration.

        :param oid: OID string to register
        :raises ValueError: if the OID already exists in the registry
        """
        oid_upper = oid.upper()
        if oid_upper in self._oids:
            raise ValueError(f"Duplicate OID: '{oid_upper}' is already registered")
        self._oids.add(oid_upper)

    def exists(self, oid: str) -> bool:
        """Check if an OID has been generated or registered.

        :param oid: OID string to check (case-insensitive)
        """
        return oid.upper() in self._oids

    def reset(self) -> None:
        """Clear all tracked OIDs."""
        self._oids.clear()

    def _register_with_context(self, oid: str, pattern: str, values: dict):
        """Register a generated OID, providing context in error messages."""
        if oid in self._oids:
            raise ValueError(
                f"Duplicate OID: '{oid}' generated from pattern '{pattern}' "
                f"with values {values} — this OID is already registered"
            )
        self._oids.add(oid)
