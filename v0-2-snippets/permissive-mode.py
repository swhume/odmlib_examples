"""
This odmlib v0.2 example snippet covers:
1. **The problem** — what happens when strict mode encounters non-conformant content
2. **The `permissive()` context manager** — temporarily relaxing validation
3. **`ValidationMode` flags** — graduated control over which checks to skip
4. **Loading non-conformant files** — using `open_odm()` and `open_define()` with `permissive`
5. **The Load-Inspect-Fix-Validate workflow** — repairing a broken document end-to-end
"""
import os
import tempfile
import odmlib.odm_loader as OL
import odmlib.loader as LD
import odmlib.odm_1_3_2.model as ODM
import odmlib.define_2_1.model as DEFINE

from odmlib import (
    ValidationMode,
    permissive,
    get_mode,
    set_mode,
    open_odm,
    open_define,
    OdmlibTypeError,
    OdmlibValidationError,
)

"""
1. The problem: what happens when strict mode encounters non-conformant content
"""
print("1. The problem: what happens when strict mode encounters non-conformant content")
# strict mode is the default and its not possible to load a non-conformant document
try:
    item = ODM.ItemDef(OID="IT.BAD", Name="BAD", DataType="bogus", Length=8)
except (OdmlibTypeError, OdmlibValidationError) as e:
    print(f"Strict mode rejected the ItemDef:")
    print(f"  {type(e).__name__}: {e}")

try:
    ref = ODM.ItemRef(ItemOID="IT.TEST", Mandatory="Maybe")
except (OdmlibTypeError, OdmlibValidationError) as e:
    print(f"Strict mode rejected the ItemRef:")
    print(f"  {type(e).__name__}: {e}")

try:
    loader = LD.ODMLoader(OL.XMLODMLoader())
    loader.open_odm_document("data/nonconformant_odm.xml")
    odm = loader.root()
except Exception as e:
    print(f"Failed to load non-conformant file in strict mode:")
    print(f"  {type(e).__name__}: {e}")

"""
2. The `permissive()` context manager: temporarily relaxing validation
"""
print("\n2. The `permissive()` context manager: temporarily relaxing validation")
with permissive():
    item = ODM.ItemDef(OID="IT.BAD", Name="BAD", DataType="bogus", Length=8)
    print(f"ItemDef created successfully in permissive mode")
    print(f"  OID:      {item.OID}")
    print(f"  Name:     {item.Name}")
    print(f"  DataType: {item.DataType}")

# strict mode is automatically restored outside the block
print(f"\nCurrent mode: {get_mode()}")
with permissive():
    loader = LD.ODMLoader(OL.XMLODMLoader())
    loader.open_odm_document("data/nonconformant_odm.xml")
    odm = loader.root()

print(f"Loaded successfully in permissive mode!")
print(f"  FileOID:    {odm.FileOID}")
print(f"  Study OID:  {odm.Study[0].OID}")
print(f"  StudyName:  {odm.Study[0].GlobalVariables.StudyName}")

mdv = odm.Study[0].MetaDataVersion[0]
item_def = mdv.ItemDef[0]
item_ref = mdv.ItemGroupDef[0].ItemRef[0]

print(f"\nNon-conformant values that were loaded:")
print(f"  ItemDef.DataType:  {item_def.DataType!r} (should be a valid CDISC type)")
print(f"  ItemRef.Mandatory: {item_ref.Mandatory!r} (should be 'Yes' or 'No')")

with permissive():
    # TODO if Name is missing and loaded in permissive mode, should the below raise an error?
    print(f"  ItemDef.Name:      {item_def.Name!r} (missing required attribute)")
    # set Name to be an integer instead of a string
    item_def.Name = 1234

# prints fine outside of the permissive block - a missing name
print(f"  ItemDef.Name:      {item_def.Name!r} (string attribute set to an integer)")

"""
3. `ValidationMode` flags: graduated control over which checks to skip
"""
print("\n3. `ValidationMode` flags: graduated control over which checks to skip")
# the flags and their values
for member in ValidationMode:
    print(f"  {member.name:20s} = {member.value}")

# PERMISSIVE is a composite of all four SKIP flags
print(f"\nPERMISSIVE == SKIP_REQUIRED | SKIP_VALUESET | SKIP_TYPE | SKIP_FORMAT:")
composed = (ValidationMode.SKIP_REQUIRED | ValidationMode.SKIP_VALUESET
            | ValidationMode.SKIP_TYPE | ValidationMode.SKIP_FORMAT)
print(f"  {ValidationMode.PERMISSIVE == composed}")

# in strict mode, omitting the required Name attribute raises an error
try:
    item = ODM.ItemDef(OID="IT.TEST", DataType="text")
except Exception as e:
    print(f"Strict: {type(e).__name__}: {e}")

# with SKIP_REQUIRED, the object is created and Name returns None
with permissive(ValidationMode.SKIP_REQUIRED):
    item = ODM.ItemDef(OID="IT.TEST", DataType="text")
    print(f"\nSKIP_REQUIRED: ItemDef created without Name")
    print(f"  OID:  {item.OID}")
    print(f"  Name: {item.Name!r}  (None = not set)")

with permissive(ValidationMode.SKIP_VALUESET):
    # DataType="bogus" is not a valid CDISC data type
    item = ODM.ItemDef(OID="IT.TEST", Name="TEST", DataType="bogus", Length=8)
    print(f"SKIP_VALUESET: ItemDef.DataType = {item.DataType!r}")

    # Mandatory="Maybe" is not Yes/No
    ref = ODM.ItemRef(ItemOID="IT.TEST", Mandatory="Maybe")
    print(f"SKIP_VALUESET: ItemRef.Mandatory = {ref.Mandatory!r}")

# in strict mode, OID must be a string
try:
    study = ODM.Study(OID=12345)
except OdmlibTypeError as e:
    print(f"Strict: {e}")

# with SKIP_TYPE, the integer is stored as-is
with permissive(ValidationMode.SKIP_TYPE):
    study = ODM.Study(OID=12345)
    print(f"\nSKIP_TYPE: Study.OID = {study.OID!r} (type: {type(study.OID).__name__})")

    # unknown attributes set via assignment are accepted instead of raising an error
    item = ODM.ItemDef(OID="IT.TEST", Name="TEST", DataType="text", Length=8)
    item.CustomAttr = "unexpected"
    print(f"SKIP_TYPE: Unknown attribute stored: CustomAttr = {item.CustomAttr!r}")

# In strict mode, CreationDateTime must be a valid ISO 8601 datetime
try:
    odm_bad = ODM.ODM(
        FileOID="F.TEST", FileType="Snapshot",
        CreationDateTime="not-a-datetime",
        ODMVersion="1.3.2",
    )
except Exception as e:
    print(f"Strict: {type(e).__name__}: {e}")

# with SKIP_FORMAT, the malformed string is stored
with permissive(ValidationMode.SKIP_FORMAT):
    odm_bad = ODM.ODM(
        FileOID="F.TEST", FileType="Snapshot",
        CreationDateTime="not-a-datetime",
        ODMVersion="1.3.2",
    )
    print(f"\nSKIP_FORMAT: CreationDateTime = {odm_bad.CreationDateTime!r}")

# skip required and valueset checks, but still enforce type and format
selective = ValidationMode.SKIP_REQUIRED | ValidationMode.SKIP_VALUESET
print(f"Combined mode: {selective}")
print(f"  Includes SKIP_REQUIRED: {bool(selective & ValidationMode.SKIP_REQUIRED)}")
print(f"  Includes SKIP_VALUESET: {bool(selective & ValidationMode.SKIP_VALUESET)}")
print(f"  Includes SKIP_TYPE:     {bool(selective & ValidationMode.SKIP_TYPE)}")
print(f"  Includes SKIP_FORMAT:   {bool(selective & ValidationMode.SKIP_FORMAT)}")

with permissive(selective):
    # this works: missing Name (SKIP_REQUIRED) and bogus DataType (SKIP_VALUESET)
    item = ODM.ItemDef(OID="IT.TEST", DataType="bogus")
    print(f"\nCreated ItemDef with missing Name and invalid DataType")
    print(f"  Name: {item.Name!r}, DataType: {item.DataType!r}")

    # but this still fails: wrong type for OID (SKIP_TYPE is NOT active)
    try:
        bad = ODM.Study(OID=12345)
    except OdmlibTypeError:
        print(f"  Type check still enforced: OID=12345 was rejected")

"""
4. Loading Non-Conformant Files with `open_odm()` and `open_define()`
"""
print("\n4. Loading Non-Conformant Files with `open_odm()` and `open_define()`")
output = os.path.join("data", "inspect_odm.xml")

with open_odm("data/nonconformant_odm.xml", output_file=output, permissive=True) as odm:
    print(f"Loaded non-conformant ODM: {odm.FileOID}")
    print(f"  Study:     {odm.Study[0].OID}")
    print(f"  StudyName: {odm.Study[0].GlobalVariables.StudyName}")

    mdv = odm.Study[0].MetaDataVersion[0]
    for igd in mdv.ItemGroupDef:
        print(f"\n  ItemGroupDef: {igd.Name} ({igd.OID})")
        for ref in igd.ItemRef:
            print(f"    ItemRef: OID={ref.ItemOID}, Mandatory={ref.Mandatory!r}")

    for item in mdv.ItemDef:
        print(f"\n  ItemDef: OID={item.OID}")
        print(f"    Name:     {item.Name!r}")
        print(f"    DataType: {item.DataType!r}")

# selective permissive mode
output = os.path.join("data", "selective_odm.xml")
selective_mode = ValidationMode.SKIP_REQUIRED | ValidationMode.SKIP_VALUESET

with open_odm("data/nonconformant_odm.xml", output_file=output,
              permissive=selective_mode) as odm:
    mdv = odm.Study[0].MetaDataVersion[0]
    item = mdv.ItemDef[0]
    print(f"Loaded with selective flags: {selective_mode}")
    print(f"  ItemDef.Name:     {item.Name!r} (missing required — allowed by SKIP_REQUIRED)")
    print(f"  ItemDef.DataType: {item.DataType!r} (invalid value — allowed by SKIP_VALUESET)")

# loading a non-conformant Define-XML
output = os.path.join("data", "inspect_define.xml")
with open_define("data/nonconformant_define21.xml", output_file=output,
                 permissive=True) as define:
    print(f"Loaded non-conformant Define-XML: {define.FileOID}")
    print(f"  Context: {define.Context!r}")
    mdv = define.Study.MetaDataVersion
    print(f"  DefineVersion: {mdv.DefineVersion}")

    for igd in mdv.ItemGroupDef:
        print(f"\n  ItemGroupDef: {igd.Name} ({igd.OID})")
        print(f"    Repeating:      {igd.Repeating!r}  (missing required attribute)")
        print(f"    SASDatasetName: {igd.SASDatasetName!r}")

    for item in mdv.ItemDef:
        print(f"\n  ItemDef: {item.Name} ({item.OID})")
        print(f"    DataType: {item.DataType!r}")


"""
5. Permissive mode enables a structured workflow for repairing non-conformant documents:
1. **Load** — open the document in permissive mode
2. **Inspect** — examine the loaded objects to find violations
3. **Fix** — correct the conformance problems programmatically
4. **Validate** — reload the repaired document in strict mode to confirm it is conformant
"""
### Step 1: Load and Inspect
with permissive():
    loader = LD.ODMLoader(OL.XMLODMLoader())
    loader.open_odm_document("data/nonconformant_odm.xml")
    odm = loader.root()

mdv = odm.Study[0].MetaDataVersion[0]

# inspect for violations
issues = []
for item in mdv.ItemDef:
    # TODO this doesn't work because Name is required and is missing in the define.xml - should this work?
    # Hint: Attribute 'Name' is required when constructing ItemDef
    # Hack: added with permissive() to skip the Name check
    with permissive():
        if item.Name is None:
            issues.append(f"ItemDef '{item.OID}': missing required Name attribute")
    if item.DataType not in ("text", "integer", "float", "date", "time",
                             "datetime", "string", "boolean", "double",
                             "hexBinary", "base64Binary", "hexFloat",
                             "base64Float", "partialDate", "partialTime",
                             "partialDatetime", "durationDatetime",
                             "intervalDatetime", "incompleteDatetime",
                             "incompleteDate", "incompleteTime", "URI"):
        issues.append(f"ItemDef '{item.OID}': invalid DataType '{item.DataType}'")

for igd in mdv.ItemGroupDef:
    for ref in igd.ItemRef:
        if ref.Mandatory not in ("Yes", "No"):
            issues.append(f"ItemRef '{ref.ItemOID}': invalid Mandatory '{ref.Mandatory}'")

print(f"Found {len(issues)} issue(s):")
for i, issue in enumerate(issues, 1):
    print(f"  {i}. {issue}")

### Step 2: Fix the conformance problems
# Fix 1: Set the missing Name attribute
for item in mdv.ItemDef:
    # TODO this doesn't work because Name is required and is missing in the define.xml - should this work?
    # Hack: added with permissive() to skip the Name check
    with permissive():
        if item.Name is None:
            item.Name = item.OID.replace("IT.", "")  # derive Name from OID
            print(f"Fixed: ItemDef '{item.OID}' Name set to '{item.Name}'")

# Fix 2: Correct the invalid DataType
for item in mdv.ItemDef:
    if item.DataType == "bogus":
        item.DataType = "text"  # default to text
        print(f"Fixed: ItemDef '{item.OID}' DataType set to 'text'")

# Fix 3: Correct the invalid Mandatory value
for igd in mdv.ItemGroupDef:
    for ref in igd.ItemRef:
        if ref.Mandatory == "Maybe":
            ref.Mandatory = "No"  # default to No for uncertain items
            print(f"Fixed: ItemRef '{ref.ItemOID}' Mandatory set to 'No'")

### Step 3: Save the Repaired Document
repaired_file = os.path.join("data", "repaired_odm.xml")
odm.write_xml(repaired_file)
print(f"Repaired document written to: {repaired_file}")
