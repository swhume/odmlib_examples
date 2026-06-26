"""Template-Placeholder Iterator for Define-XML templates (odmlib v0.2).

`data/define-360i.xml` is a near-complete Define-XML 2.1 document with many
occurrences of `__PLACEHOLDER__` scattered across attributes making this a 2nd
level template. Besides the `__PLACEHOLDER__`, this is a valid Define-XML file.
(ItemDef.Length, Origin.Type/Source, PDFPageRef.PageRefs, CodeListItem.CodedValue)
and TranslatedText text content (CodeListItem decodes, one MethodDef description).

This snippet loads the template permissively, walks the parsed object tree, and
yields a `Placeholder` dataclass for every `__PLACEHOLDER__` hit. Each Placeholder
carries the parent odmlib object, the attribute (or `_content`) holding the sentinel,
a category key, a human-readable path-like locator, and a category-specific
`context` dict the caller can use to decide a replacement. A `.replace()` method
writes the new value back into the live object tree.

Run from the v0-2-snippets directory:
    python template-placeholders.py
"""
from dataclasses import dataclass
from typing import Any, Iterator, Optional

import odmlib.loader as LD
import odmlib.define_loader as DL
from odmlib import permissive

PLACEHOLDER = "__PLACEHOLDER__"
INPUT_FILE = "data/define-360i.xml"
OUTPUT_FILE = "data/define-360i-completed.xml"
MODEL_PACKAGE = "define_2_1"
NS_URI = "http://www.cdisc.org/ns/def/v2.1"


@dataclass
class Placeholder:
    """One __PLACEHOLDER__ occurrence with enough context to replace it.

    `element` is the parent odmlib object that owns the placeholder. `attribute` is
    the attribute name on that object — e.g. "Length", "Type", "Source",
    "PageRefs", "CodedValue", or "_content" when the placeholder sits inside a
    TranslatedText text node. Call `replace(value)` to set the replacement
    on the live object tree."""
    element: Any
    attribute: str
    category: str
    path: str
    context: dict
    original: str = PLACEHOLDER

    def replace(self, new_value: Any) -> None:
        if self.attribute == "_content":
            # Substring replace preserves any text surrounding the sentinel
            # (needed for the MethodDef description case).
            current = self.element._content or ""
            self.element._content = current.replace(self.original, str(new_value), 1)
        else:
            setattr(self.element, self.attribute, new_value)


def _is_odm_element(obj) -> bool:
    return type(obj).__module__.startswith("odmlib")


def _qualifier(elem) -> str:
    for key in ("OID", "ID", "Name"):
        val = getattr(elem, key, None)
        if val:
            return f"[{val}]"
    return ""


def _classify(elem, attribute: str, ancestor_names: set) -> Optional[str]:
    cls = type(elem).__name__
    if cls == "ItemDef" and attribute == "Length":
        return "ItemDef.Length"
    if cls == "Origin" and attribute in ("Type", "Source"):
        return f"Origin.{attribute}"
    if cls == "PDFPageRef" and attribute == "PageRefs":
        return "PDFPageRef.PageRefs"
    if cls == "CodeListItem" and attribute == "CodedValue":
        return "CodeListItem.CodedValue"
    if cls == "TranslatedText" and attribute == "_content":
        if "Decode" in ancestor_names:
            return "CodeListItem.Decode.TranslatedText"
        if "MethodDef" in ancestor_names:
            return "MethodDef.Description.TranslatedText"
    return None


def _build_context(category: str, elem, scope: dict) -> dict:
    if category == "ItemDef.Length":
        return {
            "item_oid": scope.get("item_oid"),
            "item_name": scope.get("item_name"),
            "item_data_type": scope.get("item_data_type"),
            "item_group_oid": scope.get("item_group_oid"),
            "item_group_name": scope.get("item_group_name"),
            "description": scope.get("item_description"),
        }
    if category in ("Origin.Type", "Origin.Source"):
        return {
            "item_oid": scope.get("item_oid"),
            "item_name": scope.get("item_name"),
            "item_group_oid": scope.get("item_group_oid"),
            "item_group_name": scope.get("item_group_name"),
            "sibling_type": getattr(elem, "Type", None),
            "sibling_source": getattr(elem, "Source", None),
        }
    if category == "PDFPageRef.PageRefs":
        return {
            "item_oid": scope.get("item_oid"),
            "item_name": scope.get("item_name"),
            "item_group_oid": scope.get("item_group_oid"),
            "leaf_id": scope.get("leaf_id"),
            "pageref_type": getattr(elem, "Type", None),
        }
    if category == "CodeListItem.CodedValue":
        return {
            "codelist_oid": scope.get("codelist_oid"),
            "codelist_name": scope.get("codelist_name"),
            "codelist_data_type": scope.get("codelist_data_type"),
            "standard_oid": scope.get("codelist_standard_oid"),
        }
    if category == "CodeListItem.Decode.TranslatedText":
        return {
            "codelist_oid": scope.get("codelist_oid"),
            "codelist_name": scope.get("codelist_name"),
            "coded_value": scope.get("codelist_item_coded_value"),
        }
    if category == "MethodDef.Description.TranslatedText":
        surrounding = (elem._content or "").replace(PLACEHOLDER, "").strip()
        return {
            "method_oid": scope.get("method_oid"),
            "method_name": scope.get("method_name"),
            "method_type": scope.get("method_type"),
            "surrounding_text": surrounding,
        }
    return {}


def _scope_for(elem, scope: dict) -> dict:
    new = dict(scope)
    cls = type(elem).__name__
    if cls == "ItemGroupDef":
        new["item_group_oid"] = getattr(elem, "OID", None)
        new["item_group_name"] = getattr(elem, "Name", None)
    elif cls == "ItemDef":
        new["item_oid"] = getattr(elem, "OID", None)
        new["item_name"] = getattr(elem, "Name", None)
        new["item_data_type"] = getattr(elem, "DataType", None)
        desc = getattr(elem, "Description", None)
        if desc is not None:
            tts = getattr(desc, "TranslatedText", None) or []
            if tts:
                new["item_description"] = getattr(tts[0], "_content", None)
    elif cls == "CodeList":
        new["codelist_oid"] = getattr(elem, "OID", None)
        new["codelist_name"] = getattr(elem, "Name", None)
        new["codelist_data_type"] = getattr(elem, "DataType", None)
        new["codelist_standard_oid"] = getattr(elem, "StandardOID", None)
    elif cls == "CodeListItem":
        new["codelist_item_coded_value"] = getattr(elem, "CodedValue", None)
    elif cls == "MethodDef":
        new["method_oid"] = getattr(elem, "OID", None)
        new["method_name"] = getattr(elem, "Name", None)
        new["method_type"] = getattr(elem, "Type", None)
    elif cls == "DocumentRef":
        new["leaf_id"] = getattr(elem, "leafID", None)
    return new


def _walk(node, path_parts, scope, ancestor_names, visited):
    if not _is_odm_element(node):
        return
    node_id = id(node)
    if node_id in visited:
        return
    visited.add(node_id)

    cls = type(node).__name__
    here_path = path_parts + [f"{cls}{_qualifier(node)}"]
    here_scope = _scope_for(node, scope)
    here_ancestors = ancestor_names | {cls}

    for attr_name, value in list(node.__dict__.items()):
        if isinstance(value, str) and PLACEHOLDER in value:
            category = (_classify(node, attr_name, ancestor_names)
                        or f"Unclassified[{cls}.{attr_name}]")
            if attr_name == "_content":
                path = "/".join(here_path) + "/text()"
            else:
                path = "/".join(here_path) + f"/@{attr_name}"
            yield Placeholder(
                element=node,
                attribute=attr_name,
                category=category,
                path=path,
                context=_build_context(category, node, here_scope),
            )
        elif _is_odm_element(value):
            yield from _walk(value, here_path, here_scope, here_ancestors, visited)
        elif isinstance(value, list):
            for item in value:
                if _is_odm_element(item):
                    yield from _walk(item, here_path, here_scope, here_ancestors, visited)


def iter_placeholders(odm) -> Iterator[Placeholder]:
    """Yield every __PLACEHOLDER__ in the document, in declaration order."""
    yield from _walk(odm, [], {}, set(), set())


def load_permissive(path):
    loader = LD.ODMLoader(DL.XMLDefineLoader(
        model_package=MODEL_PACKAGE, ns_uri=NS_URI,
    ))
    with permissive():
        loader.open_odm_document(path)
        return loader.root()


# A demo rule-book with hard-coded replacement values. A real caller would consult read actual study-level
# metadata from some source(s) to use as replacement values.
def replacement_for(p: Placeholder):
    cat, ctx = p.category, p.context
    if cat == "ItemDef.Length":
        overrides = {"USUBJID": 40, "STUDYID": 20, "DOMAIN": 8}
        if ctx.get("item_name") in overrides:
            return overrides[ctx["item_name"]]
        return 8 if ctx.get("item_data_type") == "integer" else 200
    if cat == "Origin.Type":
        return "Assigned"
    if cat == "Origin.Source":
        return "Sponsor"
    if cat == "PDFPageRef.PageRefs":
        return "1"
    if cat == "CodeListItem.CodedValue":
        return "PLACEHOLDER_TERM"  # TODO: look up by ctx["codelist_oid"]
    if cat == "CodeListItem.Decode.TranslatedText":
        return "Placeholder term"  # TODO: look up by ctx["codelist_oid"]
    if cat == "MethodDef.Description.TranslatedText":
        return "Algorithm"
    return None


def summarize(placeholders):
    counts = {}
    for p in placeholders:
        counts[p.category] = counts.get(p.category, 0) + 1
    print(f"\nFound {sum(counts.values())} placeholders:")
    for cat, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {n:4d}  {cat}")


def main():
    print("1. Loading the Define-XML template permissively")
    odm = load_permissive(INPUT_FILE)
    print(f"   FileOID:   {odm.FileOID}")
    print(f"   Study OID: {odm.Study.OID}")

    print("\n2. Discovering placeholders")
    discovered = list(iter_placeholders(odm))
    summarize(discovered)

    print("\n3. Sample context for the first placeholder in each category")
    seen = set()
    for p in discovered:
        if p.category in seen:
            continue
        seen.add(p.category)
        print(f"\n   path:     {p.path}")
        print(f"   category: {p.category}")
        for k, v in p.context.items():
            print(f"     {k}: {v!r}")

    print("\n4. Applying the rule-book")
    replaced = skipped = 0
    for p in discovered:
        new_value = replacement_for(p)
        if new_value is None:
            skipped += 1
            continue
        p.replace(new_value)
        replaced += 1
    print(f"   Replaced {replaced}; skipped (no rule) {skipped}")

    print(f"\n5. Writing completed Define-XML -> {OUTPUT_FILE}")
    odm.write_xml(OUTPUT_FILE)

    print("\n6. Re-loading the completed file in strict mode")
    try:
        strict_loader = LD.ODMLoader(DL.XMLDefineLoader(
            model_package=MODEL_PACKAGE, ns_uri=NS_URI,
        ))
        strict_loader.open_odm_document(OUTPUT_FILE)
        strict_loader.root()
        print("   Strict-mode load: SUCCESS")
    except Exception as e:
        print(f"   Strict-mode load FAILED: {type(e).__name__}: {e}")

    with open(OUTPUT_FILE) as f:
        remaining = f.read().count(PLACEHOLDER)
    print(f"\n   '{PLACEHOLDER}' occurrences remaining in output: {remaining}")


if __name__ == "__main__":
    main()
