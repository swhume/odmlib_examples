from odmlib.context import open_odm, open_define
import os
import shutil
import json

source_file = os.path.join("data", "cdash-odm-test.xml")
output_ctx = os.path.join("data", "context_demo_output.xml")

# demonstrate the open_odm context manager
with open_odm(source_file, output_file=output_ctx) as odm:
    # inside the with block, `odm` is a fully loaded odmlib ODM object
    odm.SourceSystem = "Modified by context manager"
    mdv = odm.Study[0].MetaDataVersion[0]
    print(f"  Loaded: FileOID={odm.FileOID}, {len(mdv.ItemDef)} ItemDefs")
    print(f"  Modified SourceSystem to: {odm.SourceSystem}")

# odm file was automatically written when the `with` block exited cleanly
print(f"\nFile saved to {os.path.basename(output_ctx)} ({os.path.getsize(output_ctx)} bytes)")

# quick update file in place
inplace_file = os.path.join("data", "context_inplace.xml")
shutil.copy(source_file, inplace_file)

# verify original value
with open_odm(inplace_file) as odm:
    print(f"Before: Originator = {odm.Originator!r}")

# modify in place (no output_file argument)
with open_odm(inplace_file) as odm:
    odm.Originator = "Updated In-Place"

# read back to confirm the change persisted
with open_odm(inplace_file) as odm:
    print(f"After:  Originator = {odm.Originator!r}")


# demo context manager error handling
print("\n\n=== Error handling demo ===")
error_output = os.path.join("data", "context_error_output.xml")

try:
    with open_odm(source_file, output_file=error_output) as odm:
        odm.SourceSystem = "This change should NOT be saved"
        # Simulate an error occurring mid-modification
        raise ValueError("Something went wrong during processing!")
except ValueError as e:
    print(f"Caught exception: {e}")

# the output file should not exist because the exception prevented saving
file_exists = os.path.exists(error_output)
print(f"Output file exists: {file_exists}")
print("The original source file is untouched, and no corrupted output was written.")

# demonstrates the open_odm context manager using JSON
print("\n\n=== JSON context demo ===")
json_source = os.path.join("data", "context_demo.json")
json_output = os.path.join("data", "context_demo_output.json")
# JSON auto-detection
with open_odm(json_source, output_file=json_output) as odm:
    print(f"Loaded from JSON: FileOID={odm.FileOID}")
    odm.SourceSystem = "Modified via JSON context"

# verify output is JSON
with open(json_output) as f:
    d = json.load(f)
print(f"Saved as JSON: SourceSystem={d['SourceSystem']}")

# demonstrates the open_define context manager
print("\n\n=== Define context demo ===")
define_source = "./data/defineV21-SDTM.xml"
define_output = os.path.join("data", "define_context_output.xml")

with open_define(define_source, output_file=define_output) as define:
    mdv = define.Study.MetaDataVersion
    print(f"Define-XML loaded: FileOID={define.FileOID}")
    print(f"  MetaDataVersion: {mdv.OID} ({mdv.Name})")
    print(f"  ItemGroupDefs:   {len(mdv.ItemGroupDef)}")
    print(f"  ItemDefs:        {len(mdv.ItemDef)}")
    print(f"  CodeLists:       {len(mdv.CodeList)}")

    # List the dataset names
    for igd in mdv.ItemGroupDef:
        print(f"    - {igd.Name} ({igd.OID})")

print(f"\nDefine-XML saved to {os.path.basename(define_output)}")