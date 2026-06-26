# custom-extension

A focused tutorial on building your own **local odmlib extension model** and loading documents with
it using the `local_model=True` loader option and a custom namespace.

This fills the role that the vendor examples (Veeva, OSB) and `extended-define2xlsx` used to play in
this repo — those now live in their own repositories — by showing the extension *pattern* in the
smallest form that still runs.

## What's here

```
custom-extension/
  acme_odm_1_0/
    __init__.py
    model.py          # the local extension model (adds acme:Label to ItemDef)
  data/
    acme-odm.xml      # a small ODM doc that uses the acme namespace
  custom_extension.py # loads the doc with the local model, edits, and round-trips
```

## The two rules for a local model

`acme_odm_1_0/model.py` demonstrates both:

1. **Register every custom namespace at import time** with
   `odmlib.ns_registry.NamespaceRegistry(prefix=..., uri=...)`.
2. **Re-declare the slice of the tree you use.** The loader instantiates each element by class
   name and only recurses into the child descriptors found in that class's *own* `__dict__`. So
   every element in your documents needs a class in the model, and each class must re-declare (by
   referencing the base class, e.g. `ItemDef = ODM.MetaDataVersion.ItemDef`) the children and
   attributes it should carry. New extension attributes are added with
   `T.<type>(namespace="<prefix>")` — here `Label = T.String(namespace="acme")`.

This example covers only the elements used by `data/acme-odm.xml`. A production extension would
re-declare the full ODM tree (the vendor models in the `odmlib_snippets` repo are complete examples).

## v0.2.0 features shown

- `XMLODMLoader(model_package="acme_odm_1_0", ns_uri=..., local_model=True)` — load against a local
  model package resolved from the working directory.
- Reading and writing a custom-namespace attribute (`acme:Label`).
- A read → edit → write → reload round-trip that preserves the extension.

## Run

```bash
cd snippets/custom-extension
python custom_extension.py
```

`local_model=True` imports `acme_odm_1_0` from the current directory, so run the script from this
folder (or otherwise ensure this folder is on `PYTHONPATH`).
