"""
A self-testing proof that odmlib's XML *string* serialization is correct.

`to_xml_string()` is the only serialization path that has to carry its own namespace
declarations: `write_xml()` hands the tree to `ODMWriter`, which declares them on the way
out, while a string is often passed to an API, a message queue, or a schema validator with
no file and no writer involved. This snippet proves that a string produced by odmlib stands
on its own, for ODM v1.3.2 *and* Define-XML v2.1:

  1. re-loadable   - the string alone loads back into an equivalent odmlib document, and
                     re-serializing that document reproduces the same string (a fixed point)
  2. schema valid  - the string alone validates against the official CDISC XSD (bundled with
                     odmlib), declaring exactly the namespaces it uses - no more, no less
  3. file-faithful - it agrees with what `write_xml()` puts in a file, byte for byte and as
                     canonical XML. The default string is the file minus its XML declaration;
                     `to_xml_string(xml_declaration=True)` reproduces the file exactly.

Each document is serialized *after* every other document has been loaded, so the checks also
prove that odmlib's per-document namespace snapshots keep a loaded ODM document from picking
up the `def:` namespace registered by a Define-XML load.

Properties 1-3 are proved for document roots; the last section then proves the same namespace
guarantee holds for elements reached by walking the tree, and shows the one case that is still
the caller's responsibility - an element constructed after the load.

Closing checks pin the flip side: `to_xml()` returns an ElementTree *buffer* with no
declarations, so `ET.tostring(obj.to_xml())` is not a substitute for `to_xml_string()` -
loudly on Define-XML, and *silently*, with data loss, on ODM.

This snippet is a test, not a demo: it prints one line per check, and on any failure it
lists every failed check and exits non-zero.

    cd snippets && python string-serialization.py; echo "exit=$?"

Writes data/string-serialization-odm.xml and data/string-serialization-define.xml (both
gitignored) so the serialized output can also be checked from an independent process:

    python -c "
    from odmlib.odm_parser import ODMSchemaValidator
    for f, std, ver in [('data/string-serialization-odm.xml', 'odm', '1.3.2'),
                        ('data/string-serialization-define.xml', 'define', '2.1')]:
        errs = list(ODMSchemaValidator(standard=std, version=ver).xsd.iter_errors(f))
        print(f, len(errs), 'errors'); assert not errs"
"""
import datetime
import inspect
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

import odmlib.define_2_1.model as DEFINE
import odmlib.define_loader as DL
import odmlib.loader as LD
import odmlib.ns_registry as NS
import odmlib.odm_loader as OL
from odmlib.builder import ODMBuilder
from odmlib.odm_parser import ODMSchemaValidator

ODM_NS = "http://www.cdisc.org/ns/odm/v1.3"
DEFINE_NS = "http://www.cdisc.org/ns/def/v2.1"
DEFINE_20_NS = "http://www.cdisc.org/ns/def/v2.0"
XLINK_NS = "http://www.w3.org/1999/xlink"

# what ElementTree.write(xml_declaration=True, encoding='UTF-8') emits, and therefore the
# only difference between a write_xml() file and a to_xml_string() string today
XML_DECLARATION = b"<?xml version='1.0' encoding='UTF-8'?>\n"

ODM_FILE = os.path.join("data", "cdash-odm-test.xml")
DEFINE_FILE = os.path.join("data", "defineV21-SDTM.xml")

# written so the serialized output can be schema-checked from an independent process
ODM_OUT = os.path.join("data", "string-serialization-odm.xml")
DEFINE_OUT = os.path.join("data", "string-serialization-define.xml")

failures = []
current_case = ""       # prefixes failures in the summary, since labels repeat across cases


def check(label, passed, detail=""):
    """Record and report one assertion. Never raises - every check gets to run."""
    print(f"  [{'PASS' if passed else 'FAIL'}] {label}")
    if not passed:
        failures.append(f"{current_case}: {label}" if current_case else label)
        if detail:
            print(f"         {detail}")
    return passed


def used_namespaces(root):
    """Return every namespace URI the parsed tree actually resolves, tags and attributes.

    A prefix that was used but never declared cannot show up here - the parse would have
    failed first - so this doubles as a namespace-completeness check.
    """
    uris = set()
    for elem in root.iter():
        if elem.tag.startswith("{"):
            uris.add(elem.tag[1:].split("}", 1)[0])
        for name in elem.attrib:
            if name.startswith("{"):
                uris.add(name[1:].split("}", 1)[0])
    return uris


def declared_namespaces(xml_string):
    """Return {prefix: uri} for the xmlns declarations literally present in the root start tag.

    This reads the raw text on purpose. ElementTree *consumes* xmlns declarations into Clark
    notation, so a parsed tree can prove a prefix resolved but can never tell you what was
    actually written - an unused or reserved prefix declaration is invisible to it. That blind
    spot is exactly what makes this class of bug hard to see, so check the start tag directly.
    The default namespace comes back under the empty-string key.
    """
    start_tag = xml_string[:xml_string.index(">") + 1]
    return dict(re.findall(r'xmlns:?([\w.-]*)="([^"]*)"', start_tag))


def check_reloadable(xml_string, source, new_loader):
    """1. The string alone re-loads into an equivalent document."""
    label = "string re-loads without a file or an external xmlns fixup"
    try:
        loader = new_loader()
        loader.load_odm_string(xml_string)
        reloaded = loader.root()
    except Exception as e:
        # a broken string can fail anywhere in the load path, and not always as an
        # OdmlibError - report it as a failed check rather than a traceback
        check(label, False, f"{type(e).__name__}: {e}")
        return
    check(label, reloaded is not None)
    check("re-loaded document is equivalent to the original",
          reloaded.to_dict() == source.to_dict(),
          "to_dict() differs, so the string lost or altered content")
    # a fixed point: serialize -> load -> serialize must land on the same string, which is
    # what makes the string safe to hand off and round-trip repeatedly
    check("re-serializing the re-loaded document reproduces the same string",
          reloaded.to_xml_string() == xml_string,
          "serialization is not a fixed point across a string round-trip")


def check_schema_valid(xml_string, standard, version, required_ns):
    """2. The string alone is valid against the official CDISC schema."""
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as pe:
        check("string is namespace-well-formed on its own", False, f"ParseError: {pe}")
        return
    check("string is namespace-well-formed on its own", True)
    check("root element resolves to the ODM namespace", root.tag == f"{{{ODM_NS}}}ODM",
          f"root tag is {root.tag!r}")
    resolved = used_namespaces(root)
    missing = required_ns - resolved
    check(f"every namespace the document uses is declared ({len(resolved)} resolved)",
          not missing, f"not resolved after a standalone re-parse: {sorted(missing)}")

    # ...and nothing extra. Read the literal start tag, not the parsed tree.
    declared = declared_namespaces(xml_string)
    check("the default xmlns is the ODM namespace", declared.get("") == ODM_NS,
          f"default xmlns is {declared.get('')!r}")
    unused = {p: u for p, u in declared.items() if p and u not in resolved}
    check("no unused prefix is declared", not unused,
          f"declared but never used in the document: {unused}")
    check("the reserved 'xml' prefix is not declared", "xml" not in declared,
          "xmlns:xml must never be emitted - it is bound implicitly by the XML spec")

    # the string is validated as-is - no file, no set_odm_namespace_attributes_string() repair
    validator = ODMSchemaValidator(standard=standard, version=version)
    errors = list(validator.xsd.iter_errors(xml_string))
    detail = "; ".join(f"{e.reason} @ {e.path}" for e in errors[:5])
    check(f"string validates against the official {standard} v{version} schema",
          not errors, f"{len(errors)} schema error(s): {detail}")


def check_matches_file(xml_string, source):
    """3. The string agrees with what write_xml() writes to a file."""
    # a scratch file: this is an intermediate for the comparison, not snippet output
    with tempfile.TemporaryDirectory() as tmp:
        xml_file = os.path.join(tmp, "written.xml")
        try:
            source.write_xml(xml_file)
            with open(xml_file, "rb") as f:
                written = f.read()
        except Exception as e:
            check("write_xml() writes the document to a file", False, f"{type(e).__name__}: {e}")
            return

        check("write_xml() file starts with the XML declaration",
              written.startswith(XML_DECLARATION), f"starts with {written[:40]!r}")
        # the only difference between the two paths is that declaration, so comparing the
        # remainder is an exact byte-for-byte comparison of the serialized document itself
        body = written[len(XML_DECLARATION):]
        check("file content after the declaration is byte-identical to the string",
              body == xml_string.encode("utf-8"),
              f"file body is {len(body)} bytes, string is {len(xml_string.encode('utf-8'))}")
        # ...and canonical XML agreement, which ignores the declaration entirely and would
        # still catch a difference in attribute order, whitespace, or namespace binding
        try:
            equal = ET.canonicalize(xml_string) == ET.canonicalize(from_file=xml_file)
            detail = "the two serialization paths disagree semantically"
        except ET.ParseError as pe:
            equal, detail = False, f"ParseError: {pe}"
        check("string and file are equal as canonical XML", equal, detail)

        # xml_declaration= landed in odmlib 0.2.1; feature-detect rather than gate on
        # __version__, which reads "0.2.1.dev0" on a dev checkout and sorts below "0.2.1".
        if "xml_declaration" in inspect.signature(source.to_xml_string).parameters:
            check("to_xml_string(xml_declaration=True) is byte-identical to the file",
                  source.to_xml_string(xml_declaration=True).encode("utf-8") == written,
                  "the declaration-included string does not match write_xml() exactly")
            check("...and equals the declaration plus the default string",
                  source.to_xml_string(xml_declaration=True) ==
                  XML_DECLARATION.decode("utf-8") + xml_string,
                  "the two forms disagree by more than the declaration")
        else:
            print("  [SKIP] to_xml_string(xml_declaration=) needs odmlib >= 0.2.2")


def run_case(name, source, new_loader, standard, version, required_ns):
    global current_case
    current_case = name
    print(f"\n{name}")
    xml_string = source.to_xml_string()
    try:
        size = f"{sum(1 for _ in ET.fromstring(xml_string).iter()):,} elements"
    except ET.ParseError:
        size = "does not re-parse"      # reported as a failed check below, not here
    print(f"  serialized {len(xml_string):,} characters, {size}")
    check_reloadable(xml_string, source, new_loader)
    check_schema_valid(xml_string, standard, version, required_ns)
    check_matches_file(xml_string, source)


def check_anti_patterns(odm, define):
    """to_xml() is a serialization buffer, not a self-contained document."""
    global current_case
    current_case = "anti-pattern"
    print("\nAnti-pattern: ET.tostring(obj.to_xml()) instead of obj.to_xml_string()")
    raw_odm = ET.tostring(odm.to_xml(), encoding="UTF-8").decode("utf-8")
    check("to_xml() emits no xmlns declarations", "xmlns" not in raw_odm)
    try:
        raw_odm_tag = ET.fromstring(raw_odm).tag
    except ET.ParseError as pe:
        raw_odm_tag = f"unparseable ({pe})"
    check("so an ODM v1.3.2 tree re-parses into no namespace at all",
          raw_odm_tag == "ODM", f"expected an undeclared 'ODM' root tag, got {raw_odm_tag!r}")
    odm_errors = list(ODMSchemaValidator(standard="odm", version="1.3.2").xsd.iter_errors(raw_odm))
    check("and the official ODM schema rejects it", bool(odm_errors),
          "an undeclared tree unexpectedly passed schema validation")

    # The dangerous half: this does not raise. odmlib loads the namespace-less string,
    # FileOID reads back correctly, and every Study has quietly vanished. A smoke test
    # that only checks FileOID would pass while the payload is gone.
    try:
        bad_loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
        bad_loader.load_odm_string(raw_odm)
        reloaded_bad = bad_loader.root()
    except Exception as e:
        check("odmlib re-loads the undeclared string without raising", False,
              f"{type(e).__name__}: {e}")
        return
    check("odmlib re-loads the undeclared string without raising", True)
    check("...and FileOID still reads back correctly, so it looks fine",
          reloaded_bad.FileOID == odm.FileOID,
          f"{reloaded_bad.FileOID!r} != {odm.FileOID!r}")
    check(f"...but every Study is silently gone ({len(odm.Study)} -> {len(reloaded_bad.Study)})",
          len(odm.Study) > 0 and len(reloaded_bad.Study) == 0,
          "expected the Study elements to be dropped into a foreign namespace")

    raw_define = ET.tostring(define.to_xml(), encoding="UTF-8").decode("utf-8")
    try:
        ET.fromstring(raw_define)
        check("a Define-XML tree is not even well-formed on its own (unbound def: prefix)",
              False, "expected ET.ParseError: unbound prefix")
    except ET.ParseError:
        check("a Define-XML tree is not even well-formed on its own (unbound def: prefix)", True)


def check_nested_element_namespaces(define):
    """Nested elements serialize with their document's namespaces, not global state.

    Everything above serializes document *roots*. Loading captures a per-document namespace
    snapshot, and the loader binds it recursively, so a child reached by *walking* the tree
    is protected too. The one case still not covered is an element constructed after the
    load - shown here honestly rather than glossed over.

    Runs last and restores the registry, because it deliberately mutates global state.
    """
    global current_case
    current_case = "nested elements"
    print("\nNested-element namespace binding")

    mdv = define.Study.MetaDataVersion          # reached by walking, not handed back
    igd = mdv.ItemGroupDef[0]                   # deeper still
    check("the loaded root carries a namespace snapshot",
          NS.get_document_namespaces(define) is not None)
    check("an element reached by walking the tree is bound too (recursive bind)",
          NS.get_document_namespaces(mdv) is not None,
          "the loader did not bind descendants - is this odmlib < 0.2.2?")
    check("a deeply nested element is bound as well",
          NS.get_document_namespaces(igd) is not None)

    try:
        # A legitimate act for an app that handles both Define versions. It re-registers
        # the def: prefix globally, to v2.0.
        import odmlib.define_2_0.model  # noqa: F401

        check("the root serializes with its load-time def/v2.1 (snapshot wins)",
              f'xmlns:def="{DEFINE_NS}"' in define.to_xml_string(),
              "the per-document snapshot failed to protect the root")
        check("the nested element serializes with def/v2.1 as well",
              f'xmlns:def="{DEFINE_NS}"' in mdv.to_xml_string(),
              f"nested element fell back to the global registry ({DEFINE_20_NS})")
        check("so does the deeply nested element",
              f'xmlns:def="{DEFINE_NS}"' in igd.to_xml_string())

        # The residual limitation: built AFTER the load, so never bound.
        fresh = DEFINE.ItemGroupDef(OID="IG.NEW", Name="New", Repeating="No",
                                    IsReferenceData="No", Purpose="Tabulation",
                                    Structure="One record per subject",
                                    ArchiveLocationID="LF.TS")
        check("an element built AFTER the load has no snapshot (documented limitation)",
              NS.get_document_namespaces(fresh) is None)
        check("...so it falls back to the global registry's def/v2.0",
              f'xmlns:def="{DEFINE_20_NS}"' in fresh.to_xml_string(),
              "expected the post-load element to use current global state")
        NS.bind_document_namespaces(fresh, NS.get_document_namespaces(define))
        check("...and an explicit rebind fixes it",
              f'xmlns:def="{DEFINE_NS}"' in fresh.to_xml_string(),
              "NS.bind_document_namespaces() did not take effect")
    finally:
        # Restore the registry so nothing after this point inherits def -> v2.0.
        NS.NamespaceRegistry(prefix="def", uri=DEFINE_NS)


def main():
    for path in (ODM_FILE, DEFINE_FILE):
        if not os.path.isfile(path):
            sys.exit(f"ERROR: {path} not found - run this snippet from the snippets directory")

    def new_odm_loader():
        return LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))

    def new_define_loader():
        return LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1", ns_uri=DEFINE_NS))

    # load both documents up front, so every string below is produced with the other
    # standard's namespaces already registered - a document must serialize with the
    # namespaces it was loaded under, not whatever the shared registry saw last
    odm_loader = new_odm_loader()
    odm_loader.open_odm_document(ODM_FILE)
    odm = odm_loader.root()

    define_loader = new_define_loader()
    define_loader.open_odm_document(DEFINE_FILE)
    define = define_loader.root()

    # a document built in memory has no load-time namespace snapshot, so it exercises the
    # other branch of to_xml_string(): namespaces come from the shared registry instead
    built = (
        ODMBuilder()
        .set_file(FileOID="F.STR.001", FileType="Snapshot",
                  CreationDateTime=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                  ODMVersion="1.3.2", Originator="odmlib")
        .add_study(OID="S.STR.001", study_name="String Serialization",
                   study_description="Built in memory, never loaded from a file",
                   protocol_name="STR-001")
        .add_metadata_version(OID="MDV.STR.001", Name="String Serialization v1")
        .add_item_group_def(OID="IG.DM", Name="DM", Repeating="No")
        .add_item_ref(ItemOID="IT.AGE", Mandatory="Yes", OrderNumber=1)
        .add_item_def(OID="IT.AGE", Name="AGE", DataType="integer", Length=3)
        .build()
    )

    cases = [
        (f"ODM v1.3.2, loaded from {ODM_FILE}", odm, new_odm_loader,
         "odm", "1.3.2", {ODM_NS}),
        (f"Define-XML v2.1, loaded from {DEFINE_FILE}", define, new_define_loader,
         "define", "2.1", {ODM_NS, DEFINE_NS, XLINK_NS}),
        ("ODM v1.3.2, built in memory with ODMBuilder", built, new_odm_loader,
         "odm", "1.3.2", {ODM_NS}),
    ]
    for name, source, new_loader, standard, version, required_ns in cases:
        try:
            run_case(name, source, new_loader, standard, version, required_ns)
        except Exception as e:
            # one broken case must not stop the others from being checked and reported
            check(f"{name}: checks ran to completion", False, f"{type(e).__name__}: {e}")

    global current_case
    current_case = "namespace isolation"
    print("\nNamespace isolation between the documents loaded above")
    check("the loaded ODM string is not polluted by the Define-XML load",
          "xmlns:def" not in odm.to_xml_string(),
          "an ODM v1.3.2 document declared the Define-XML namespace it never uses")

    check_anti_patterns(odm, define)

    # Persist both serialized documents so the output can be schema-validated from an
    # independent process (see the command in this snippet's header).
    current_case = "output files"
    print("\nWriting output files for independent verification")
    for doc, out in ((odm, ODM_OUT), (define, DEFINE_OUT)):
        doc.write_xml(out)
    check(f"wrote {ODM_OUT} and {DEFINE_OUT}",
          all(os.path.isfile(p) for p in (ODM_OUT, DEFINE_OUT)))

    # Last: it mutates the global namespace registry (and restores it).
    check_nested_element_namespaces(define)

    if failures:
        print(f"\n{len(failures)} string serialization check(s) FAILED:")
        for i, label in enumerate(failures, 1):
            print(f"  {i}. {label}")
        sys.exit(1)
    print("\nAll string serialization checks passed.")


if __name__ == "__main__":
    main()
