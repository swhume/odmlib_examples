"""
This odmlib v0.2 example snippet covers new error handling features:
1. **Exception hierarchy** — the new error types and how they relate to each other
2. **Structured error attributes** — accessing context, hints, and element paths on exceptions
3. **Type validation errors** — what happens when you assign the wrong type to an attribute
4. **Required attribute errors** — catching missing required attributes
5. **Element order errors** — detecting and fixing out-of-order child elements
6. **OID validation errors** — duplicate OIDs and broken references
7. **Conformance errors** — Cerberus-based metadata conformance checking
8. **Collect-all-errors mode** — gathering every validation problem in a single pass
9. **Warnings** — non-fatal issues and deprecation notices
10. **Backward compatibility** — how existing `except ValueError` code still works
"""
import datetime
import warnings

import odmlib.define_2_1.model as DEFINE
import odmlib.odm_1_3_2.model as ODM

from odmlib import (
    OdmlibError,
    OdmlibValidationError,
    OdmlibRequiredAttributeError,
    OdmlibTypeError,
    OdmlibOIDError,
    OdmlibConformanceError,
    OdmlibElementOrderError,
    OdmlibWarning,
    OdmlibDeprecationWarning,
    ErrorCollector,
    create_oid_checker,
)

"""
1. Exception hierarchy: the new error types and how they relate to each other
"""
print("1. Exception hierarchy: the new error types and how they relate to each other")
# every odmlib exception is an OdmlibError
print(f"OdmlibValidationError is OdmlibError: {issubclass(OdmlibValidationError, OdmlibError)}")
print(f"OdmlibTypeError is OdmlibError:       {issubclass(OdmlibTypeError, OdmlibError)}")
print(f"OdmlibOIDError is OdmlibError:        {issubclass(OdmlibOIDError, OdmlibError)}")

# specific subtypes
print(f"\nOdmlibOIDError is OdmlibValidationError:        {issubclass(OdmlibOIDError, OdmlibValidationError)}")
print(f"OdmlibConformanceError is OdmlibValidationError: {issubclass(OdmlibConformanceError, OdmlibValidationError)}")
print(f"OdmlibElementOrderError is OdmlibValidationError: {issubclass(OdmlibElementOrderError, OdmlibValidationError)}")

# backward compatibility: validation errors are still ValueErrors
print(f"\nOdmlibValidationError is ValueError: {issubclass(OdmlibValidationError, ValueError)}")
print(f"OdmlibTypeError is TypeError:         {issubclass(OdmlibTypeError, TypeError)}")

"""
2. Structured error attributes: accessing context, hints, and element paths on exceptions
"""
print("\n2. Structured error attributes: accessing context, hints, and element paths on exceptions")
# unlike plain `ValueError` messages, the new exceptions carry structured metadata that you can inspect
# trigger a type error by assigning an integer where a string is expected
try:
    item = ODM.ItemDef(OID="IT.STUDYID", Name="STUDYID", DataType="text", Length=200)
    item.Origin = 12345  # Origin expects a string, not an integer
except OdmlibTypeError as e:
    print("=== Formatted error message ===")
    print(e)
    print("\n=== Structured attributes ===")
    print(f"  attribute:     {e.attribute}")
    print(f"  expected_type: {e.expected_type}")
    print(f"  actual_value:  {e.actual_value}")
    print(f"  hint:          {e.hint}")

"""
3. Type validation errors: what happens when you assign the wrong type to an attribute
"""
print("\n3. Type validation errors: what happens when you assign the wrong type to an attribute")
# example 3.1: wrong type for a string attribute
try:
    study = ODM.Study(OID=999)  # OID must be a string
except OdmlibTypeError as e:
    print(f"String type error: {e.attribute} — got {e.actual_value!r}")
    print(f"  Hint: {e.hint}")

# example 3.2: non-integer where an integer is expected
try:
    item_ref = ODM.ItemRef(ItemOID="IT.STUDYID", OrderNumber="not_a_number", Mandatory="Yes")
except OdmlibTypeError as e:
    print(f"Integer conversion error: {e.attribute} — got {e.actual_value!r}")
    print(f"  Hint: {e.hint}")

# example 3.3: invalid enumerated value
try:
    item = ODM.ItemDef(OID="IT.STUDYID", Name="STUDYID", DataType="invalid_type", Length=200)
except OdmlibTypeError as e:
    print(f"Enumeration error: {e.attribute} — got {e.actual_value!r}")
    print(f"  Hint: {e.hint}")

"""
4. Required attribute errors: catching missing required attributes
"""
print("\n4. Required attribute errors: catching missing required attributes")
# create an ItemDef without the required DataType attribute, then try to access it
item = ODM.ItemDef.__new__(ODM.ItemDef)  # bypass __init__ to skip validation
item.__dict__["OID"] = "IT.TEST"
item.__dict__["Name"] = "TEST"
# DataType was never set
try:
    _ = item.DataType  # accessing the missing required attribute
except OdmlibRequiredAttributeError as e:
    print(f"Missing attribute: {e.attribute}")
    print(f"Element type: {e.element_type}")
    print(f"Hint: {e.hint}")

"""
5. Element order errors: detecting and fixing out-of-order child elements
"""
print("\n5. Element order errors: detecting and fixing out-of-order child elements")
# build a small Define-XML document with elements in the wrong order
current_datetime = datetime.datetime.now(datetime.timezone.utc).isoformat()

odm = DEFINE.ODM(
    FileOID="DEF.DEMO",
    FileType="Snapshot",
    CreationDateTime=current_datetime,
    ODMVersion="1.3.2",
    Context="Submission",
    Originator="odmlib",
    SourceSystem="odmlib",
    SourceSystemVersion="0.2.0",
)

study = DEFINE.Study(OID="ST.DEMO")
study.GlobalVariables = DEFINE.GlobalVariables()
study.GlobalVariables.StudyName = ODM.StudyName(_content="Demo Study")
study.GlobalVariables.StudyDescription = ODM.StudyDescription(_content="Error handling demo")
study.GlobalVariables.ProtocolName = ODM.ProtocolName(_content="DEMO-001")

mdv = DEFINE.MetaDataVersion(OID="MDV.DEMO", Name="Demo MDV", DefineVersion="2.1.0")
study.MetaDataVersion = mdv
odm.Study = study

# add an ItemDef before an ItemGroupDef — this is the wrong order per the ODM spec
item = ODM.ItemDef(OID="IT.STUDYID", Name="STUDYID", DataType="text", Length=200)
mdv.ItemDef.append(item)

igd = DEFINE.ItemGroupDef(
    OID="IG.DM", Name="DM", Repeating="No",
    IsReferenceData="No", SASDatasetName="DM",
    Structure="One record per subject", Purpose="Tabulation",
)
igd.ItemRef.append(ODM.ItemRef(ItemOID="IT.STUDYID", OrderNumber=1, Mandatory="Yes"))
mdv.ItemGroupDef.append(igd)

print("Document built with elements in the wrong order.")
# verify_order() detects the problem
try:
    mdv.verify_order()
except OdmlibElementOrderError as e:
    print(f"Order error in: {e.element_type}")
    print(f"Hint: {e.hint}")
    print(f"\nFull message:\n{e}")

# fix the ordering automatically with reorder_object()
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    mdv.reorder_object()
    if caught:
        print(f"Warning issued: {caught[0].message}")

# now verify_order() passes
result = mdv.verify_order()
print(f"\nOrder verified: {result}")

"""
6. OID validation errors: duplicate OIDs and broken references
"""
print("\n6. OID validation errors: duplicate OIDs and broken references")
# create a checker for the Define-XML 2.1 model
checker = create_oid_checker("define_2_1")

# add a broken reference — this ItemRef points to an OID that does not exist
igd2 = DEFINE.ItemGroupDef(
    OID="IG.VS", Name="VS", Repeating="Yes",
    IsReferenceData="No", SASDatasetName="VS",
    Structure="One record per subject per visit per test", Purpose="Tabulation",
)
igd2.ItemRef.append(ODM.ItemRef(ItemOID="IT.NONEXISTENT", OrderNumber=1, Mandatory="Yes"))
mdv.ItemGroupDef.append(igd2)

try:
    odm.verify_oids(checker)
except OdmlibOIDError as e:
    print(f"OID error: {e}")

# Fix the broken reference first so verify_oids passes
mdv.ItemGroupDef.remove(igd2)  # remove the problematic ItemGroupDef

# Add a MethodDef that nothing references
orphan_method = ODM.MethodDef(OID="MT.ORPHAN", Name="Orphaned Method", Type="Computation")
orphan_method.Description = ODM.Description()
orphan_method.Description.TranslatedText.append(
    ODM.TranslatedText(_content="This method is not referenced anywhere", lang="en")
)
mdv.MethodDef.append(orphan_method)

checker = create_oid_checker("define_2_1")
odm.verify_oids(checker)

orphans = odm.unreferenced_oids(checker)
if orphans:
    print("Unreferenced OIDs found:")
    for oid, ref_attr in orphans.items():
        print(f"  {oid} (expected ref attribute: {ref_attr})")
else:
    print("All OIDs are referenced.")

"""
7. Conformance errors: Cerberus-based metadata conformance checking
"""
print("\n7. Conformance errors: Cerberus-based metadata conformance checking")
from odmlib.define_2_1.rules.metadata_schema import MetadataSchema

conformance = MetadataSchema()

# create an ItemGroupDef with missing required fields for conformance
bad_igd = DEFINE.ItemGroupDef(
    OID="IG.BAD", Name="BAD", Repeating="No",
    IsReferenceData="No", SASDatasetName="BAD",
    Structure="", Purpose="Tabulation",  # empty Structure may fail conformance
)

try:
    bad_igd.verify_conformance(conformance)
    print("Conformance check passed.")
except OdmlibConformanceError as e:
    print(f"Conformance error for: {e.element_type}")
    print(f"Hint: {e.hint}")
    print(f"\nCerberus errors (dict): {e.cerberus_errors}")

"""
8. Collect-all-errors mode: gathering every validation problem in a single pass
"""
print("\n8. Collect-all-errors mode: gathering every validation problem in a single pass")
# first, fail-fast mode (the default)
checker = create_oid_checker("define_2_1")
conformance = MetadataSchema()

try:
    odm.validate(collect_errors=False, oid_checker=checker, conformance_checker=conformance)
    print("Validation passed.")
except OdmlibError as e:
    print(f"Fail-fast stopped at first error:")
    print(f"  Type: {type(e).__name__}")
    print(f"  Message: {e}")

# now use collect_errors=True to gather all errors
checker = create_oid_checker("define_2_1")

errors = odm.validate(collect_errors=True, oid_checker=checker, conformance_checker=conformance)

if errors:
    print(f"Found {len(errors)} validation error(s):\n")
    for i, err in enumerate(errors, 1):
        print(f"  {i}. [{type(err).__name__}] {err}")
else:
    print("No validation errors found.")

collector = ErrorCollector()

# Add odmlib errors from validate()
checker = create_oid_checker("define_2_1")
odmlib_errors = odm.validate(collect_errors=True, oid_checker=checker)
for err in odmlib_errors:
    collector.add_error(err)

# Add your own custom validation errors
for igd in mdv.ItemGroupDef:
    if not igd.ItemRef:
        collector.add_error(
            OdmlibValidationError(
                f"ItemGroupDef '{igd.OID}' has no ItemRef children",
                element_type="ItemGroupDef",
                hint="Every dataset should reference at least one variable",
            )
        )

# check results
print(f"Total errors collected: {len(collector.errors)}")
print(f"Has errors: {collector.has_errors}")

# raise_if_errors() raises a summary exception if there are multiple errors,
# or re-raises the single error if there is exactly one
if collector.has_errors:
    try:
        collector.raise_if_errors()
    except OdmlibValidationError as e:
        print(f"\nSummary exception:\n{e}")
