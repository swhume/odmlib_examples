# xlsx2define2-1

## Introduction

The xlsx2define2-1 program is an odmlib example application that generates a Define-XML v2.1 file from an Excel
spreadsheet containing the study metadata. The spreadsheet format makes it easier to edit or create metadata content
for inclusion in a Define-XML v2.1 file. The companion [define2-1-to-xlsx](../define2-1-to-xlsx) program performs
the reverse conversion, taking a Define-XML v2.1 file and producing the metadata spreadsheet.

This example demonstrates odmlib v0.2.0 features including the structured exception hierarchy, the dynamic OID
checker, and collect-all-errors validation.

## Prerequisites

- Python 3.9+
- [odmlib](https://github.com/swhume/odmlib) v0.2.0 or later

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or install odmlib directly from the repository for the latest version:

```bash
pip install /path/to/odmlib
```

## Usage

### Basic Conversion

Generate a Define-XML v2.1 file from the example Excel metadata spreadsheet:

```bash
python xlsx2define2-1.py -e ./data/odmlib-define-metadata.xlsx -d ./data/odmlib-roundtrip-define.xml
```

### With Conformance Checking

Run OID validation and metadata conformance checks before writing the Define-XML file. This uses odmlib v0.2.0's
`validate(collect_errors=True)` mode to report all validation errors at once rather than stopping at the first:

```bash
python xlsx2define2-1.py -c -e ./data/odmlib-define-metadata.xlsx -d ./data/odmlib-roundtrip-define.xml
```

### With XML Schema Validation

Schema validate the generated Define-XML file against the Define-XML v2.1 XSD:

Uses the XSD files in the odmlib_examples/schema directory as the default:
```bash
python xlsx2define2-1.py -v -c -e ./data/odmlib-define-metadata.xlsx -d ./data/odmlib-roundtrip-define.xml
```

Specifies the location of the XSD file explicitly using the `-s` argument:
```bash
python xlsx2define2-1.py -v -c -e ./data/odmlib-define-metadata.xlsx -d ./data/odmlib-roundtrip-define.xml \
  -s "/path/to/define2-1-0.xsd"
```

### Command-Line Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `-e, --excel` | Path to the input Excel metadata file | Yes |
| `-d, --define` | Path for the output Define-XML file (default: `./odmlib-define-xml.xml`) | No |
| `-c, --check` | Run conformance checks (OID validation, metadata schema) | No |
| `-v, --validate` | Schema validate the output Define-XML file | No |
| `-s, --schema` | Path to the Define-XML v2.1 XSD schema file (required with `-v`) | No |

## odmlib v0.2.0 Features Demonstrated

- **Structured Exception Hierarchy**: Uses `OdmlibValidationError` for input validation errors instead of bare
  `ValueError`, providing clearer error classification.
- **Dynamic OID Checker**: Uses `create_oid_checker("define_2_1")` to dynamically generate OID reference/definition
  checking based on model introspection, replacing the deprecated manual `OIDRef` class.
- **Collect-All-Errors Validation**: Uses `odm.validate(collect_errors=True)` to run all validation checks (element
  ordering, OID integrity, metadata conformance) and report every error found, rather than stopping at the first
  failure.
- **MetadataSchema Conformance**: Passes a `MetadataSchema` conformance checker to the unified `validate()` method.

## Architecture

The program follows a worksheet-driven architecture where each Excel worksheet tab maps to a dedicated Python module
that creates the corresponding odmlib Define-XML elements.

### Conversion Flow

1. Load the Excel workbook and iterate through worksheets
2. Each worksheet is processed by its corresponding loader class via `SHEET_LOADERS` dispatch
3. Loader classes parse rows and create odmlib model objects, stored in a shared `define_objects` dictionary
4. The `_build_doc()` method assembles all objects into a complete Define-XML document
5. Optionally run conformance checks using `validate(collect_errors=True)`
6. Write the document to XML using odmlib's `write_xml()` method

### File Listing

| File | Description |
|------|-------------|
| `xlsx2define2-1.py` | Main script with `Xls2Define` converter and `DefineValidator` classes |
| `define_object.py` | `DefineObject` base class with common Excel parsing utilities |
| `odm.py` | Creates the root ODM/Define element with file-level metadata |
| `Study.py` | Parses Study worksheet; creates Study and MetaDataVersion objects |
| `Standards.py` | Parses Standards worksheet; creates Standard objects |
| `Datasets.py` | Parses Datasets worksheet; creates ItemGroupDef objects |
| `Variables.py` | Parses Variables worksheet; creates ItemDef and ItemRef objects |
| `ValueLevel.py` | Parses ValueLevel worksheet; creates ValueListDef objects |
| `WhereClauses.py` | Parses WhereClauses worksheet; creates WhereClauseDef objects |
| `CodeLists.py` | Parses CodeLists worksheet; creates CodeList with CodeListItem or EnumeratedItem |
| `Dictionaries.py` | Parses Dictionaries worksheet; creates CodeList with ExternalCodeList |
| `Methods.py` | Parses Methods worksheet; creates MethodDef objects |
| `Comments.py` | Parses Comments worksheet; creates CommentDef objects |
| `Documents.py` | Parses Documents worksheet; creates leaf (document reference) objects |
| `supporting_docs.py` | Creates AnnotatedCRF and SupplementalDoc elements |

### Input / Output

- **Input**: Excel workbook with 11 worksheets (Study, Standards, Datasets, Variables, ValueLevel, WhereClauses,
  CodeLists, Dictionaries, Methods, Comments, Documents). See `data/odmlib-define-metadata.xlsx` for an example.
- **Output**: Define-XML v2.1 file. See `data/odmlib-roundtrip-define.xml` for an example.

## Limitations

These are example programs intended to demonstrate odmlib capabilities. They are not production-ready applications.
Contributions and bug reports are welcome.
