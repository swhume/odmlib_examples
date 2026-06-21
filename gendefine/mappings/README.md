# Mapping Configuration Reference

This directory contains JSON mapping configurations for gendefine. Each mapping file defines how
a specific spreadsheet format maps to Define-XML v2.1 concepts.

## Included Mappings

| File | Format | OID Strategy | Description |
|---|---|---|---|
| `odmlib-format.json` | odmlib-define-metadata.xlsx | column | Original odmlib format with explicit OIDs |
| `standard-spec.json` | Standard-Spec.xlsx | pattern | Alternative format with generated OIDs |

## Mapping File Structure

```json
{
  "mapping_version": "1.0",
  "mapping_name": "my-format",
  "description": "Human-readable description of this mapping",
  "define_version": "2.1",
  "global_settings": { ... },
  "worksheets": { ... },
  "oid_patterns": { ... },
  "value_transforms": { ... },
  "defaults": { ... }
}
```

### Required Top-Level Fields

| Field | Type | Description |
|---|---|---|
| `mapping_version` | string | Version of the mapping format (currently "1.0") |
| `mapping_name` | string | Human-readable identifier for this mapping |
| `description` | string | Description of the spreadsheet format this mapping supports |
| `define_version` | string | Target Define-XML version (e.g., "2.1") |
| `global_settings` | object | Global settings applied across all worksheets |
| `worksheets` | object | Worksheet mappings keyed by worksheet name |

### Optional Top-Level Fields

| Field | Type | Description |
|---|---|---|
| `oid_patterns` | object | OID generation patterns keyed by element type |
| `value_transforms` | object | Transform definitions keyed by transform name |
| `defaults` | object | Default values keyed by attribute name |

## Global Settings

| Property | Type | Description |
|---|---|---|
| `language` | string | Default `xml:lang` value for TranslatedText (e.g., "en") |
| `default_purpose` | string | Default Purpose value for ItemGroupDef |
| `annotated_crf_leaf_id` | string | Leaf ID for AnnotatedCRF document reference |
| `oid_generation_strategy` | "pattern" or "column" | How OIDs are obtained |
| `where_clause_source` | string | "worksheet" (dedicated tab) or "inline" (parsed from text) |

## Worksheet Entry

Each key in `worksheets` is the worksheet name as it appears in the spreadsheet.

| Property | Required | Type | Description |
|---|---|---|---|
| `target` | Yes | string or array | Define-XML element(s) this worksheet produces |
| `format` | Yes | "attribute_value" or "tabular" | Worksheet layout type |
| `column_map` | Yes | object | Column-to-attribute mappings |
| `oid_pattern` | No | string | OID pattern for this worksheet's target element |

### Format Types

- **`attribute_value`**: Key-value pairs in two columns (e.g., Study worksheet). Column A has
  the attribute name, Column B has the value.
- **`tabular`**: Header row followed by data rows. Each column maps to a Define-XML attribute.

### Target Values

The `target` field identifies which Define-XML element(s) the worksheet contributes to:

- `"study_metadata"` — Study/MetaDataVersion metadata
- `"ItemGroupDef"` — Dataset definitions
- `["ItemDef", "ItemRef"]` — Variable definitions (produces both elements)
- `["ValueListDef", "ItemDef", "ItemRef"]` — Value-level definitions
- `"WhereClauseDef"` — Where clause definitions
- `"CodeList"` — Codelist definitions
- `"MethodDef"` — Method definitions
- `"CommentDef"` — Comment definitions
- `"leaf"` — Document references

## Column Map Entry

Each key in `column_map` is the spreadsheet column header name.

| Property | Required | Type | Description |
|---|---|---|---|
| `maps_to` | Yes* | string | Target attribute in the intermediate JSON |
| `also` | No | string or array | Additional attributes to populate with the same value |
| `oid_source` | No | "column" | Indicates this column provides explicit OID values |
| `oid_role` | No | "component" or "parent_lookup" | Role in OID generation |
| `optional` | No | boolean | Whether this column can contain empty/null values |
| `type` | No | "integer", "float", "string" | Type coercion target |
| `processing` | No | string | Name of a value_transform to apply |
| `ignore_for_define` | No | boolean | If true, column is read but excluded from Define-XML |

*`maps_to` is required unless `ignore_for_define` is true.

### Special `maps_to` Prefixes

- `_oid` — The column provides the element's OID
- `_vl_oid` — The column provides a ValueListDef OID
- `_item_oid` — The column provides the value-level ItemDef OID
- `_dataset` — The column identifies the parent dataset
- `_key_variables` — The column contains comma-separated key variable names
- `_where_clause_expr` — The column contains an inline where clause expression

### The `also` Property

When a single spreadsheet column should populate multiple Define-XML attributes, use `also`:

```json
"Dataset": { "maps_to": "Name", "also": ["Domain", "SASDatasetName"] }
```

This copies the Dataset column value to Name, Domain, and SASDatasetName.

## OID Patterns

OID patterns use `{placeholder}` syntax. Placeholders are replaced with values from the
current row. All generated OIDs are uppercased.

```json
{
  "oid_patterns": {
    "ItemGroupDef": "IG.{Dataset}",
    "ItemDef": "IT.{Dataset}.{Variable}",
    "ValueListDef": "VL.{Dataset}.{Variable}",
    "WhereClauseDef": "WC.{Dataset}.{Variable}.{Value}",
    "MethodDef": "MT.{Name}",
    "CommentDef": "COM.{index}",
    "CodeList": "CL.{Codelist}",
    "leaf": "LF.{Dataset}",
    "Standard": "STD.{index}"
  }
}
```

### Placeholder Reference

| Placeholder | Source |
|---|---|
| `{Dataset}` | Dataset name from the current row |
| `{Variable}` | Variable name from the current row |
| `{Name}` | Name field from the current row |
| `{Value}` | Value from a where clause condition |
| `{Codelist}` | Codelist name from a variable reference |
| `{index}` | Auto-incrementing counter |

## Value Transforms

### Lookup Transform

Map input values to output values through a lookup table:

```json
{
  "core_to_mandatory": {
    "type": "lookup",
    "map": { "Req": "Yes", "Exp": "No", "Perm": "No" },
    "default": "No"
  }
}
```

### Type Coercion Transform

Convert values to a target type:

```json
{
  "to_integer": {
    "type": "type_coercion",
    "target": "integer"
  }
}
```

Supported targets: `"integer"`, `"float"`, `"string"`.

### Regex Parse Transform

Parse a string value with a regex pattern, returning captured groups:

```json
{
  "parse_expression": {
    "type": "regex_parse",
    "pattern": "^(\\w+)\\s*(EQ|NE)\\s*(\\S+)$",
    "output_fields": ["Variable", "Comparator", "Value"]
  }
}
```

### Custom Transform

Reference a built-in handler function:

```json
{
  "parse_key_sequence": {
    "type": "custom",
    "handler": "key_variables_to_sequence"
  }
}
```

## Defaults

Default values for required Define-XML attributes that may not appear in the spreadsheet:

```json
{
  "defaults": {
    "Purpose": "Tabulation",
    "Repeating": "No",
    "IsReferenceData": "No",
    "Mandatory": "No",
    "Language": "en",
    "DefineVersion": "2.1.0"
  }
}
```

## JSON Schema

The mapping configuration schema is defined in `mapping_schema.json`. Validate your mapping with:

```bash
python gendefine.py --validate-mapping -m your-mapping.json
```

The intermediate JSON schema is defined in `intermediate_schema.json`. Validate with:

```bash
python gendefine.py --validate-json -j your-intermediate.json
```

## Annotated Examples

### odmlib-format.json

This mapping supports the original `odmlib-define-metadata.xlsx` format with explicit OIDs.

Key characteristics:
- `oid_generation_strategy: "column"` — OIDs read directly from the spreadsheet
- Each worksheet has an `OID` column mapped with `"oid_source": "column"`
- No `oid_patterns` section needed
- No value transforms needed (columns map directly to Define-XML attributes)
- The `also` property is used for `Dataset` → `Name` + `Domain` + `SASDatasetName`

### standard-spec.json

This mapping supports the Standard-Spec.xlsx alternative format.

Key characteristics:
- `oid_generation_strategy: "pattern"` — OIDs generated from templates
- `where_clause_source: "inline"` — Where clauses parsed from text expressions
- `core_to_mandatory` transform converts Core (Req/Exp/Perm) to Mandatory (Yes/No)
- `parse_key_sequence` custom transform converts Key Variables to KeySequence
- `ignore_for_define: true` on Developer Notes and Variant columns
- Codelist stubs auto-generated from variable references (no CodeLists worksheet)
- Single Standard generated from study metadata (no Standards worksheet)
- Defaults provide Purpose, Repeating, IsReferenceData, Mandatory values
