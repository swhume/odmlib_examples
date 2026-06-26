# get_started

The **start here** odmlib example. It demonstrates the two most common things you do with
[odmlib](https://github.com/swhume/odmlib) v0.2.0:

1. **Create** an ODM v1.3.2 document from scratch (`ODMCreator`) — build the Study, MetaDataVersion,
   Protocol, StudyEventDef, FormDef, ItemGroupDef, ItemDef, CodeList, and MethodDef objects, then
   serialize to XML and JSON.
2. **Read and process** an ODM document (`ODMProcessor`) — XML-schema validate it, load it with the
   `ODMLoader`, run an OID reference/definition check, and list the metadata.

## v0.2.0 features shown

- `odmlib.odm_parser.ODMSchemaValidator(standard="odm", version="1.3.2")` — resolves the **bundled**
  ODM 1.3.2 schema, so no local XSD path is required.
- `create_oid_checker("odm_1_3_2")` + `MetaDataVersion.verify_oids(...)` — model-aware OID checking.
- The structured exception hierarchy (`OdmlibOIDError`).

## Prerequisites

```bash
pip install -r requirements.txt
```

(installs `odmlib>=0.2.0rc1` and `xmlschema`)

## Run

```bash
cd get_started
python get_started.py
```

This writes `./data/odm_demo.xml`, then reads it back and prints the metadata. No command-line
arguments are required.
