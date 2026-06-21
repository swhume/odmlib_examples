# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains example applications demonstrating the **odmlib** Python package for working with CDISC 
ODM (Operational Data Model) and its extensions, particularly Define-XML v2.0/v2.1. The odmlib package provides an 
object-oriented interface for creating and processing ODM documents.

- **Core dependency**: [odmlib](https://github.com/swhume/odmlib) (`pip install odmlib`)
- **Author**: Sam Hume
- **License**: MIT

## Running Examples

Each example directory is self-contained with its own `requirements.txt`. Install dependencies per example:

```bash
cd <example_directory>
pip install -r requirements.txt
```

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

**CDISC Library API** (requires API key):
```bash
python library_xml/library_xml.py -d -e "/mdr/sdtmig/3-4" -k YOUR_API_KEY
```

**CT to JSON**:
```bash
python ct2json/ct2json.py -x ./data/sdtm-ct.xml -j ./data/sdtm-ct.json
```

**Jupyter notebooks**:
```bash
jupyter notebook notebooks/first_odm.ipynb
```

## Architecture

### Directory Structure
- `get_started/` - Basic odmlib intro (start here)
- `xlsx2define2-1/` - Excel → Define-XML v2.1 (current)
- `define2-1-to-xlsx/` - Define-XML v2.1 → Excel (current)
- `xls2define/`, `define2xls/` - v2.0 versions (deprecated)
- `library_xml/` - CDISC Library API integration
- `ct2json/`, `ct2odm/` - Controlled Terminology conversions
- `merge_odm/` - ODM file merging
- `snippets/` - Small utilities and extension examples (Veeva, OSB)
- `notebooks/` - Educational Jupyter notebooks

### Code Patterns

Each conversion tool follows a consistent pattern with separate modules per ODM component:

```
odm.py           # Root ODM/Define object creation
Study.py         # Study/MetaDataVersion setup
Datasets.py      # ItemGroupDef (datasets)
Variables.py     # ItemDef (variables)
CodeLists.py     # CodeList management
Methods.py       # MethodDef definitions
Comments.py      # CommentDef metadata
Documents.py     # Document references (leaf elements)
define_object.py # Base class with common functionality
```

Each component class inherits from `define_object.DefineObject` and implements `create_define_objects(sheet, objects, lang, acrf)` to parse Excel sheets and create odmlib objects.

### Extension Models

Custom ODM extensions are packaged as separate model directories:
- `library_define_1_0/`, `library_odm_1_0/` - Library-XML
- `veeva_1_0/`, `veeva_odm_1_0/` - Veeva extensions
- `osb_odm_1_0/` - OSB extensions

### Validation

odmlib provides built-in validation:
- XML Schema validation via `xmlschema`
- OID reference validation via `odmlib.define_2_1.rules.oid_ref`
- Metadata conformance via `odmlib.define_2_1.rules.metadata_schema`

## Notes

- XSD schema file paths in examples may need adjustment for your environment
- The v2.0 examples (`xls2define/`, `define2xls/`) are deprecated; use v2.1 versions
- These are demonstration applications, not production-ready tools
