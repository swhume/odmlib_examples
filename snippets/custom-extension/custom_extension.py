"""
custom_extension.py

Load an ODM document that uses a custom vendor namespace with a LOCAL odmlib extension model,
read the extension attribute, add another extended ItemDef in code, and round-trip the result.

The extension model lives in ./acme_odm_1_0/ (see acme_odm_1_0/model.py). The key loader option
is `local_model=True`, which tells odmlib to import the model package by name from the current
working directory instead of from inside odmlib itself.

Run from this directory:

    cd custom-extension
    python custom_extension.py
"""
import os
import odmlib.odm_loader as OL
import odmlib.loader as LD
import acme_odm_1_0.model as ACME

ODM_NS = "http://www.cdisc.org/ns/odm/v1.3"
SRC = os.path.join("data", "acme-odm.xml")
OUT = os.path.join("data", "acme-odm-roundtrip.xml")


def main():
    # --- 1. load the extended document with the local model -------------------------------
    loader = LD.ODMLoader(
        OL.XMLODMLoader(model_package="acme_odm_1_0", ns_uri=ODM_NS, local_model=True)
    )
    loader.open_odm_document(SRC)
    odm = loader.root()
    mdv = odm.Study[0].MetaDataVersion[0]

    print(f"Loaded {os.path.basename(SRC)} with the acme_odm_1_0 extension model")
    print("ItemDefs and their acme:Label extension attribute:")
    for itd in mdv.ItemDef:
        print(f"  {itd.OID}: Name={itd.Name!r}, acme:Label={itd.Label!r}")

    # --- 2. add another extended ItemDef in code ------------------------------------------
    new_item = ACME.ItemDef(OID="ACME.IT.RACE", Name="RACE", DataType="text", Label="Race")
    mdv.ItemDef.append(new_item)
    print(f"\nAdded {new_item.OID} with acme:Label={new_item.Label!r}")

    # --- 3. round-trip: write back out, then reload and confirm ---------------------------
    odm.write_xml(OUT)
    print(f"Wrote {os.path.basename(OUT)}")

    reloader = LD.ODMLoader(
        OL.XMLODMLoader(model_package="acme_odm_1_0", ns_uri=ODM_NS, local_model=True)
    )
    reloader.open_odm_document(OUT)
    rt_mdv = reloader.root().Study[0].MetaDataVersion[0]
    race = next((i for i in rt_mdv.ItemDef if i.OID == "ACME.IT.RACE"), None)
    print(f"\nRound-trip confirmed: {len(rt_mdv.ItemDef)} ItemDefs; "
          f"ACME.IT.RACE acme:Label={race.Label!r}")


if __name__ == "__main__":
    main()
