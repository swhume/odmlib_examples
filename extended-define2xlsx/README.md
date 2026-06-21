# define2-1-to-xlsx

## Introduction

The define2-1-to-xlsx program is an odmlib example application that converts a Define-XML v2.1 file into an Excel
spreadsheet containing the study metadata. The spreadsheet format makes it easier to review, edit, or create new
metadata content. The companion [xlsx2define2-1](../xlsx2define2-1) program performs the reverse conversion, taking
the metadata spreadsheet and generating a Define-XML v2.1 file.

This example demonstrates odmlib v0.2.0 features including the `ODMLoader`/`XMLDefineLoader` parsing API,
`MetaDataVersion.find()` for cross-reference lookups, and structured exceptions.

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

Convert a Define-XML v2.1 file to an Excel spreadsheet:

```bash
python define2-1-to-xlsx.py -d ./data/odmlib-roundtrip-define.xml -p ./data/
```

### With Schema Validation

Validate the Define-XML file against the XSD schema before converting:

```bash
python define2-1-to-xlsx.py -v -d ./data/odmlib-roundtrip-define.xml -p ./data/ \
  -s "/path/to/define2-1-0.xsd"
```

### With Custom Language and Output Filename

```bash
python define2-1-to-xlsx.py -d ./data/odmlib-roundtrip-define.xml -p ./data/ -l en -e my-metadata.xlsx
```

### Command-Line Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `-d, --define` | Path to the input Define-XML v2.1 file | Yes |
| `-p, --path` | Directory path for the output Excel file (default: `./`) | No |
| `-e, --excel` | Name of the output Excel file (default: `odmlib-define-metadata.xlsx`) | No |
| `-v, --validate` | Schema validate the Define-XML file before conversion | No |
| `-s, --schema` | Path to the Define-XML v2.1 XSD schema file (required with `-v`) | No |
| `-l, --lang` | Language code for TranslatedText elements (default: `en`) | No |

## odmlib v0.2.0 Features Demonstrated

- **ODMLoader / XMLDefineLoader**: Uses odmlib's loader API to parse Define-XML v2.1 files into a fully navigable
  object model with `loader.MetaDataVersion()` and `loader.Study()`.
- **MetaDataVersion.find()**: Uses `mdv.find("ItemDef", "OID", oid)` for cross-reference lookups when extracting
  related metadata (e.g., finding the ItemDef referenced by an ItemRef).
- **Structured Exceptions**: Uses `OdmlibValidationError` for data integrity errors and
  `OdmlibSchemaValidationError` for XML schema validation failures, replacing bare `ValueError` and raw xmlschema
  exceptions.

## Architecture

The program follows an extractor-per-worksheet architecture. Each Define-XML metadata component is extracted by a
dedicated Python module that writes its output to a CSV file. The CSV files are then combined into a single Excel
workbook.

### Conversion Flow

1. Load the Define-XML file using `ODMLoader` with `XMLDefineLoader`
2. Extract `MetaDataVersion` and `Study` objects from the loaded document
3. Each extractor module iterates through the relevant odmlib collections (e.g., `mdv.ItemGroupDef`, `mdv.CodeList`)
4. Cross-references are resolved using `mdv.find()` (e.g., finding an ItemDef by its OID)
5. Each extractor writes its data to a CSV file
6. `ExcelDefineFile` combines all CSV files into a single Excel workbook with formatted headers

### File Listing

| File | Description |
|------|-------------|
| `define2-1-to-xlsx.py` | Main script with `Define2Xls` converter and `DefineValidator` classes |
| `excel_define_file.py` | `ExcelDefineFile` class that combines CSV files into an Excel workbook |
| `study.py` | Extracts Study-level metadata (StudyName, Description, ProtocolName) |
| `standards.py` | Extracts Standards declarations |
| `datasets.py` | Extracts ItemGroupDef (dataset) definitions |
| `variables.py` | Extracts ItemDef (variable) definitions and ItemRef ordering |
| `value_level.py` | Extracts ValueListDef and value-level ItemRef metadata |
| `where_clauses.py` | Extracts WhereClauseDef and RangeCheck criteria |
| `codelists.py` | Extracts CodeList definitions with CodeListItem or EnumeratedItem terms |
| `dictionaries.py` | Extracts CodeList definitions with ExternalCodeList references |
| `methods.py` | Extracts MethodDef definitions with FormalExpressions |
| `comments.py` | Extracts CommentDef definitions |
| `documents.py` | Extracts leaf (document reference) elements |

### Input / Output

- **Input**: Define-XML v2.1 file. See `data/odmlib-roundtrip-define.xml` for an example.
- **Output**: Excel workbook with 11 worksheets (Study, Standards, Datasets, Variables, ValueLevel, WhereClauses,
  CodeLists, Dictionaries, Methods, Comments, Documents). See `data/odmlib-define-metadata.xlsx` for an example.

## Limitations

These are example programs intended to demonstrate odmlib capabilities. They are not production-ready applications.
Contributions and bug reports are welcome.
