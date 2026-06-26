# ct2json

Convert a CDISC **Controlled Terminology** file expressed as CT-XML (an ODM media type) into JSON,
with optional XML-schema validation, using [odmlib](https://github.com/swhume/odmlib) v0.2.0.

The program loads the CT-XML with the `ct_1_1_1` model package and writes it back out as JSON via
`write_json()`.

## v0.2.0 features shown

- Loading an ODM media type with a non-default model package:
  `XMLODMLoader(model_package="ct_1_1_1", ns_uri="http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC")`.
- Object → JSON serialization with `write_json()`.
- Schema validation via `ODMSchemaValidator(xsd_file=...)`, catching the structured
  `OdmlibSchemaValidationError`.

## Prerequisites

```bash
pip install -r requirements.txt
```

(installs `odmlib>=0.2.0` and `xmlschema`)

## Run

Basic conversion:

```bash
cd ct2json
python ct2json.py -x ./data/sdtm-ct.xml -j ./data/sdtm-ct.json
```

With schema validation (uses the bundled `schema/controlledterminology1-1-1.xsd` by default):

```bash
python ct2json.py -v -x ./data/sdtm-ct.xml -j ./data/sdtm-ct.json
```

Override the schema path with `-s`, and set the language with `-l` (default `en`).

| Flag | Meaning |
|------|---------|
| `-x` / `--ct` | CT-XML input file (required) |
| `-j` / `--json` | JSON output file (default `./`) |
| `-s` / `--schema` | CT-XML XSD path (default `./schema/controlledterminology1-1-1.xsd`) |
| `-v` / `--validate` | schema-validate the CT-XML before converting |
| `-l` / `--lang` | language code (default `en`) |

> The sample `data/sdtm-ct.xml` is large (~18 MB); conversion of the full file may take a moment.
