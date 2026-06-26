"""
modify-existing-document.py

A very common real-world task: load an existing Define-XML document, change it (update an
attribute, add a new definition, remove one), and write it back out -- a read -> modify -> write
round-trip.

This snippet shows:
  - loading with the `open_define` context manager (auto-writes to output_file on a clean exit)
  - locating an element by OID with `MetaDataVersion.find(...)`
  - UPDATE: renaming an existing ItemDef
  - ADD:    appending a new ItemDef
  - REMOVE: dropping an ItemDef from the collection
  - reloading the written file to confirm the changes persisted
"""
import os
import odmlib.define_2_1.model as DEFINE
from odmlib.context import open_define

SRC = os.path.join("data", "defineV21-SDTM.xml")
OUT = os.path.join("data", "modified-define.xml")

UPDATE_OID = "IT.DM.AGE"     # existing ItemDef to rename
REMOVE_OID = "IT.DM.AGEU"    # existing ItemDef to delete
NEW_OID = "IT.DM.NEWVAR"     # ItemDef to add


def main():
    # --- read + modify (auto-written to OUT when the with-block exits cleanly) -------------
    with open_define(SRC, output_file=OUT) as define:
        mdv = define.Study.MetaDataVersion
        start_count = len(mdv.ItemDef)
        print(f"Loaded {os.path.basename(SRC)}: {start_count} ItemDefs")

        # UPDATE: find an ItemDef by OID and rename it
        age = mdv.find("ItemDef", "OID", UPDATE_OID)
        print(f"  update: {age.OID} Name {age.Name!r} -> 'AGE (years)'")
        age.Name = "AGE (years)"

        # ADD: append a new ItemDef
        mdv.ItemDef.append(DEFINE.ItemDef(OID=NEW_OID, Name="New Variable", DataType="text"))
        print(f"  add:    {NEW_OID}")

        # REMOVE: drop an ItemDef from the collection
        mdv.ItemDef = [it for it in mdv.ItemDef if it.OID != REMOVE_OID]
        print(f"  remove: {REMOVE_OID}")

        print(f"ItemDef count after edits: {len(mdv.ItemDef)} (was {start_count})")

    print(f"\nWrote {os.path.basename(OUT)}")

    # --- reload the written file to confirm the changes persisted -------------------------
    with open_define(OUT, write_on_exit=False) as define:
        mdv = define.Study.MetaDataVersion
        renamed = mdv.find("ItemDef", "OID", UPDATE_OID)
        added = mdv.find("ItemDef", "OID", NEW_OID)
        removed = mdv.find("ItemDef", "OID", REMOVE_OID)
        print("\nConfirming round-trip:")
        print(f"  renamed {UPDATE_OID} -> Name = {renamed.Name!r}")
        print(f"  added   {NEW_OID} present = {added is not None}")
        print(f"  removed {REMOVE_OID} present = {removed is not None}")


if __name__ == "__main__":
    main()
