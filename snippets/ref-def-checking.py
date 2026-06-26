"""
This odmlib v0.2 example snippet covers:
1. Basic usage — creating a checker and validating OID integrity
2. What the checker validates — duplicate OIDs, missing definitions, type mismatches
3. Finding unreferenced OIDs — detecting orphaned metadata
4. Inspecting the discovered mappings — understanding what the introspection found
5. Cross-model support — using the same API for ODM 1.3.2, Define-XML 2.1, and more
"""

import argparse
import odmlib.odm_1_3_2.model as ODM
import odmlib.define_2_1.model as DEFINE
from odmlib import create_oid_checker, OdmlibOIDError


# build a small but internally consistent MetaDataVersion
protocol = ODM.Protocol()
protocol.StudyEventRef = [
    ODM.StudyEventRef(StudyEventOID="SE.BASELINE", OrderNumber=1, Mandatory="Yes")
]

se_baseline = ODM.StudyEventDef(OID="SE.BASELINE", Name="Baseline Visit", Repeating="No", Type="Scheduled")
se_baseline.FormRef = [ODM.FormRef(FormOID="F.DM", Mandatory="Yes", OrderNumber=1)]

form_dm = ODM.FormDef(OID="F.DM", Name="Demographics", Repeating="No")
form_dm.ItemGroupRef = [ODM.ItemGroupRef(ItemGroupOID="IG.DM", Mandatory="Yes")]

igd_dm = ODM.ItemGroupDef(OID="IG.DM", Name="Demographics", Repeating="No")
igd_dm.ItemRef = [
    ODM.ItemRef(ItemOID="IT.SUBJID", Mandatory="Yes", OrderNumber=1),
    ODM.ItemRef(ItemOID="IT.AGE", Mandatory="Yes", OrderNumber=2),
    ODM.ItemRef(ItemOID="IT.SEX", Mandatory="Yes", OrderNumber=3),
]

item_subjid = ODM.ItemDef(OID="IT.SUBJID", Name="Subject ID", DataType="text", Length=20)
item_age = ODM.ItemDef(OID="IT.AGE", Name="Age", DataType="integer", Length=3)
item_sex = ODM.ItemDef(OID="IT.SEX", Name="Sex", DataType="text", Length=1)
item_sex.CodeListRef = ODM.CodeListRef(CodeListOID="CL.SEX")

cl_sex = ODM.CodeList(OID="CL.SEX", Name="Sex", DataType="text")
cl_sex.CodeListItem = [
    ODM.CodeListItem(CodedValue="M", Decode=ODM.Decode(
        TranslatedText=[ODM.TranslatedText(_content="Male", lang="en")])),
    ODM.CodeListItem(CodedValue="F", Decode=ODM.Decode(
        TranslatedText=[ODM.TranslatedText(_content="Female", lang="en")])),
]

mdv = ODM.MetaDataVersion(OID="MDV.001", Name="Demographics v1")
mdv.Protocol = protocol
mdv.StudyEventDef = [se_baseline]
mdv.FormDef = [form_dm]
mdv.ItemGroupDef = [igd_dm]
mdv.ItemDef = [item_subjid, item_age, item_sex]
mdv.CodeList = [cl_sex]

print("MetaDataVersion built with:")
print(f"  1 StudyEventDef  -> references FormDef F.DM")
print(f"  1 FormDef        -> references ItemGroupDef IG.DM")
print(f"  1 ItemGroupDef   -> references 3 ItemDefs")
print(f"  3 ItemDefs       -> IT.SEX references CodeList CL.SEX")
print(f"  1 CodeList")

"""
1. basic usage: create a checker and validate
"""
print("\n1. basic usage: create a basic checker and validate OID usage")
checker = create_oid_checker("odm_1_3_2")
result = mdv.verify_oids(checker)

print(f"\nOID validation passed: {result}")
print(f"\nOID definitions found: {len(checker.oid)}")
for oid, element_type in sorted(checker.oid.items()):
    print(f"  {oid:20s} defined by {element_type}")

# inspect the collected OID references
print("OID references collected:")
for attr, oid_set in sorted(checker.oid_ref.items()):
    if oid_set:  # only show attributes that had references
        expected_def = checker.ref_def.get(attr, "?")
        print(f"  {attr:25s} -> {sorted(oid_set)}  (expects {expected_def})")

"""
2. what the checker validates: a. duplicate OIDs, b. missing definitions, c. type mismatches
"""
print("\n2. what the checker validates: a. duplicate OIDs, b. missing definitions, c. type mismatches")
# add a second ItemDef with the same OID as an existing one
duplicate_item = ODM.ItemDef(OID="IT.AGE", Name="Age Duplicate", DataType="integer", Length=3)
mdv.ItemDef.append(duplicate_item)

### 2.a.
print("\n2a. check for duplicate OIDs")
checker_dup = create_oid_checker("odm_1_3_2")
try:
    mdv.verify_oids(checker_dup)
except OdmlibOIDError as e:
    print(f"Caught: {type(e).__name__}")
    print(f"  Message:   {e}")
    print(f"  Attribute: {e.attribute}")
    print(f"  Hint:      {e.hint}")

# remove the duplicate so subsequent examples work
mdv.ItemDef.remove(duplicate_item)

### 2.b.
print("\n2b. check for missing definitions")
# add an ItemRef that points to a non-existent ItemDef
igd_dm.ItemRef.append(
    ODM.ItemRef(ItemOID="IT.NONEXISTENT", Mandatory="No", OrderNumber=4)
)

checker_missing = create_oid_checker("odm_1_3_2")
try:
    mdv.verify_oids(checker_missing)
except OdmlibOIDError as e:
    print(f"Caught: {type(e).__name__}")
    print(f"  Message:   {e}")
    print(f"  Attribute: {e.attribute}")
    print(f"  Hint:      {e.hint}")

# clean up
igd_dm.ItemRef.pop()

### 2.c.
print("\n2c. check for type mismatches")
# add an ItemRef whose ItemOID points to the CodeList OID instead of an ItemDef
igd_dm.ItemRef.append(
    ODM.ItemRef(ItemOID="CL.SEX", Mandatory="No", OrderNumber=4)
)

checker_mismatch = create_oid_checker("odm_1_3_2")
try:
    mdv.verify_oids(checker_mismatch)
except OdmlibOIDError as e:
    print(f"Caught: {type(e).__name__}")
    print(f"  Message:   {e}")
    print(f"  Attribute: {e.attribute}")
    print(f"  Hint:      {e.hint}")

# clean up
igd_dm.ItemRef.pop()

"""
3. find unreferenced OIDs
"""
print("\n3. find unreferenced OIDs")
# add an ItemDef that nothing references - an orphan
orphan_item = ODM.ItemDef(OID="IT.UNUSED_WEIGHT", Name="Weight", DataType="float", Length=5)
mdv.ItemDef.append(orphan_item)

# add a CodeList that nothing references - an orphan
orphan_cl = ODM.CodeList(OID="CL.UNUSED_NY", Name="No Yes", DataType="text")
orphan_cl.EnumeratedItem = [
    ODM.EnumeratedItem(CodedValue="N"),
    ODM.EnumeratedItem(CodedValue="Y"),
]
mdv.CodeList.append(orphan_cl)

# verify OIDs first - required before checking unreferenced
checker_orphan = create_oid_checker("odm_1_3_2")
mdv.verify_oids(checker_orphan)

# find unreferenced OIDs
orphans = mdv.unreferenced_oids(checker_orphan)

if orphans:
    print(f"Found {len(orphans)} unreferenced OID(s):")
    for oid, ref_attr in orphans.items():
        # ref_attr tells us what kind of reference attribute should have pointed here
        print(f"  {oid:25s} (expected reference via {ref_attr})")
else:
    print("All OIDs are referenced.")

# clean up
mdv.ItemDef.remove(orphan_item)
mdv.CodeList.remove(orphan_cl)

"""
4. Inspecting the discovered mappings: understanding what the introspection found
"""
print("\n4. Inspecting the discovered mappings: understanding what the introspection found")
# create a fresh checker and inspect what the introspection discovered about the model
checker = create_oid_checker("odm_1_3_2")
print("=== OID Definition Elements ===")
print(f"Classes with an OID attribute ({len(checker.oid_defs)}):")
for cls_name in sorted(checker.oid_defs):
    print(f"  {cls_name}")

print(f"\n=== Ref -> Def Mapping ({len(checker.ref_def)} entries) ===")
print("Which definition class does each reference attribute point to?")
for attr, def_class in sorted(checker.ref_def.items()):
    print(f"  {attr:40s} -> {def_class}")

print(f"\n=== Def -> Ref Mapping ({len(checker.def_ref)} entries) ===")
print("Which reference attributes point to each definition class?")
for def_class, ref_attrs in sorted(checker.def_ref.items()):
    print(f"  {def_class:25s} <- {ref_attrs}")

# each model has a skip list of elements and attributes to omit from the check
print("=== Skip Lists for ODM 1.3.2 ===")
print(f"Skipped attributes: {checker.skip_attr}")
print(f"Skipped elements:   {checker.skip_elem}")

# you can add extra skips via the factory function parameters
custom_checker = create_oid_checker(
    "odm_1_3_2",
    extra_skip_attrs=["SomeCustomOID"],
    extra_skip_elems=["MyCustomElement"],
)

print(f"Extended skip_attr: {custom_checker.skip_attr}")
print(f"Extended skip_elem: {custom_checker.skip_elem}")

"""
5. Cross-model support: using the same API for ODM 1.3.2, Define-XML 2.1, and more
"""
print("\n5. Cross-model support: using the same API for ODM 1.3.2, Define-XML 2.1, and more")
# compare checkers for different models
checker_odm = create_oid_checker("odm_1_3_2")
checker_define = create_oid_checker("define_2_1")

print("=== ODM 1.3.2 ===")
print(f"  OID definition classes: {len(checker_odm.oid_defs)}")
print(f"  Ref -> Def mappings:    {len(checker_odm.ref_def)}")
print(f"  Skip attrs:             {checker_odm.skip_attr}")
print(f"  Skip elems:             {checker_odm.skip_elem}")

print(f"\n=== Define-XML 2.1 ===")
print(f"  OID definition classes: {len(checker_define.oid_defs)}")
print(f"  Ref -> Def mappings:    {len(checker_define.ref_def)}")
print(f"  Skip attrs:             {checker_define.skip_attr}")
print(f"  Skip elems:             {checker_define.skip_elem}")

# show what Define-XML adds beyond ODM
odm_defs = set(checker_odm.oid_defs)
define_defs = set(checker_define.oid_defs)
define_only = define_defs - odm_defs
if define_only:
    print(f"\n  Define-XML specific definition classes: {sorted(define_only)}")

odm_refs = set(checker_odm.ref_def.keys())
define_refs = set(checker_define.ref_def.keys())
define_only_refs = define_refs - odm_refs
if define_only_refs:
    print(f"  Define-XML specific ref attributes:     {sorted(define_only_refs)}")

# build a Define-XML 2.1 MetaDataVersion with interconnected elements
wc = DEFINE.WhereClauseDef(OID="WC.DM.SEX")
vl = DEFINE.ValueListDef(OID="VL.DM.SEX")

# the ValueListDef contains an ItemRef that references both the ItemDef and WhereClauseDef
vl_item_ref = DEFINE.ItemRef(ItemOID="IT.DM.SEX", Mandatory="No")
vl_item_ref.WhereClauseRef = [DEFINE.WhereClauseRef(WhereClauseOID="WC.DM.SEX")]
vl.ItemRef = [vl_item_ref]

# ItemDef references a CodeList and a ValueList
item_def = DEFINE.ItemDef(OID="IT.DM.SEX", Name="Sex", DataType="text", Length=1)
item_def.CodeListRef = DEFINE.CodeListRef(CodeListOID="CL.SEX")
item_def.ValueListRef = DEFINE.ValueListRef(ValueListOID="VL.DM.SEX")

# a comment attached via CommentOID
comment = DEFINE.CommentDef(OID="COM.DM.001")
comment.Description = DEFINE.Description()
comment.Description.TranslatedText = [DEFINE.TranslatedText(_content="Demographics comment", lang="en")]

codelist = DEFINE.CodeList(OID="CL.SEX", Name="Sex", DataType="text", SASFormatName="SEX")

define_mdv = DEFINE.MetaDataVersion(
    OID="MDV.DEFINE", Name="Define Test", Description="OID check demo", DefineVersion="2.1.0",
)
define_mdv.ValueListDef = [vl]
define_mdv.WhereClauseDef = [wc]
define_mdv.ItemDef = [item_def]
define_mdv.CodeList = [codelist]
define_mdv.CommentDef = [comment]

# validate with a Define-XML 2.1 checker
checker_d21 = create_oid_checker("define_2_1")
result = define_mdv.verify_oids(checker_d21)
print(f"Define-XML 2.1 OID validation passed: {result}")

print(f"\nOID definitions found: {len(checker_d21.oid)}")
for oid, elem_type in sorted(checker_d21.oid.items()):
    print(f"  {oid:20s} -> {elem_type}")

print(f"\nReferences validated:")
for attr, oid_set in sorted(checker_d21.oid_ref.items()):
    if oid_set:
        print(f"  {attr:25s} -> {sorted(oid_set)}")
