# library_xml

## Introduction

`library_xml` retrieves a standard from the [CDISC Library](https://library.cdisc.org) as **Library-XML**
(an ODM media type) and loads it into [odmlib](https://github.com/swhume/odmlib) for processing,
writing the result out as JSON.

Its main value as an example is that it shows how to use **external/local odmlib extension models**.
The two model packages bundled here —

- `library_odm_1_0/` — Library-XML based on ODM (e.g. CDASHIG)
- `library_define_1_0/` — Library-XML based on Define-XML (e.g. SDTMIG)

— are loaded with the odmlib v0.2.0 `local_model=True` loader option, so they make a good template
for implementing your own ODM extensions. (For a from-scratch walkthrough of building a local
extension model, see [`../snippets/custom-extension/`](../snippets/custom-extension/).)

## v0.2.0 features shown

- Loading documents against a **local extension model**: `XMLDefineLoader(model_package=...,
  local_model=True)` / `XMLODMLoader(model_package=..., local_model=True)`.
- Namespace declaration via `odmlib.ns_registry.NamespaceRegistry`.
- `create_document_from_string()` to parse XML retrieved over HTTP, and `to_json()` to serialize.

## Prerequisites

```bash
pip install -r requirements.txt
```

(installs `odmlib>=0.2.0` and `requests`)

You also need a **CDISC Library API key** — create an account at
[library.cdisc.org](https://library.cdisc.org) and use your own key in place of `YOUR_API_KEY` below.

## Run

Retrieve SDTMIG v3.4 (Define-XML flavor of Library-XML — note the `-d` flag):

```bash
cd library_xml
python library_xml.py -d -e "/mdr/sdtmig/3-4" -k YOUR_API_KEY
```

Retrieve CDASHIG v2.2 (ODM flavor) to a named output file:

```bash
python library_xml.py -e "/mdr/cdashig/2-2" -f library-odmlib-cdashig2-2.json -k YOUR_API_KEY
```

The `-d` flag selects the Define-XML model for Library-XML; omit it for the ODM model. The endpoint is
given by `-e`, and `-f` sets the output JSON filename (a default is used when omitted).

## Limitations

This is a demonstration program, not a production application. It exercises the metadata sections of
Library-XML and could be extended to address additional use cases. Using the CDISC Library API
requires your own account and credentials.
