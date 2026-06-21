# gendefine

Generate Define-XML v2.1 from metadata spreadsheets using JSON mapping configurations.

## Overview

`gendefine` is an odmlib example that generalizes Excel-to-Define-XML generation. Instead of hard-coding
column names and worksheet layouts (as in `xlsx2define2-1`), gendefine uses a JSON mapping configuration
to decouple the spreadsheet format from the Define-XML generation logic.

This enables a single codebase to process a variety of metadata spreadsheet formats — only a new mapping
configuration file is needed for each format.

### How It Differs from xlsx2define2-1

| Aspect | xlsx2define2-1 | gendefine |
|---|---|---|
| Worksheet handling | One Python module per worksheet | Single reader driven by JSON mapping |
| Column references | Hard-coded column name strings | Column names declared in JSON mapping |
| OID handling | Mix of column-sourced and generated | Unified strategy per mapping |
| Adding a new format | Rewrite handler modules | Write a new JSON mapping file |
| Intermediate representation | None (spreadsheet to odmlib directly) | Explicit intermediate JSON |

## Quick Start

```bash
cd gendefine
pip install -r requirements.txt
```

**Original format (odmlib-define-metadata.xlsx):**
```bash
python gendefine.py -e data/odmlib-define-metadata.xlsx \
                    -m mappings/odmlib-format.json \
                    -d data/output-define.xml
```

**Standard-Spec format:**
```bash
python gendefine.py -e data/Standard-Spec.xlsx \
                    -m mappings/standard-spec.json \
                    -d data/standard-spec-define.xml
```

## Architecture

### Three-Stage Pipeline

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Metadata XLSX   │     │   JSON Mapping    │     │  Define-XML v2.1 │
│  (any format)    │────>│   Configuration   │────>│  Output File     │
└─────────────────┘     └──────────────────┘     └──────────────────┘
        │                        │
        │   Stage 1: Extract     │   Stage 2: Transform
        v                        v
┌──────────────────────────────────────┐     Stage 3: Generate
│  Intermediate JSON                    │────────────────────────>
│  (normalized metadata)               │
└──────────────────────────────────────┘
```

**Stage 1 — Extract:** Read the spreadsheet using the mapping to identify which columns correspond
to which Define-XML concepts. Produce normalized intermediate JSON.

**Stage 2 — Transform:** Apply mapping rules (OID generation, value transforms, defaults) to produce
a fully resolved metadata payload.

**Stage 3 — Generate:** Consume the resolved JSON and use odmlib to build the Define-XML v2.1 object
tree, then serialize to XML.

### Module Overview

| Module | Responsibility |
|---|---|
| `gendefine.py` | Main entry point, CLI, pipeline orchestration |
| `config_loader.py` | Load and validate JSON mapping configurations |
| `spreadsheet_reader.py` | Generic spreadsheet reading driven by mapping |
| `intermediate_builder.py` | Build intermediate JSON from mapped spreadsheet data |
| `define_builder.py` | Build odmlib Define-XML objects from intermediate JSON |
| `oid_generator.py` | Pattern-based OID generation with uniqueness tracking |
| `value_transformer.py` | Lookup, type coercion, regex parse, and default transforms |
| `where_clause_parser.py` | Parse inline where clause expressions from text values |
| `validator.py` | Schema validation and conformance checking |

## Usage Guide

### Full Pipeline Mode

Generate Define-XML directly from a spreadsheet:

```bash
python gendefine.py -e spreadsheet.xlsx -m mapping.json -d output-define.xml
```

Save intermediate JSON alongside Define-XML:

```bash
python gendefine.py -e spreadsheet.xlsx -m mapping.json -d output-define.xml -j intermediate.json
```

With validation and conformance checking:

```bash
python gendefine.py -e spreadsheet.xlsx -m mapping.json -d output-define.xml \
                    -v -c -s ../schema/cdisc-define-2.1/define2-1-0.xsd
```

### Extract-Only Mode

Produce intermediate JSON for inspection or editing:

```bash
python gendefine.py --extract-only -e spreadsheet.xlsx -m mapping.json -j intermediate.json
```

### Generate-Only Mode

Produce Define-XML from intermediate JSON (possibly hand-edited):

```bash
python gendefine.py --generate-only -j intermediate.json -d output-define.xml
```

### Validation Modes

Validate a mapping file against the schema:

```bash
python gendefine.py --validate-mapping -m mappings/odmlib-format.json
```

Validate intermediate JSON (schema + OID uniqueness + cross-references):

```bash
python gendefine.py --validate-json -j intermediate.json
```

### CLI Reference

| Argument | Description |
|---|---|
| `-e`, `--excel` | Path to the metadata spreadsheet (.xlsx) |
| `-m`, `--mapping` | Path to the JSON mapping configuration file |
| `-d`, `--define` | Path for the output Define-XML file (default: `./gendefine-output.xml`) |
| `-j`, `--json` | Path for the intermediate JSON file |
| `-s`, `--schema` | Path to the Define-XML v2.1 XSD schema (default: `../schema/cdisc-define-2.1/define2-1-0.xsd`) |
| `-v`, `--validate` | Validate output Define-XML against the XSD schema |
| `-c`, `--check` | Run conformance checks (OID refs, metadata) on generated Define-XML |
| `--extract-only` | Produce only the intermediate JSON (no Define-XML) |
| `--generate-only` | Consume intermediate JSON to produce Define-XML (ignores `-e` and `-m`) |
| `--validate-mapping` | Validate a mapping file against the schema and exit |
| `--validate-json` | Validate intermediate JSON (schema + cross-references) and exit |

## Mapping Configuration Guide

A mapping file is a JSON document that tells gendefine how to read a specific spreadsheet format and
translate it into Define-XML. Each supported spreadsheet format has its own mapping file.

### Creating a New Mapping

1. **Inventory worksheets:** List each worksheet name and whether it uses key-value pairs
   (`attribute_value`) or a header row with data rows (`tabular`).

2. **Map to Define-XML targets:** Identify which Define-XML element(s) each worksheet produces
   (e.g., Datasets → `ItemGroupDef`, Variables → `["ItemDef", "ItemRef"]`).

3. **Map columns to attributes:** For each column, specify `maps_to` (the target attribute name),
   and optionally `also` (additional attributes to populate with the same value).

4. **Define OID strategy:** Set `oid_generation_strategy` in `global_settings`:
   - `"column"` — OIDs are read from the spreadsheet (requires an OID column)
   - `"pattern"` — OIDs are generated from templates like `"IG.{Dataset}"`

5. **Define value transforms:** Add lookup tables, type coercions, or regex parsers for columns
   that need transformation (e.g., `Core` → `Mandatory`).

6. **Set defaults:** Provide default values for required Define-XML attributes not present in
   the spreadsheet.

7. **Mark excluded columns:** Flag columns that should not map to Define-XML with
   `"ignore_for_define": true`.

8. **Validate:** Run `python gendefine.py --validate-mapping -m your-mapping.json`

### Key Mapping Features

- **`column_map`** — Maps spreadsheet column names to Define-XML attributes
- **`also`** — Populates additional attributes from the same column (string or array)
- **`oid_patterns`** — Templates for generating OIDs (e.g., `"IG.{Dataset}"`)
- **`value_transforms`** — Named transform rules (lookup, type_coercion, regex_parse, custom)
- **`defaults`** — Default values for attributes missing from the spreadsheet
- **`ignore_for_define`** — Excludes informational columns from Define-XML generation
- **`optional`** — Marks columns that can contain empty/null values

See `mappings/README.md` for the complete mapping configuration reference.

## Intermediate JSON Format

The intermediate JSON is a normalized, format-agnostic metadata payload produced during extraction.

### Purpose and Benefits

- **Transparency:** Inspect normalized metadata before Define-XML generation
- **Editability:** Manually add or correct metadata not in the spreadsheet
- **Testability:** Deterministic, diff-friendly artifact for regression testing
- **Decoupling:** Extract and generate stages can evolve independently

### Structure Overview

```json
{
  "gendefine_version": "1.0",
  "source_mapping": "odmlib-format",
  "source_file": "path/to/spreadsheet.xlsx",
  "study": { "oid": "...", "study_name": "...", ... },
  "metadata_version": { "oid": "...", "name": "...", ... },
  "standards": [ ... ],
  "datasets": [ ... ],
  "variables": [ ... ],
  "value_levels": [ ... ],
  "where_clauses": [ ... ],
  "codelists": [ ... ],
  "dictionaries": [ ... ],
  "methods": [ ... ],
  "comments": [ ... ],
  "documents": [ ... ]
}
```

### Validation

Validate intermediate JSON with schema, OID uniqueness, and cross-reference checks:

```bash
python gendefine.py --validate-json -j intermediate.json
```

The schema is defined in `mappings/intermediate_schema.json`.

## Supported Formats

### Original Format (odmlib-define-metadata.xlsx)

The same format used by `xlsx2define2-1`. Worksheets: Study, Standards, Datasets, Variables,
ValueLevel, WhereClauses, CodeLists, Dictionaries, Methods, Comments, Documents.

- OIDs are provided explicitly in the spreadsheet
- Where clauses are defined in a dedicated worksheet
- Codelists include full term definitions

### Standard-Spec Format

An alternative metadata format with different conventions:

- No explicit OIDs — generated from patterns (e.g., `IG.{Dataset}`, `IT.{Dataset}.{Variable}`)
- `Core` column instead of `Mandatory` (transformed via lookup: Req→Yes, Exp/Perm→No)
- `Key Variables` column in Datasets (comma-separated) instead of `KeySequence` in Variables
- Where clauses embedded as inline expressions (e.g., `TESTCD EQ SYSBP`)
- No CodeLists worksheet — codelist stubs generated from variable references
- No Dictionaries or Standards worksheets
- Informational columns (`Developer Notes`, `Variant`) excluded via `ignore_for_define`

## Extending gendefine

### Adding Support for a New Spreadsheet Format

Create a new JSON mapping file — no code changes needed for straightforward column renaming
and OID generation scenarios. See the Mapping Configuration Guide above.

### Adding New Value Transforms

Add a new entry to the `value_transforms` section of your mapping file. Supported types:
- `lookup` — Map values through a lookup table with optional default
- `type_coercion` — Convert to integer, float, or string
- `regex_parse` — Parse with a regex, return captured groups
- `custom` — Reference a handler function name

### Handling Missing Worksheets

When a spreadsheet format omits a worksheet (e.g., no CodeLists tab), gendefine:
- Produces empty arrays in the intermediate JSON
- Logs a warning noting which elements will be absent
- For codelists, can generate stubs from variable references (OID + Name, no terms)

## Dependencies

- odmlib >= 0.2.0
- openpyxl >= 3.0.9
- jsonschema >= 4.0.0
- Python 3.10+

## Running Tests

```bash
cd gendefine
python -m pytest tests/ -v
```

## Example Command-Line Invocations

```bash
# --- Original Format ---

# Basic: Excel to Define-XML
python gendefine.py -e data/odmlib-define-metadata.xlsx \
                    -m mappings/odmlib-format.json \
                    -d data/output-define.xml

# With validation and conformance checking
python gendefine.py -e data/odmlib-define-metadata.xlsx \
                    -m mappings/odmlib-format.json \
                    -d data/output-define.xml \
                    -v -c -s ../schema/cdisc-define-2.1/define2-1-0.xsd

# Extract to intermediate JSON for inspection
python gendefine.py -e data/odmlib-define-metadata.xlsx \
                    -m mappings/odmlib-format.json \
                    -j data/intermediate.json \
                    --extract-only

# Generate Define-XML from intermediate JSON
python gendefine.py --generate-only \
                    -j data/intermediate.json \
                    -d data/output-define.xml

# --- Standard-Spec Format ---

# Basic: Standard-Spec to Define-XML
python gendefine.py -e data/Standard-Spec.xlsx \
                    -m mappings/standard-spec.json \
                    -d data/standard-spec-define.xml

# --- Validation ---

# Validate a mapping file
python gendefine.py --validate-mapping -m mappings/odmlib-format.json

# Validate intermediate JSON
python gendefine.py --validate-json -j data/intermediate.json
```
