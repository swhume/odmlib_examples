# odmlib examples

A set of runnable examples for the [odmlib](https://github.com/swhume/odmlib) Python package, an object-oriented interface for creating 
and processing CDISC ODM documents and their extensions, notably **Define-XML v2.1**.

All examples target **odmlib v0.2.0**. Each example directory has its own `README.md` and
`requirements.txt`; the repo-root `requirements.txt` aggregates every dependency so the whole repo
can be set up from one virtual environment.

## odmlib version

Examples pin `odmlib>=0.2.0rc1`. Today, that specifier installs the `0.2.0` release from PyPI and will automatically 
prefer updated versions once they're published. Install per example, or everything at once from the root:

```bash
pip install -r requirements.txt
```

## Catalog

### Getting started
| Example | What it does |
|---------|--------------|
| [`get_started/`](get_started/) | **Start here.** Create an ODM v1.3.2 document, then read it back: schema-validate, load, OID-check, and list metadata. |

### Excel ↔ Define-XML v2.1
| Example | What it does |
|---------|--------------|
| [`xlsx2define2-1/`](xlsx2define2-1/) | Generate Define-XML v2.1 from an Excel metadata workbook. Canonical v0.2.0 example (structured exceptions, dynamic OID checker, collect-all-errors validation). |
| [`define2-1-to-xlsx/`](define2-1-to-xlsx/) | The reverse: extract Define-XML v2.1 metadata into Excel/CSV. |

### Conversions
| Example | What it does |
|---------|--------------|
| [`ct2json/`](ct2json/) | Convert CDISC Controlled Terminology from CT-XML to JSON (with optional schema validation). |
| [`ct2odm/`](ct2odm/) | Build CT-XML ODM from a CDISC CT tab-delimited export. |
| [`merge_odm/`](merge_odm/) | Merge a form (and its dependent metadata) from one ODM file into another. |

### Integration
| Example | What it does |
|---------|--------------|
| [`library_xml/`](library_xml/) | Retrieve a standard from the CDISC Library API as Library-XML and load it with **local extension models**. |

### Snippets & notebooks
| Location | What it is |
|----------|------------|
| [`snippets/`](snippets/) | Focused, single-feature scripts: builders, context managers, validation, element re-ordering, modifying documents, conversions, ARM, and a custom-extension tutorial. |
| [`notebooks/`](notebooks/) | Jupyter notebooks for v0.2 features. |
| [`schema/`](schema/) | Reference XSDs (ODM 1.3.2, Define-XML 2.1, ARM 1.0). |

## Related repositories

Some programs that used to live here now have their own repositories:

- **gendefine** — generalized Excel → Define-XML v2.1 with JSON mapping configs:
  [github.com/swhume/gendefine](https://github.com/swhume/gendefine)
- **[odmlib_snippets](https://github.com/swhume/odmlib_snippets)** — narrow/vendor-specific snippets
  (Veeva, OSB), and early notebooks. Also useful as a test
  corpus and as reference material for generative AI.

## Limitations

These are demonstration programs, not production-ready applications. If an example doesn't run,
update to the latest odmlib and open an issue on GitHub.
