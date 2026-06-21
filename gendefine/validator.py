"""Validates Define-XML output and intermediate JSON using odmlib's validation framework."""

import json
import os

import jsonschema

from odmlib import odm_parser as P, create_oid_checker
from odmlib.define_2_1.rules.metadata_schema import MetadataSchema

# intermediate_schema.json lives in the mappings/ directory
_SCHEMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mappings")
_INTERMEDIATE_SCHEMA_FILE = os.path.join(_SCHEMA_DIR, "intermediate_schema.json")


class DefineValidator:
    """Validates Define-XML output using odmlib's validation framework."""

    def validate_schema(self, define_file: str, schema_path: str) -> list[str]:
        """Validate a Define-XML file against the XSD schema.

        :param define_file: path to the Define-XML file
        :param schema_path: path to the Define-XML v2.1 XSD schema
        :returns: list of error messages (empty if valid)
        """
        errors = []
        validator = P.ODMSchemaValidator(schema_path)
        try:
            validator.validate_file(define_file)
        except Exception as e:
            errors.append(str(e))
        return errors

    def check_conformance(self, odm) -> list[str]:
        """Run OID reference checks and metadata conformance checks.

        :param odm: odmlib ODM object
        :returns: list of error messages (empty if valid)
        """
        oid_checker = create_oid_checker("define_2_1")
        conformance_checker = MetadataSchema()
        errors = odm.Study.validate(
            collect_errors=True,
            oid_checker=oid_checker,
            conformance_checker=conformance_checker,
        )
        orphans = oid_checker.check_unreferenced_oids()
        if orphans:
            errors.append(f"Unreferenced OID Defs: {orphans}")
        return errors if errors else []


class IntermediateValidator:
    """Validates intermediate JSON structure and cross-references."""

    def __init__(self):
        with open(_INTERMEDIATE_SCHEMA_FILE) as f:
            self._schema = json.load(f)

    def validate_schema(self, data: dict) -> list[str]:
        """Validate intermediate JSON against the intermediate schema.

        :param data: the intermediate JSON dict
        :returns: list of error messages (empty if valid)
        """
        errors = []
        v = jsonschema.Draft202012Validator(self._schema)
        for error in sorted(v.iter_errors(data), key=lambda e: list(e.path)):
            path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "(root)"
            errors.append(f"{path}: {error.message}")
        return errors

    def check_oid_uniqueness(self, data: dict) -> list[str]:
        """Check that all OIDs are unique across all element types.

        :param data: the intermediate JSON dict
        :returns: list of error messages for duplicate OIDs
        """
        oid_sources = []

        # Collect (oid_value, source_description) pairs
        for i, ds in enumerate(data.get("datasets", [])):
            oid_sources.append((ds.get("oid"), f"datasets[{i}] ({ds.get('name', '?')})"))
        for i, var in enumerate(data.get("variables", [])):
            oid_sources.append((var.get("oid"), f"variables[{i}] ({var.get('name', '?')})"))
        for i, vl in enumerate(data.get("value_levels", [])):
            oid_sources.append((vl.get("item_oid"), f"value_levels[{i}] item_oid ({vl.get('name', '?')})"))
        for i, wc in enumerate(data.get("where_clauses", [])):
            oid_sources.append((wc.get("oid"), f"where_clauses[{i}]"))
        for i, cl in enumerate(data.get("codelists", [])):
            oid_sources.append((cl.get("oid"), f"codelists[{i}] ({cl.get('name', '?')})"))
        for i, d in enumerate(data.get("dictionaries", [])):
            oid_sources.append((d.get("oid"), f"dictionaries[{i}] ({d.get('name', '?')})"))
        for i, m in enumerate(data.get("methods", [])):
            oid_sources.append((m.get("oid"), f"methods[{i}] ({m.get('name', '?')})"))
        for i, c in enumerate(data.get("comments", [])):
            oid_sources.append((c.get("oid"), f"comments[{i}]"))
        for i, s in enumerate(data.get("standards", [])):
            oid_sources.append((s.get("oid"), f"standards[{i}] ({s.get('name', '?')})"))

        # Find duplicates
        seen = {}
        errors = []
        for oid, source in oid_sources:
            if oid is None:
                continue
            if oid in seen:
                errors.append(f"Duplicate OID '{oid}': found in {seen[oid]} and {source}")
            else:
                seen[oid] = source
        return errors

    def check_cross_references(self, data: dict) -> tuple[list[str], list[str]]:
        """Check cross-reference integrity in intermediate JSON.

        :param data: the intermediate JSON dict
        :returns: tuple of (errors, warnings)
        """
        errors = []
        warnings = []

        # Collect defined OIDs by type
        codelist_oids = {cl.get("oid") for cl in data.get("codelists", [])}
        codelist_oids |= {d.get("oid") for d in data.get("dictionaries", [])}
        method_oids = {m.get("oid") for m in data.get("methods", [])}
        comment_oids = {c.get("oid") for c in data.get("comments", [])}
        wc_oids = {wc.get("oid") for wc in data.get("where_clauses", [])}
        vl_oids = {vl.get("vl_oid") for vl in data.get("value_levels", [])}
        variable_oids = {var.get("oid") for var in data.get("variables", [])}
        standard_oids = {s.get("oid") for s in data.get("standards", [])}

        # Check variable cross-references
        for i, var in enumerate(data.get("variables", [])):
            var_desc = f"variables[{i}] ({var.get('name', '?')})"
            if var.get("codelist_oid") and var["codelist_oid"] not in codelist_oids:
                errors.append(f"{var_desc}: codelist_oid '{var['codelist_oid']}' not found in codelists or dictionaries")
            if var.get("method_oid") and var["method_oid"] not in method_oids:
                errors.append(f"{var_desc}: method_oid '{var['method_oid']}' not found in methods")
            if var.get("comment_oid") and var["comment_oid"] not in comment_oids:
                errors.append(f"{var_desc}: comment_oid '{var['comment_oid']}' not found in comments")
            if var.get("valuelist_oid") and var["valuelist_oid"] not in vl_oids:
                errors.append(f"{var_desc}: valuelist_oid '{var['valuelist_oid']}' not found in value_levels")

        # Check value-level cross-references
        for i, vl in enumerate(data.get("value_levels", [])):
            vl_desc = f"value_levels[{i}] ({vl.get('name', '?')})"
            if vl.get("where_clause_oid") and vl["where_clause_oid"] not in wc_oids:
                errors.append(f"{vl_desc}: where_clause_oid '{vl['where_clause_oid']}' not found in where_clauses")
            if vl.get("codelist_oid") and vl["codelist_oid"] not in codelist_oids:
                errors.append(f"{vl_desc}: codelist_oid '{vl['codelist_oid']}' not found in codelists or dictionaries")
            if vl.get("method_oid") and vl["method_oid"] not in method_oids:
                errors.append(f"{vl_desc}: method_oid '{vl['method_oid']}' not found in methods")
            if vl.get("comment_oid") and vl["comment_oid"] not in comment_oids:
                errors.append(f"{vl_desc}: comment_oid '{vl['comment_oid']}' not found in comments")

        # Check dataset cross-references
        for i, ds in enumerate(data.get("datasets", [])):
            ds_desc = f"datasets[{i}] ({ds.get('name', '?')})"
            if ds.get("comment_oid") and ds["comment_oid"] not in comment_oids:
                errors.append(f"{ds_desc}: comment_oid '{ds['comment_oid']}' not found in comments")
            if ds.get("standard_oid") and ds["standard_oid"] not in standard_oids:
                errors.append(f"{ds_desc}: standard_oid '{ds['standard_oid']}' not found in standards")

        # Check where clause range_check item_oid references
        for i, wc in enumerate(data.get("where_clauses", [])):
            for j, rc in enumerate(wc.get("range_checks", [])):
                if rc.get("item_oid") and rc["item_oid"] not in variable_oids:
                    warnings.append(
                        f"where_clauses[{i}].range_checks[{j}]: item_oid '{rc['item_oid']}' "
                        f"not found in variables (may reference a value-level item)"
                    )

        return errors, warnings

    def validate_all(self, data: dict) -> tuple[list[str], list[str]]:
        """Run all validations: schema, OID uniqueness, and cross-references.

        :param data: the intermediate JSON dict
        :returns: tuple of (errors, warnings)
        """
        errors = self.validate_schema(data)
        if errors:
            # Schema errors make cross-reference checking unreliable
            return errors, []

        errors.extend(self.check_oid_uniqueness(data))
        xref_errors, warnings = self.check_cross_references(data)
        errors.extend(xref_errors)
        return errors, warnings
