import datetime
import os
from odmlib.builder import ODMBuilder

current_datetime = datetime.datetime.now(datetime.timezone.utc).isoformat()

odm_fluid = (
    ODMBuilder()
    .set_file(
        FileOID="F.DM.FLUID",
        FileType="Snapshot",
        CreationDateTime=current_datetime,
        ODMVersion="1.3.2",
        Originator="odmlib",
        SourceSystem="odmlib",
        SourceSystemVersion="0.2.0",
    )
    .add_study(
        OID="S.DM.001",
        study_name="Demographics Study",
        study_description="A simple demographics example",
        protocol_name="DM-001",
    )
    .add_metadata_version(OID="MDV.DM.001", Name="Demographics v1")
    .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
    .add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes", OrderNumber=1)
    .add_item_ref(ItemOID="IT.AGE", Mandatory="No", OrderNumber=2)
    .add_item_ref(ItemOID="IT.SEX", Mandatory="No", OrderNumber=3)
    .add_item_def(OID="IT.SUBJID", Name="SUBJID", DataType="text", Length=20)
    .add_item_def(OID="IT.AGE", Name="AGE", DataType="integer", Length=3)
    .add_item_def(OID="IT.SEX", Name="SEX", DataType="text", Length=1)
    .add_code_list(
        OID="CL.SEX", Name="Sex", DataType="text",
        items=[
            {"CodedValue": "M", "Decode": "Male"},
            {"CodedValue": "F", "Decode": "Female"},
        ],
    )
    .build()
)

print(f"Fluid API: created ODM with FileOID={odm_fluid.FileOID}")
print(f"  Study OID:   {odm_fluid.Study[0].OID}")
print(f"  Datasets:    {len(odm_fluid.Study[0].MetaDataVersion[0].ItemGroupDef)}")
print(f"  Variables:   {len(odm_fluid.Study[0].MetaDataVersion[0].ItemDef)}")
print(f"  CodeLists:   {len(odm_fluid.Study[0].MetaDataVersion[0].CodeList)}")

# the builder result is a standard odmlib ODM object
print(f"\nType: {type(odm_fluid).__module__}.{type(odm_fluid).__name__}")

# serialize to XML and write to a temp file
xml_file = os.path.join("data", "fluid_demo.xml")
odm_fluid.write_xml(xml_file)

with open(xml_file) as f:
    xml_text = f.read()
print(f"\nXML file written ({len(xml_text)} characters). First 300 characters:")
print(xml_text[:500] + "...")


"""
The `with_description()` helper attaches a `Description` element to the most recently created component. It 
targets the last `ItemDef` if one was just added, otherwise the last `ItemGroupDef`, otherwise the current 
`MetaDataVersion`.
"""
odm_desc = (
    ODMBuilder()
    .set_file(FileOID="F.DESC", FileType="Snapshot", CreationDateTime=current_datetime)
    .add_study(
        OID="S.DESC",
        study_name="Description Demo",
        study_description="Demonstrating with_description()",
        protocol_name="DESC-001",
    )
    .add_metadata_version(OID="MDV.DESC", Name="Descriptions v1")
    .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
    .with_description("One record per subject containing demographic variables")
    .add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes", OrderNumber=1)
    .add_item_ref(ItemOID="IT.AGE", Mandatory="No", OrderNumber=2)
    .add_item_def(OID="IT.SUBJID", Name="SUBJID", DataType="text", Length=20)
    .with_description("Unique subject identifier within the study")
    .add_item_def(OID="IT.AGE", Name="AGE", DataType="integer", Length=3)
    .with_description("Age of the subject in years at time of informed consent")
    .build()
)

mdv = odm_desc.Study[0].MetaDataVersion[0]

# Description on the ItemGroupDef
igd_desc = mdv.ItemGroupDef[0].Description.TranslatedText[0]._content
print(f"ItemGroupDef IG.DM description: {igd_desc}")

# Descriptions on the ItemDefs
for item in mdv.ItemDef:
    desc_text = item.Description.TranslatedText[0]._content
    print(f"ItemDef {item.OID} description: {desc_text}")

"""
Multiple Datasets and Context Switching
When you call `add_item_group_def()` a second time, the builder updates its internal pointer. Subsequent 
`add_item_ref()` calls target the new dataset. This makes it straightforward to define multi-dataset studies in a 
single chain.
"""
odm_multi = (
    ODMBuilder()
    .set_file(FileOID="F.MULTI", FileType="Snapshot", CreationDateTime=current_datetime)
    .add_study(
        OID="S.MULTI",
        study_name="Multi-Dataset Study",
        study_description="Two domains in one builder chain",
        protocol_name="MULTI-001",
    )
    .add_metadata_version(OID="MDV.MULTI", Name="Multi-Dataset v1")
    # --- Demographics dataset ---
    .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
    .add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes", OrderNumber=1)
    .add_item_ref(ItemOID="IT.AGE", Mandatory="No", OrderNumber=2)
    # --- Vital Signs dataset (builder switches context here) ---
    .add_item_group_def(OID="IG.VS", Name="Vital Signs", Repeating="Yes")
    .add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes", OrderNumber=1)
    .add_item_ref(ItemOID="IT.VSTESTCD", Mandatory="Yes", OrderNumber=2)
    .add_item_ref(ItemOID="IT.VSSTRESN", Mandatory="No", OrderNumber=3)
    # --- ItemDefs (shared across datasets, added to MetaDataVersion) ---
    .add_item_def(OID="IT.SUBJID", Name="SUBJID", DataType="text", Length=20)
    .add_item_def(OID="IT.AGE", Name="AGE", DataType="integer", Length=3)
    .add_item_def(OID="IT.VSTESTCD", Name="VSTESTCD", DataType="text", Length=8)
    .add_item_def(OID="IT.VSSTRESN", Name="VSSTRESN", DataType="float", Length=8)
    .build()
)

mdv = odm_multi.Study[0].MetaDataVersion[0]
for igd in mdv.ItemGroupDef:
    refs = [r.ItemOID for r in igd.ItemRef]
    print(f"  {igd.Name} ({igd.OID}): {len(igd.ItemRef)} refs -> {refs}")