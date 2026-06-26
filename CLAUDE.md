# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains example applications demonstrating the **odmlib** Python package for working with CDISC 
ODM (Operational Data Model) and its extensions, particularly Define-XML v2.1. The odmlib package provides an 
object-oriented interface for creating and processing ODM documents.

- **Core dependency**: [odmlib](https://github.com/swhume/odmlib) — examples target **v0.2.0** and pin
  `odmlib>=0.2.0rc1` (installs the 0.2.0 release candidate today and prefers final 0.2.0 once published)
- **Author**: Sam Hume
- **License**: MIT

## Running Examples

Each example directory is self-contained with its own `requirements.txt`. Install dependencies per example:

```bash
cd <example_directory>
pip install -r requirements.txt
```

Or install everything at once from the repo-root `requirements.txt`.

### Key Commands

**Excel to Define-XML v2.1 (recommended)**:
```bash
python xlsx2define2-1/xlsx2define2-1.py -e ./data/odmlib-define-metadata.xlsx -d ./data/odmlib-roundtrip-define.xml
```

With validation and conformance checking:
```bash
python xlsx2define2-1/xlsx2define2-1.py -v -c -e ./data/odmlib-define-metadata.xlsx -d ./data/odmlib-roundtrip-define.xml -s "/path/to/define2-1-0.xsd"
```

**Define-XML v2.1 to Excel**:
```bash
python define2-1-to-xlsx/define2-1-to-xlsx.py -d ./data/sdtm-xls-define.xml -p ./data/
```

**Get started (create + read an ODM document)**:
```bash
cd get_started && python get_started.py
```

**CDISC Library API** (requires API key):
```bash
python library_xml/library_xml.py -d -e "/mdr/sdtmig/3-4" -k YOUR_API_KEY
```

**CT to JSON / CT to ODM**:
```bash
python ct2json/ct2json.py -x ./data/sdtm-ct.xml -j ./data/sdtm-ct.json
python ct2odm/ct2odm.py -c ./data/sdtm-ct.txt -x ./data/sdtm-ct.xml -s SDTM -d 2021-06-25
```

**Jupyter notebooks**:
```bash
jupyter notebook notebooks/read_odm.ipynb
```

## Architecture

### Directory Structure
- `get_started/` - Basic odmlib intro (start here)
- `xlsx2define2-1/` - Excel → Define-XML v2.1 (canonical example)
- `define2-1-to-xlsx/` - Define-XML v2.1 → Excel (canonical example)
- `library_xml/` - CDISC Library API integration (uses local extension models)
- `ct2json/`, `ct2odm/` - Controlled Terminology conversions
- `merge_odm/` - ODM file merging
- `snippets/` - Focused single-feature v0.2 scripts (builders, context managers, validation,
  element re-ordering, modifying documents, conversions, ARM, and a `custom-extension/` tutorial)
- `notebooks/` - Educational Jupyter notebooks for v0.2 features
- `schema/` - Reference XSDs (ODM 1.3.2, Define-XML 2.1, ARM 1.0)

Some programs have moved to their own repositories: **gendefine** and **extended-define2xlsx**
(standalone repos), and the narrow/vendor-specific snippets (Veeva, OSB), deprecated Define-XML v2.0
converters (`xls2define`, `define2xls`), and early notebooks now live in **odmlib_snippets**.

### Code Patterns

The Excel ↔ Define-XML tools (`xlsx2define2-1/`, `define2-1-to-xlsx/`) follow a consistent pattern with
separate modules per ODM component:

```
odm.py           # Root ODM/Define object creation
study.py         # Study/MetaDataVersion setup
datasets.py      # ItemGroupDef (datasets)
variables.py     # ItemDef (variables)
codelists.py     # CodeList management
methods.py       # MethodDef definitions
comments.py      # CommentDef metadata
documents.py     # Document references (leaf elements)
define_object.py # Base class with common functionality
```

### Extension Models

Custom ODM extensions are packaged as separate model directories (a `model.py` that subclasses the
base model and registers a custom namespace, loaded with `local_model=True`):
- `library_xml/library_define_1_0/`, `library_xml/library_odm_1_0/` - Library-XML
- `snippets/custom-extension/acme_odm_1_0/` - minimal tutorial extension

### Validation (odmlib v0.2.0)

- XML Schema validation via `odmlib.odm_parser.ODMSchemaValidator` (accepts `xsd_file=` or
  `standard=`/`version=` to resolve a bundled schema)
- OID reference/definition validation via `create_oid_checker("<model_package>")` plus
  `element.verify_oids(checker)` or `element.validate(collect_errors=True, oid_checker=checker)`
- Metadata conformance via `odmlib.define_2_1.rules.metadata_schema.MetadataSchema`
- The structured exception hierarchy: `OdmlibValidationError`, `OdmlibOIDError`,
  `OdmlibConformanceError`, `OdmlibElementOrderError`, `OdmlibSchemaValidationError`

## Notes

- XSD schema file paths in examples may need adjustment for your environment
- These are demonstration applications, not production-ready tools
- See `REFACTOR_ODMLIB_EXAMPLES.md` for the rationale behind the current repo organization and
  `REFACTOR_TESTING_GUIDE.md` for how to verify the examples
