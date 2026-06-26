# snippets

Focused [odmlib](https://github.com/swhume/odmlib) **v0.2.0** snippets. Each file demonstrates one
feature or workflow rather than being a complete application. Most write their output to `data/`.

Run a snippet from this directory so its relative `data/` paths resolve, e.g.:

```bash
cd snippets
python context-managers.py
```

(Install dependencies from the repo-root `requirements.txt`, which pins `odmlib>=0.2.0rc1`.)

## Creating & building

| Snippet | Demonstrates |
|---------|--------------|
| `fluid_api.py` | The fluent `ODMBuilder` API for constructing ODM documents. |
| `odm132-odm-builder.py` | A full tour of `ODMBuilder` for ODM v1.3.2. |
| `odm20-odm-builder.py` | `ODMBuilder` for ODM v2.0 and how v2.0 differs structurally. |

## Reading, editing & context managers

| Snippet | Demonstrates |
|---------|--------------|
| `context-managers.py` | `open_odm` / `open_define` context managers (auto-write, in-place, JSON, error handling). |
| `modify-existing-document.py` | **(new)** Read → update / add / remove → write round-trip on a Define-XML document. |
| `element-reordering.py` | **(new)** Detect out-of-order children with `verify_order()` and fix them with `reorder_object()`. |

## Validation & error handling

| Snippet | Demonstrates |
|---------|--------------|
| `error-handling.py` | The structured exception hierarchy and collect-all-errors validation. |
| `permissive-mode.py` | `ValidationMode` / permissive loading for non-conformant documents. |
| `ref-def-checking.py` | OID reference/definition checking and unreferenced-OID detection. |
| `define-validator.py` | Validating a Define-XML template (with placeholders) and collecting schema errors. |

## Conversion & interchange

| Snippet | Demonstrates |
|---------|--------------|
| `dataset-json.py` | Reading/writing Dataset-JSON v1.1 with schema validation. |
| `define2dsj.py` | Define-XML v2.1 → Dataset-JSON v1.1. |
| `define2pandas.py` | Define-XML v2.1 ↔ pandas DataFrames. |
| `template-placeholders.py` | Discovering, categorizing, and replacing `__PLACEHOLDER__` values in a Define-XML template. |
| `template2dsj.py` | Converting a Define-XML template to Dataset-JSON. |

## Extensions

| Snippet | Demonstrates |
|---------|--------------|
| `arm-example.py` | The ARM (Analysis Results Metadata) v1.0 extension for ADaM Define-XML v2.1. |
| `custom-extension/` | **(new)** Building your own local extension model and loading it with `local_model=True`. |

> Narrow, vendor-specific, and deprecated snippets (Veeva, OSB, the v2.0 converters, early notebooks)
> have moved to the [odmlib_snippets](https://github.com/swhume/odmlib_snippets) repository.
