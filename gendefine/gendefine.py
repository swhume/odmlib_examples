"""gendefine: Generate Define-XML v2.1 from metadata spreadsheets using JSON mapping configurations.

This is the main entry point and CLI for the gendefine pipeline. It supports multiple
modes of operation:
- Full pipeline: spreadsheet + mapping -> intermediate JSON -> Define-XML
- Extract only: spreadsheet + mapping -> intermediate JSON
- Generate only: intermediate JSON -> Define-XML
- Validate mapping: check a mapping file against the schema
- Validate JSON: check intermediate JSON against schema + cross-references
"""

import argparse
import json
import os
import sys

from config_loader import MappingConfig
from spreadsheet_reader import SpreadsheetReader
from intermediate_builder import IntermediateBuilder
from define_builder import DefineBuilder
from validator import DefineValidator, IntermediateValidator
from oid_generator import OIDGenerator
from value_transformer import ValueTransformer


def set_cmd_line_args():
    """Define and parse command-line arguments.

    :return: argparse.Namespace with parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Generate Define-XML v2.1 from a metadata spreadsheet using a JSON mapping."
    )
    parser.add_argument(
        "-e", "--excel",
        help="path to the metadata spreadsheet (.xlsx)",
        dest="excel_file"
    )
    parser.add_argument(
        "-m", "--mapping",
        help="path to the JSON mapping configuration file",
        dest="mapping_file"
    )
    parser.add_argument(
        "-d", "--define",
        help="path for the output Define-XML file",
        dest="define_file",
        default="./gendefine-output.xml"
    )
    parser.add_argument(
        "-j", "--json",
        help="path for the intermediate JSON file",
        dest="json_file"
    )
    parser.add_argument(
        "-s", "--schema",
        help="path to the Define-XML v2.1 schema for validation",
        dest="schema_file",
        default="../schema/cdisc-define-2.1/define2-1-0.xsd"
    )
    parser.add_argument(
        "-v", "--validate",
        help="validate the output Define-XML against the schema",
        action="store_true",
        dest="is_validate"
    )
    parser.add_argument(
        "-c", "--check",
        help="run conformance checks on the generated Define-XML",
        action="store_true",
        dest="is_check"
    )
    parser.add_argument(
        "--extract-only",
        help="produce only the intermediate JSON (no Define-XML generation)",
        action="store_true",
        dest="extract_only"
    )
    parser.add_argument(
        "--generate-only",
        help="consume intermediate JSON to produce Define-XML (requires -j, ignores -e and -m)",
        action="store_true",
        dest="generate_only"
    )
    parser.add_argument(
        "--validate-mapping",
        help="validate the mapping file against the schema and exit",
        action="store_true",
        dest="validate_mapping"
    )
    parser.add_argument(
        "--validate-json",
        help="validate an intermediate JSON file against the schema and check cross-references",
        action="store_true",
        dest="validate_json"
    )
    return parser.parse_args()


def validate_mapping(mapping_file: str) -> int:
    """Load and validate a mapping file, print the result.

    :param mapping_file: path to the JSON mapping configuration file
    :returns: 0 on success, 1 on failure
    """
    try:
        config = MappingConfig(mapping_file)
        print(f"Mapping '{config.mapping_name}' is valid.")
        print(f"  Version: {config.mapping_version}")
        print(f"  Define-XML target: {config.define_version}")
        print(f"  Worksheets: {', '.join(config.worksheet_names)}")
        return 0
    except FileNotFoundError:
        print(f"Error: mapping file not found: {mapping_file}")
        return 1
    except Exception as e:
        print(f"Mapping validation failed: {e}")
        return 1


def run_extract_only(excel_path: str, mapping_path: str, json_path: str) -> int:
    """Run extract-only mode: spreadsheet -> intermediate JSON.

    :returns: 0 on success, 1 on failure
    """
    try:
        # 1. Load mapping configuration
        config = MappingConfig(mapping_path)

        # 2. Read spreadsheet
        reader = SpreadsheetReader(config)
        raw_data = reader.read_workbook(excel_path)

        # 3. Build intermediate JSON
        oid_gen = OIDGenerator()
        transformer = ValueTransformer(config.value_transforms, config.defaults)
        builder = IntermediateBuilder(config, oid_gen, transformer)
        intermediate = builder.build(raw_data)
        intermediate["source_file"] = excel_path

        # 4. Validate intermediate JSON against schema
        iv = IntermediateValidator()
        errors = iv.validate_schema(intermediate)
        if errors:
            print(f"Warning: intermediate JSON has {len(errors)} schema issue(s):")
            for err in errors:
                print(f"  {err}")

        # 5. Write intermediate JSON
        with open(json_path, "w") as f:
            json.dump(intermediate, f, indent=2, default=str, ensure_ascii=False)

        # 6. Print extraction summary
        print(f"Intermediate JSON saved to {json_path}")
        print("Extraction summary:")
        print(f"  Datasets:      {len(intermediate.get('datasets', []))}")
        print(f"  Variables:     {len(intermediate.get('variables', []))}")
        print(f"  Value levels:  {len(intermediate.get('value_levels', []))}")
        print(f"  Where clauses: {len(intermediate.get('where_clauses', []))}")
        print(f"  Codelists:     {len(intermediate.get('codelists', []))}")
        print(f"  Dictionaries:  {len(intermediate.get('dictionaries', []))}")
        print(f"  Methods:       {len(intermediate.get('methods', []))}")
        print(f"  Comments:      {len(intermediate.get('comments', []))}")
        print(f"  Documents:     {len(intermediate.get('documents', []))}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_generate_only(json_path: str, define_path: str,
                      validate: bool, check: bool, schema_path: str) -> int:
    """Run generate-only mode: intermediate JSON -> Define-XML.

    :returns: 0 on success, 1 on failure
    """
    try:
        # 1. Load intermediate JSON
        with open(json_path) as f:
            data = json.load(f)

        # 2. Fill in missing optional sections as empty arrays
        for key in ("standards", "value_levels", "where_clauses", "codelists",
                     "dictionaries", "methods", "comments", "documents"):
            data.setdefault(key, [])

        # 3. Validate against intermediate schema
        iv = IntermediateValidator()
        errors = iv.validate_schema(data)
        if errors:
            print(f"Intermediate JSON validation failed ({len(errors)} error(s)):")
            for err in errors:
                print(f"  {err}")
            return 1

        # 4. Build Define-XML
        lang = data.get("study", {}).get("language", "en")
        define_builder = DefineBuilder(data, lang)
        odm = define_builder.build()

        # 5. Validate if requested
        if check:
            dv = DefineValidator()
            conf_errors = dv.check_conformance(odm)
            if conf_errors:
                print(f"Conformance check found {len(conf_errors)} error(s):")
                for i, err in enumerate(conf_errors, 1):
                    print(f"  {i}. {err}")
            else:
                print("Define-XML passes all validation checks (OIDs, conformance, element order)...")

        # 6. Write Define-XML
        odm.write_xml(define_path)
        print(f"Define-XML written to {define_path}")

        # 7. Schema validate after writing (needs the file on disk)
        if validate and schema_path:
            dv = DefineValidator()
            schema_errors = dv.validate_schema(define_path, schema_path)
            if schema_errors:
                print(f"Schema validation errors:")
                for err in schema_errors:
                    print(f"  {err}")
            else:
                print("Define-XML schema validation completed successfully...")

        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {json_path}: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_validate_json(json_path: str) -> int:
    """Validate intermediate JSON against schema and check cross-references.

    :returns: 0 on success (no errors), 1 on failure
    """
    try:
        with open(json_path) as f:
            data = json.load(f)

        iv = IntermediateValidator()
        errors, warnings = iv.validate_all(data)

        if errors:
            print(f"Validation found {len(errors)} error(s):")
            for i, err in enumerate(errors, 1):
                print(f"  {i}. {err}")
        else:
            print("Intermediate JSON is valid.")

        if warnings:
            print(f"\n{len(warnings)} warning(s):")
            for i, w in enumerate(warnings, 1):
                print(f"  {i}. {w}")

        return 1 if errors else 0
    except FileNotFoundError:
        print(f"Error: file not found: {json_path}")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {json_path}: {e}")
        return 1


def run_full_pipeline(excel_path, mapping_path, define_path, json_path,
                      validate, check, schema_path) -> int:
    """Run the full gendefine pipeline: spreadsheet -> intermediate JSON -> Define-XML.

    :returns: 0 on success, 1 on failure
    """
    try:
        # 1. Load mapping configuration
        config = MappingConfig(mapping_path)
        lang = config.global_settings.get("language", "en")

        # 2. Read spreadsheet
        reader = SpreadsheetReader(config)
        raw_data = reader.read_workbook(excel_path)

        # 3. Build intermediate JSON
        oid_gen = OIDGenerator()
        transformer = ValueTransformer(config.value_transforms, config.defaults)
        builder = IntermediateBuilder(config, oid_gen, transformer)
        intermediate = builder.build(raw_data)
        intermediate["source_file"] = excel_path

        # 4. Optionally save intermediate JSON
        if json_path:
            with open(json_path, "w") as f:
                json.dump(intermediate, f, indent=2, default=str)
            print(f"Intermediate JSON saved to {json_path}")

        # 5. Build Define-XML
        define_builder = DefineBuilder(intermediate, lang)
        odm = define_builder.build()

        # 6. Validate if requested
        if check:
            validator = DefineValidator()
            errors = validator.check_conformance(odm)
            if errors:
                print(f"Conformance check found {len(errors)} error(s):")
                for i, err in enumerate(errors, 1):
                    print(f"  {i}. {err}")
            else:
                print("Define-XML passes all validation checks (OIDs, conformance, element order)...")

        # 7. Write Define-XML
        odm.write_xml(define_path)
        print(f"Define-XML written to {define_path}")

        # 8. Schema validate after writing (needs the file on disk)
        if validate and schema_path:
            validator = DefineValidator()
            errors = validator.validate_schema(define_path, schema_path)
            if errors:
                print(f"Schema validation errors:")
                for err in errors:
                    print(f"  {err}")
            else:
                print("Define-XML schema validation completed successfully...")

        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point for gendefine."""
    args = set_cmd_line_args()

    # --validate-mapping mode
    if args.validate_mapping:
        if not args.mapping_file:
            print("Error: --validate-mapping requires -m/--mapping")
            sys.exit(1)
        sys.exit(validate_mapping(args.mapping_file))

    # --validate-json mode
    if args.validate_json:
        if not args.json_file:
            print("Error: --validate-json requires -j/--json")
            sys.exit(1)
        sys.exit(run_validate_json(args.json_file))

    # Mutual exclusivity check
    if args.extract_only and args.generate_only:
        print("Error: --extract-only and --generate-only are mutually exclusive")
        sys.exit(1)

    # --extract-only mode
    if args.extract_only:
        if not args.json_file:
            print("Error: --extract-only requires -j/--json")
            sys.exit(1)
        if not args.excel_file or not args.mapping_file:
            print("Error: --extract-only requires -e/--excel and -m/--mapping")
            sys.exit(1)
        sys.exit(run_extract_only(args.excel_file, args.mapping_file, args.json_file))

    # --generate-only mode
    if args.generate_only:
        if not args.json_file:
            print("Error: --generate-only requires -j/--json")
            sys.exit(1)
        # Default output filename from JSON filename if -d not explicitly provided
        define_path = args.define_file
        if define_path == "./gendefine-output.xml" and args.json_file:
            base = os.path.splitext(os.path.basename(args.json_file))[0]
            define_path = os.path.join(os.path.dirname(args.json_file) or ".", f"{base}-define.xml")
        sys.exit(run_generate_only(
            args.json_file, define_path,
            args.is_validate, args.is_check, args.schema_file
        ))

    # Full pipeline mode
    if not args.excel_file or not args.mapping_file:
        print("Error: full pipeline requires -e/--excel and -m/--mapping")
        sys.exit(1)
    sys.exit(run_full_pipeline(
        args.excel_file, args.mapping_file, args.define_file,
        args.json_file, args.is_validate, args.is_check, args.schema_file
    ))


if __name__ == "__main__":
    main()
