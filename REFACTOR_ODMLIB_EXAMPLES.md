# Refactoring Plan: odmlib_examples → focused v0.2.0 example repo

## 1. Context

The `odmlib_examples` repo has accreted material over several odmlib releases and no longer
reads as a clean set of examples:

- **v0.1-era examples** sit next to their **v0.2.0 replacements** (`snippets/` vs `v0-2-snippets/`,
  `notebooks/` vs `v0-2-notebooks/`), so it is unclear which are canonical.
- **Deprecated Define-XML v2.0 apps** (`xls2define/`, `define2xls/`) remain in the tree.
- **Narrow, one-off snippets** created for specific requests (Veeva and OSB) are mixed in with
  broadly useful examples.
- **Two applications have outgrown the examples repo** and now live in their own repositories:
  `gendefine/` and `extended-define2xlsx/`.

**Goal:** leave `odmlib_examples` as a curated set of current, runnable **odmlib v0.2.0** examples and
tutorials. Relocate narrow/deprecated material to a **new `odmlib_snippets` repo**, which doubles as a
test corpus and as reference material for generative AI. No example should require an odmlib version
older than `0.2.0`.

> This document is a plan. It **recommends** dispositions. Deletions of old `snippets/` and
> `notebooks/` content happen only after the maintainer reviews each file (see §4).

---

## 2. Target structure (after refactor)

```
odmlib_examples/
  README.md            # NEW: catalog/index of examples + links to sibling repos
  CLAUDE.md            # updated
  schema/              # keep (reference XSDs)
  get_started/         # refactor → v0.2.0
  xlsx2define2-1/       # keep (canonical Excel → Define-XML v2.1)
  define2-1-to-xlsx/   # keep (canonical Define-XML v2.1 → Excel)
  library_xml/         # refactor → v0.2.0 (CDISC Library integration)
  ct2json/             # refactor (add README + requirements.txt)
  ct2odm/              # refactor (add README + requirements.txt)
  merge_odm/           # refactor → v0.2.0
  snippets/            # renamed from v0-2-snippets (minus narrow one-offs) + new examples
  notebooks/           # renamed from v0-2-notebooks
```

Removed from the repo: `gendefine/`, `extended-define2xlsx/`, `xls2define/`, `define2xls/`,
the old `snippets/`, and the old `notebooks/`.

---

## 3. Disposition of every top-level directory

| Directory | Target odmlib | Action                                                                 |
|-----------|---------------|------------------------------------------------------------------------|
| `xlsx2define2-1/` | 0.2.0 ✓ | **Keep** — exemplar; no change                                         |
| `define2-1-to-xlsx/` | 0.2.0 ✓ | **Keep** — exemplar; no change                                         |
| `v0-2-snippets/` | 0.2.0 ✓ | **Keep → rename `snippets/`**; move `arm-example.py` out (see §5)      |
| `v0-2-notebooks/` | 0.2.0 ✓ | **Keep → rename `notebooks/`**                                         |
| `schema/` | n/a | **Keep** (reference XSDs)                                              |
| `get_started/` | 0.1.4 → 0.2.0 | **Refactor** (loaders, structured exceptions, OID check); modernize README |
| `library_xml/` | 0.1.4 → 0.2.0 | **Refactor**; keep its local extension models; modernize README        |
| `merge_odm/` | 0.1.4 → 0.2.0 | **Refactor**; verify `.find()`; add exception handling                 |
| `ct2json/` | old | **Refactor** — add `requirements.txt` + README; verify `write_json()` on v0.2.0 |
| `ct2odm/` | old | **Refactor** — add `requirements.txt` + README                         |
| `gendefine/` | 0.2.0 | **Remove** (own repo); add pointer link in root README                 |
| `extended-define2xlsx/` | 0.2.0 | **Remove** (own repo); `git reset` the staged add first, then drop; add pointer link |
| `xls2define/` | v2.0 (deprecated) | **Remove** Since we have more modern equivalents in the xlsx2define2-1 |
| `define2xls/` | v2.0 (deprecated) | **Remove** Since we have more modern equivalents in define2-1-to-xlsx  |
| `snippets/` (old) | 0.1.x | **Split** — see review table in §4                                     |
| `notebooks/` (old) | 0.1.x | **Review / delete** — superseded by `v0-2-notebooks`; salvage anything unique |

---

## 4. Review table — old `snippets/` (maintainer reviews before deletion)

| File | Recommendation | Rationale |
|------|----------------|-----------|
| `simple_create_odm.py` | Delete (superseded) | Covered by `odm132-odm-builder.py` / `fluid_api.py`. Keep only if a plain, non-builder construction example is wanted. |
| `odmlib_first_define.py` | Move → `odmlib_snippets` | PHUSE US Connect 2022 historical artifact; superseded by current Define-XML examples. |
| `github_issue_import.py` | Delete (superseded) | Minimal load; covered by `context-managers.py`. |
| `validate_odm.py` | **Salvage** | Contains ODM element re-ordering — fold into new `element-reordering.py` (§6). |
| `validate_define.py` | Delete / merge | Overlaps `define-validator.py` and `ref-def-checking.py`. |
| `convert_veeva_odm.py`, `veeva_write_odm.py`, `osb_odm.py` | Move → `odmlib_snippets` | Narrow vendor one-offs. |
| `veeva_1_0/`, `veeva_odm_1_0/`, `osb_odm_1_0/` | Move → `odmlib_snippets` | Vendor extension models supporting the above. |

For old `notebooks/` (`first_odm.ipynb`, `first_define.ipynb`, `generate_define.ipynb`): superseded by
`v0-2-notebooks/`. Delete after confirming each topic is covered by a v0.2 notebook; salvage any unique
content into the renamed `notebooks/`.

---

## 5. New `odmlib_snippets` repo — initial contents

Catch-all for **narrow one-offs** material:

- **From old `snippets/`:** Veeva (`convert_veeva_odm.py`, `veeva_write_odm.py`, `veeva_1_0/`,
  `veeva_odm_1_0/`), OSB (`osb_odm.py`, `osb_odm_1_0/`), and `odmlib_first_define.py`.
- **Deprecated v2.0 apps:** `xls2define/`, `define2xls/`.

The repo's README should explain its dual purpose (test corpus + generative-AI reference + random snippet repository) and give a
one-line description per snippet.

---

## 6. New examples to create (in the renamed `snippets/`)

- **`element-reordering.py`** *(explicitly requested)* — load a document whose children are out of
  schema sequence, catch `OdmlibElementOrderError`, reorder to the correct sequence, and re-validate.
  Seed from the reorder logic in the old `validate_odm.py`.
- **`modify-existing-document.py`** — read → mutate (add / remove / update an `ItemDef` or
  `ItemGroupDef`) → write round-trip. A common real-world task not clearly demonstrated today.
- **`custom-extension/`** — a focused tutorial on building a local extension model package and loading
  it with `local_model=True` and a custom namespace. This fills the gap left when
  `extended-define2xlsx`, Veeva, and OSB leave the repo, so `odmlib_examples` still shows how to extend
  odmlib.
- **From `v0-2-snippets/`:** `arm-example.py` plus its ARM data/schema: Keep and refine this example as it's the only ARM example
- Update the renamed `snippets/README.md` to index existing files plus these new ones.

---

## 7. Documentation updates

- **Root `README.md` (new/refreshed):** a catalog grouping examples by purpose —
  *Getting started · Excel ↔ Define-XML v2.1 · Conversions · Integration · Snippets · Notebooks* —
  with links out to `odmlib_snippets`.
- **`CLAUDE.md`:** update the directory-structure section, remove the deprecated
  `xls2define`/`define2xls` references, fix Key Commands paths after the renames, and state odmlib
  `0.2.0` as the baseline version.

---

## 8. Refactor pattern for v0.1 → v0.2 directories

Apply consistently across `get_started/`, `merge_odm/`, `library_xml/`, `ct2json/`, `ct2odm/`,
mirroring the current exemplar `xlsx2define2-1/`:

- Pin `requirements.txt` to `odmlib>=0.2.0`.
- Use the modern loader API (`ODMLoader` with `XMLDefineLoader` / `XMLODMLoader`).
- Replace bare error handling with the structured exception hierarchy: `OdmlibValidationError`,
  `OdmlibOIDError`, `OdmlibConformanceError`, `OdmlibElementOrderError`.
- Use `create_oid_checker` for OID reference/definition validation where relevant.
- Add or refresh the README: prerequisites, install, run command, and which v0.2.0 features it shows.

---

## 9. Execution order

1. Write this `REFACTOR_ODMLIB_EXAMPLES.md` (done — this file).
2. Remove the moved-out apps (`gendefine/`, `extended-define2xlsx/`) and add README pointers.
3. Relocate narrow one-offs + deprecated material to `odmlib_snippets`.
4. Delete superseded old material (after maintainer review per §4).
5. Rename `v0-2-snippets/ → snippets/` and `v0-2-notebooks/ → notebooks/`.
6. Refactor the v0.1 directories per §8.
7. Add the new examples per §6.
8. Update root `README.md` and `CLAUDE.md`.

---

## 10. Verification

- Create a REFACTOR_TESTING_GUIDE.md that includes test code to run for the more involved examples.
- Each refactored or new example runs end-to-end with its documented command on odmlib v0.2.0
  (e.g. `python get_started/get_started.py …`, `python snippets/element-reordering.py`).
- The v0.2 notebooks execute top-to-bottom after the rename.
- No directory remaining in `odmlib_examples` imports the `odmlib.define_2_0` model.
- All README links resolve, and `CLAUDE.md` command paths match the post-rename layout.
- `git status` reflects the intended removals/renames; the standalone-repo apps are no longer tracked
  here.
