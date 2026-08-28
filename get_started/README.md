# get_started

The **start here** odmlib example. It demonstrates the two most common things you do with
[odmlib](https://github.com/swhume/odmlib) v0.2.1:

1. **Create** an ODM v1.3.2 document from scratch (`ODMCreator`) — build the Study, MetaDataVersion,
   Protocol, StudyEventDef, FormDef, ItemGroupDef, ItemDef, CodeList, and MethodDef with the fluent
   `ODMBuilder`, validate the object tree, write it to XML, and serialize a single element to an
   XML string and to JSON.
2. **Read and process** an ODM document (`ODMProcessor`) — XML-schema validate it, load it
   read-only with `open_odm()`, validate the loaded document, and list the metadata.

## v0.2.1 patterns shown

- `ODMBuilder("odm_1_3_2")` — chainable `set_file / add_study / add_metadata_version / add_*_def /
  add_*_ref / with_description / with_question / with_codelist_ref / with_alias / add_code_list /
  add_method_def`, plus the `attach(parent, element)` escape hatch (used here for a Protocol with a
  Description) reached via `builder.current["mdv"]`.
- `odm.validate(collect_errors=True, oid_checker=create_oid_checker("odm_1_3_2"),
  conformance_checker=MetadataSchema())` — one pass that reports **every** element-order, OID
  ref/def, and conformance problem (a fresh OID checker per call).
- `ODMSchemaValidator(standard="odm", version="1.3.2").xsd.iter_errors(file)` — XSD validation
  against the **bundled** ODM 1.3.2 schema, so no local XSD path is required.
- `open_odm(file, model_package="odm_1_3_2")` — the context-manager facade; read-only by default
  (pass `output_file=` or `write_on_exit=True` to write).
- `element.to_xml_string()` / `element.to_element()` / `element.to_json()` — serializing one
  element. `to_xml_string()` declares the ODM namespace itself; never use
  `ET.tostring(obj.to_xml())`, which emits no `xmlns`.
- `mdv.find("ItemDef", "OID", ...)` — locate an element by OID without looping.

## Prerequisites

```bash
pip install -r requirements.txt
```

(installs `odmlib>=0.2.0rc1` and `xmlschema`; the serialization helpers need odmlib 0.2.1+)

## Run

```bash
cd get_started
python get_started.py
```

This writes `./data/odm_demo.xml`, then reads it back and prints the metadata. No command-line
arguments are required.
