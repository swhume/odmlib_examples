"""
This odmlib v0.2.0 snippet demonstrates the ARM (Analysis Results Metadata) 1.0
extension model, odmlib.arm_1_0, which extends Define-XML v2.1 with elements that
describe analysis results, result displays, programming code, and analysis
datasets (used in ADaM Define-XML documents). It shows how to:

  1. read an ARM-extended ADaM Define-XML file with the XMLArmLoader,
  2. traverse the ARM-specific objects (AnalysisResultDisplays / ResultDisplay /
     AnalysisResult / AnalysisDatasets / ProgrammingCode / Documentation),
  3. build a new ResultDisplay with the arm_1_0 model classes and append it,
  4. write the extended document back out as Define-XML, then read it back, and
  5. validate the generated file.

Validation note: odmlib does NOT bundle an ARM XSD -- the packaged Define-XML
v2.1 schema does not declare the arm: namespace, so it cannot schema-validate
ARM elements. This snippet therefore always runs odmlib's built-in
object-model + OID-reference validation (no schema files needed), and
additionally runs XSD validation only if you point the ARM_XSD environment
variable at a real ARM-aware schema (e.g. the CDISC define2-1-0.xsd packaged
together with arm1-0-0.xsd).
"""
import os
import odmlib.arm_loader as AL
import odmlib.loader as LD
import odmlib.arm_1_0.model as ARM
from odmlib import create_oid_checker, OdmlibError
from odmlib.odm_parser import ODMSchemaValidator

INPUT_FILE = "data/definev21-adam.xml"
OUTPUT_FILE = "data/arm-roundtrip-define.xml"
# Point ARM_XSD at a real ARM-aware Define-XML v2.1 schema to enable the XSD
# step; leave it unset to skip it (odmlib does not ship an ARM schema).
ARM_XSD = os.environ.get("ARM_XSD")  # e.g. "/path/to/cdisc-arm-1.0/define2-1-0.xsd"

# --- 1. read the ARM-extended ADaM Define-XML -------------------------------
# the XMLArmLoader understands the arm: namespace; it is used through the same
# ODMLoader facade as the ODM and Define-XML loaders
loader = LD.ODMLoader(AL.XMLArmLoader(model_package="arm_1_0",
                                      ns_uri="http://www.cdisc.org/ns/arm/v1.0"))
loader.open_odm_document(INPUT_FILE)
odm = loader.root()
mdv = odm.Study.MetaDataVersion
print(f"Loaded {odm.FileOID}")
print(f"  Study           : {odm.Study.OID}")
print(f"  MetaDataVersion : {mdv.OID} ({mdv.Name})")

# --- 2. traverse the ARM-specific objects -----------------------------------
# AnalysisResultDisplays is the ARM container added to MetaDataVersion; it
# supports len()/indexing/iteration over its ResultDisplay children
ard = mdv.AnalysisResultDisplays
print(f"\nAnalysisResultDisplays: {len(ard)} ResultDisplay element(s)")
for rd in ard:
    print(f"\n  ResultDisplay {rd.OID} - {rd.Name}")
    if rd.Description and rd.Description.TranslatedText:
        print(f"    Description : {rd.Description.TranslatedText[0]._content}")
    for ar in rd.AnalysisResult:
        print(f"    AnalysisResult {ar.OID}")
        print(f"      Reason  : {ar.AnalysisReason}")
        print(f"      Purpose : {ar.AnalysisPurpose}")
        if ar.AnalysisDatasets:
            for ds in ar.AnalysisDatasets.AnalysisDataset:
                used = ", ".join(v.ItemOID for v in ds.AnalysisVariable)
                print(f"      Dataset : {ds.ItemGroupOID} -> [{used}]")
        if ar.ProgrammingCode:
            has_code = ar.ProgrammingCode.Code is not None
            print(f"      Code    : context={ar.ProgrammingCode.Context!r} "
                  f"present={'yes' if has_code else 'no'}")

# --- 3. build a new ResultDisplay with the arm_1_0 model classes ------------
# reuse an existing ItemGroupDef and one of its ItemDef references so the new
# OID references resolve during validation
ig = mdv.ItemGroupDef[0]
analysis_item_oid = ig.ItemRef[1].ItemOID

new_rd = ARM.ResultDisplay(
    OID="RD.EXAMPLE.01",
    Name="Example Display - added with the arm_1_0 model",
    Description=ARM.Description(TranslatedText=[
        ARM.TranslatedText(_content="Result display created programmatically "
                                    "with odmlib.arm_1_0", lang="en")]),
    AnalysisResult=[
        ARM.AnalysisResult(
            OID="AR.EXAMPLE.01.R.1",
            ParameterOID=analysis_item_oid,
            AnalysisReason="SPECIFIED IN SAP",
            AnalysisPurpose="PRIMARY OUTCOME MEASURE",
            Description=ARM.Description(TranslatedText=[
                ARM.TranslatedText(_content="Example analysis result built "
                                            "with the ARM model", lang="en")]),
            AnalysisDatasets=ARM.AnalysisDatasets(AnalysisDataset=[
                ARM.AnalysisDataset(
                    ItemGroupOID=ig.OID,
                    AnalysisVariable=[ARM.AnalysisVariable(ItemOID=analysis_item_oid)],
                )]),
            Documentation=ARM.Documentation(Description=ARM.Description(
                TranslatedText=[ARM.TranslatedText(
                    _content="See SAP section for the example analysis.",
                    lang="en")])),
            ProgrammingCode=ARM.ProgrammingCode(
                Context="SAS version 9.4",
                Code=ARM.Code(_content="proc means data=ADSL; run;")),
        )],
)
ard.ResultDisplay.append(new_rd)
print(f"\nAppended ResultDisplay {new_rd.OID}; "
      f"AnalysisResultDisplays now has {len(ard)} display(s)")

# --- 4. write the extended document back out, then read it back -------------
odm.write_xml(OUTPUT_FILE)
print(f"\nWrote extended ARM Define-XML to {OUTPUT_FILE}")

reloader = LD.ODMLoader(AL.XMLArmLoader())
reloader.open_odm_document(OUTPUT_FILE)
rt = reloader.root()
rt_ard = rt.Study.MetaDataVersion.AnalysisResultDisplays
print(f"Re-read {OUTPUT_FILE}: {len(rt_ard)} ResultDisplay element(s)")
added = rt_ard.find("ResultDisplay", "OID", "RD.EXAMPLE.01")
print(f"  round-tripped new display: {added.OID} - {added.Name}")
print(f"  round-tripped new result : {added.AnalysisResult[0].OID}")

# --- 5. validate the generated file -----------------------------------------
# 5a. always: odmlib object-model + OID-reference validation (no schema needed).
#     collect_errors=True reports every finding instead of raising on the first.
checker = create_oid_checker("arm_1_0")
errors = rt.validate(collect_errors=True, oid_checker=checker)
if errors:
    print(f"\nodmlib object/OID validation found {len(errors)} finding(s):")
    for i, err in enumerate(errors, 1):
        print(f"  {i}. [{type(err).__name__}] {err}")
    # NOTE: a ProgrammingCode ordering finding here originates in the CDISC
    # ADaM sample (a ProgrammingCode that carries only a DocumentRef and no
    # Code), not in the ResultDisplay this snippet added.
else:
    print("\nodmlib object/OID validation: OK")

# 5b. optional: XSD validation against a real ARM-aware schema
if ARM_XSD:
    validator = ODMSchemaValidator(xsd_file=ARM_XSD)
    try:
        validator.validate_file(OUTPUT_FILE)
    except OdmlibError as e:  # XSD + OID + conformance + element-order
        print(f"\nARM XSD validation error: {e}")
    else:
        print(f"\nARM XSD validation ({ARM_XSD}): OK")
else:
    print("\nARM XSD validation skipped: odmlib does not bundle an ARM schema. "
          "Set the ARM_XSD env var to a real ARM-aware Define-XML v2.1 schema "
          "(define2-1-0.xsd packaged with arm1-0-0.xsd) to enable this step.")
