"""
odm132-odm-builder.py  --  odmlib v0.2.0 ODMBuilder, the complete tour.

The v0.2.0 ``ODMBuilder`` (odmlib.builder) was expanded so it can build *every*
ODM v1.3.2 study-metadata element. Where ``v0-2-snippets/fluid_api.py`` shows
the basics (file, study, one item group, a code list), this snippet builds a
*complete, schema-valid* study-metadata document and exercises the whole
builder surface:

  set_file / add_study / add_measurement_unit / add_metadata_version /
  add_study_event_ref / add_study_event_def / add_form_ref / add_form_def /
  add_item_group_ref / add_item_group_def / add_item_ref / add_item_def /
  add_code_list / add_condition_def / add_method_def
  with_description / with_question / with_codelist_ref /
  with_measurement_unit_ref / with_range_check / with_alias
  attach / attach_to_current / current   (the escape hatch)

The escape hatch (``attach`` / ``attach_to_current``) is the v0.2.0 answer to
"what about the elements that have no dedicated add_*/with_* method?". A handful
of ODM 1.3.2 metadata elements -- Include, ArchiveLayout, ExternalQuestion,
RangeCheck/ErrorMessage, ExternalCodeList, Presentation, and element-level
Description/Alias on Protocol/StudyEventDef/FormDef/CodeList -- are attached
that way here, so the resulting document genuinely covers the metadata model.

After building, the document is:
  1. written to XML,
  2. schema-validated against the bundled ODM 1.3.2 XSD,
  3. OID ref/def checked (with an unreferenced-OID report), and
  4. round-tripped: reloaded with odmlib.open_odm() and re-validated.

Run:  python odm132-odm-builder.py
"""
import datetime
import os

from odmlib import open_odm, create_oid_checker, OdmlibError
from odmlib import odm_parser as P
from odmlib.builder import ODMBuilder
import odmlib.odm_1_3_2.model as M

OUTPUT_FILE = os.path.join("data", "odm132_complete.xml")
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# 1. Build the document with the fluent ODMBuilder
# ---------------------------------------------------------------------------
builder = ODMBuilder("odm_1_3_2")  # "odm_1_3_2" is also the default

# --- File + Study + BasicDefinitions ---------------------------------------
(
    builder
    .set_file(
        FileOID="ODM.VS.001",
        FileType="Snapshot",
        Granularity="Metadata",
        CreationDateTime=NOW,
        ODMVersion="1.3.2",
        Originator="odmlib ODMBuilder demo",
        SourceSystem="odmlib",
        SourceSystemVersion="0.2.0",
        Description="Complete ODM 1.3.2 study-metadata example",
    )
    .add_study(
        OID="S.ODM.001",
        study_name="Vital Signs Study",
        study_description="A small but complete CRF metadata example",
        protocol_name="VS-PROTOCOL-001",
    )
    # BasicDefinitions / MeasurementUnit (creates BasicDefinitions on demand)
    .add_measurement_unit(OID="MU.YR", Name="years", symbol="years")
    .add_measurement_unit(OID="MU.KG", Name="kilograms", symbol="kg")
    .add_measurement_unit(OID="MU.CM", Name="centimeters", symbol="cm")
)

# --- A prior MetaDataVersion, so Include has a real target -----------------
# Include references a previously-defined MetaDataVersion. We add a minimal
# baseline version first so the cross-reference resolves during OID checking.
builder.add_metadata_version(OID="MDV.ODM.PRIOR", Name="Baseline v0.9")

# --- The main MetaDataVersion ----------------------------------------------
builder.add_metadata_version(OID="MDV.ODM.001", Name="Study Metadata v1.0")
# MetaDataVersion.Description is a plain string attribute in ODM 1.3.2;
# with_description() handles that model-shape difference for us.
builder.with_description("First production metadata version for VS-PROTOCOL-001")

mdv = builder.current["mdv"]

# Include -> no dedicated method, use the attach() escape hatch.
builder.attach(mdv, M.Include(StudyOID="S.ODM.001",
                              MetaDataVersionOID="MDV.ODM.PRIOR"))

# --- Protocol + StudyEventRefs ---------------------------------------------
# add_study_event_ref() creates the Protocol element on first call.
builder.add_study_event_ref(StudyEventOID="SE.SCREEN", Mandatory="Yes",
                            OrderNumber=1)
builder.add_study_event_ref(StudyEventOID="SE.VISIT", Mandatory="Yes",
                            OrderNumber=2)
# Protocol.Description / Protocol.Alias have no add_* helper -> attach().
protocol = mdv.Protocol
builder.attach(protocol, M.Description(TranslatedText=[
    M.TranslatedText(_content="Screening followed by repeating visits",
                     lang="en")]))
builder.attach(protocol, M.Alias(Context="ClinicalTrials.gov",
                                 Name="NCT00000000"))

# --- StudyEventDefs + FormRefs ---------------------------------------------
builder.add_study_event_def(OID="SE.SCREEN", Name="Screening",
                            Repeating="No", Type="Scheduled")
builder.attach(builder.current["study_event_def"], M.Description(
    TranslatedText=[M.TranslatedText(_content="Screening visit", lang="en")]))
builder.add_form_ref(FormOID="F.DM", Mandatory="Yes", OrderNumber=1)
builder.add_form_ref(FormOID="F.VS", Mandatory="Yes", OrderNumber=2)
builder.attach(builder.current["study_event_def"],
               M.Alias(Context="SDTM", Name="SCREENING"))

builder.add_study_event_def(OID="SE.VISIT", Name="Treatment Visit",
                            Repeating="Yes", Type="Scheduled")
builder.add_form_ref(FormOID="F.VS", Mandatory="Yes", OrderNumber=1)

# --- FormDefs + ItemGroupRefs ----------------------------------------------
builder.add_form_def(OID="F.DM", Name="Demographics", Repeating="No")
builder.attach(builder.current["form_def"], M.Description(TranslatedText=[
    M.TranslatedText(_content="Demographics CRF", lang="en")]))
builder.add_item_group_ref(ItemGroupOID="IG.DM", Mandatory="Yes",
                           OrderNumber=1)
# ArchiveLayout (PDF archival layout) -> attach(); references Presentation P.DM.
builder.attach(builder.current["form_def"], M.ArchiveLayout(
    OID="AL.DM", PdfFileName="dm.pdf", PresentationOID="P.DM"))
builder.attach(builder.current["form_def"],
               M.Alias(Context="CDASH", Name="DM"))

builder.add_form_def(OID="F.VS", Name="Vital Signs", Repeating="Yes")
# Skip the VS item group when condition C.VSSKIP evaluates true.
builder.add_item_group_ref(ItemGroupOID="IG.VS", Mandatory="Yes",
                           OrderNumber=1,
                           CollectionExceptionConditionOID="C.VSSKIP")

# --- ItemGroupDefs + ItemRefs ----------------------------------------------
builder.add_item_group_def(OID="IG.DM", Name="DM", Repeating="No",
                           Domain="DM", SASDatasetName="DM",
                           Purpose="Tabulation")
builder.with_description("One record per subject")          # -> ItemGroupDef
builder.with_alias("SDTM", "DM")                            # -> ItemGroupDef
builder.add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes", OrderNumber=1,
                     KeySequence=1, Role="Identifier")
builder.add_item_ref(ItemOID="IT.AGE", Mandatory="No", OrderNumber=2)
builder.add_item_ref(ItemOID="IT.SEX", Mandatory="No", OrderNumber=3)
builder.add_item_ref(ItemOID="IT.RACE", Mandatory="No", OrderNumber=4)

builder.add_item_group_def(OID="IG.VS", Name="VS", Repeating="Yes",
                           Domain="VS", SASDatasetName="VS",
                           Purpose="Tabulation")
builder.with_description("One record per vital sign measurement per subject")
builder.add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes", OrderNumber=1,
                     KeySequence=1, Role="Identifier")
builder.add_item_ref(ItemOID="IT.VSTESTCD", Mandatory="Yes", OrderNumber=2)
builder.add_item_ref(ItemOID="IT.VSORRES", Mandatory="No", OrderNumber=3)
# A derived item -- MethodOID references MethodDef M.DERIVE.
builder.add_item_ref(ItemOID="IT.WEIGHT", Mandatory="No", OrderNumber=4,
                     MethodOID="M.DERIVE")
builder.add_item_ref(ItemOID="IT.HEIGHT", Mandatory="No", OrderNumber=5)

# --- ItemDefs (+ enrichers) ------------------------------------------------
builder.add_item_def(OID="IT.SUBJID", Name="SUBJID", DataType="text",
                     Length=10, SDSVarName="SUBJID")
builder.with_description("Unique subject identifier")
builder.with_question("Subject ID")
builder.with_alias("SDTM", "SUBJID")

builder.add_item_def(OID="IT.AGE", Name="AGE", DataType="integer",
                     Length=3, SignificantDigits=0, SDSVarName="AGE")
builder.with_description("Age in years at informed consent")
builder.with_question("Age")
builder.with_measurement_unit_ref("MU.YR")
# RangeCheck with a soft lower bound and an error message. (ODM 1.3.2 makes
# CheckValue and FormalExpression a *choice* inside RangeCheck -- the formal
# expression form is demonstrated on ConditionDef/MethodDef below instead.)
builder.with_range_check(
    "GE", [18], soft_hard="Soft",
    ErrorMessage=M.ErrorMessage(TranslatedText=[
        M.TranslatedText(_content="Subject is under 18", lang="en")]),
)
builder.with_alias("SDTM", "AGE")

builder.add_item_def(OID="IT.SEX", Name="SEX", DataType="text",
                     Length=1, SDSVarName="SEX")
builder.with_question("Sex")
builder.with_codelist_ref("CL.SEX")
builder.with_alias("SDTM", "SEX")

builder.add_item_def(OID="IT.RACE", Name="RACE", DataType="text",
                     Length=40, SDSVarName="RACE")
builder.with_question("Race")
builder.with_codelist_ref("CL.RACE")  # CL.RACE is an ExternalCodeList

builder.add_item_def(OID="IT.VSTESTCD", Name="VSTESTCD", DataType="text",
                     Length=8, SDSVarName="VSTESTCD")
builder.with_codelist_ref("CL.VSTESTCD")  # CL.VSTESTCD uses EnumeratedItems

builder.add_item_def(OID="IT.VSORRES", Name="VSORRES", DataType="text",
                     Length=20, SDSVarName="VSORRES")
# ExternalQuestion -> no dedicated method, attach() to the current ItemDef.
builder.attach(builder.current["item_def"], M.ExternalQuestion(
    Dictionary="LOINC", Version="2.76", Code="8716-3"))

builder.add_item_def(OID="IT.WEIGHT", Name="WEIGHT", DataType="float",
                     Length=6, SignificantDigits=2, SDSVarName="VSSTRESN")
builder.with_description("Body weight")
builder.with_measurement_unit_ref("MU.KG")
builder.with_range_check("GT", [0], soft_hard="Hard")

builder.add_item_def(OID="IT.HEIGHT", Name="HEIGHT", DataType="float",
                     Length=6, SignificantDigits=2, SDSVarName="VSSTRESN")
builder.with_description("Body height")
builder.with_measurement_unit_ref("MU.CM")

# --- CodeLists -------------------------------------------------------------
# CodeListItem form (CodedValue + Decode) via the items= argument.
builder.add_code_list(
    OID="CL.SEX", Name="Sex", DataType="text",
    items=[
        {"CodedValue": "M", "Decode": "Male"},
        {"CodedValue": "F", "Decode": "Female"},
    ],
)
# CodeList-level Description and Alias have no helper -> attach() to the
# CodeList we just appended.
cl_sex = mdv.CodeList[-1]
builder.attach(cl_sex, M.Description(TranslatedText=[
    M.TranslatedText(_content="Sex of the subject", lang="en")]))
builder.attach(cl_sex, M.Alias(Context="nci:ExtCodeID", Name="C66731"))

# EnumeratedItem form (CodedValue only -- omit "Decode").
builder.add_code_list(
    OID="CL.VSTESTCD", Name="Vital Signs Test Code", DataType="text",
    items=[
        {"CodedValue": "SYSBP"},
        {"CodedValue": "DIABP"},
        {"CodedValue": "PULSE"},
        {"CodedValue": "WEIGHT"},
        {"CodedValue": "HEIGHT"},
    ],
)

# ExternalCodeList form -- create an empty CodeList then attach the
# ExternalCodeList reference.
builder.add_code_list(OID="CL.RACE", Name="Race", DataType="text")
builder.attach(mdv.CodeList[-1], M.ExternalCodeList(
    Dictionary="CDISC", Version="2024-12-13"))

# --- ConditionDef + MethodDef ----------------------------------------------
builder.add_condition_def(
    OID="C.VSSKIP", Name="Skip Vital Signs",
    description="Skip the vital signs group for screen failures",
    formal_expression="SCREENFAIL == True",
    expression_context="Python",
)
builder.add_method_def(
    OID="M.DERIVE", Name="Derive Weight in kg", Type="Computation",
    description="Convert collected weight to kilograms",
    formal_expression="WEIGHT_KG = WEIGHT_LB * 0.453592",
    expression_context="Python",
)

# --- Presentation (referenced by ArchiveLayout.PresentationOID) ------------
# Presentation lives on MetaDataVersion; no dedicated method -> attach().
builder.attach(mdv, M.Presentation(
    OID="P.DM", _content="Demographics print layout"))

odm = builder.build()

print("Built ODM document with the fluent ODMBuilder")
m = odm.Study[0].MetaDataVersion[1]
print(f"  FileOID:          {odm.FileOID}")
print(f"  Study:            {odm.Study[0].OID} "
      f"({odm.Study[0].GlobalVariables.StudyName})")
print(f"  MeasurementUnits: "
      f"{len(odm.Study[0].BasicDefinitions.MeasurementUnit)}")
print(f"  MetaDataVersions: {len(odm.Study[0].MetaDataVersion)}")
print(f"  StudyEventDefs:   {len(m.StudyEventDef)}")
print(f"  FormDefs:         {len(m.FormDef)}")
print(f"  ItemGroupDefs:    {len(m.ItemGroupDef)}")
print(f"  ItemDefs:         {len(m.ItemDef)}")
print(f"  CodeLists:        {len(m.CodeList)}")
print(f"  ConditionDefs:    {len(m.ConditionDef)}")
print(f"  MethodDefs:       {len(m.MethodDef)}")
print(f"  Presentations:    {len(m.Presentation)}")


# ---------------------------------------------------------------------------
# 2. Serialize to XML
# ---------------------------------------------------------------------------
odm.write_xml(OUTPUT_FILE)
size = os.path.getsize(OUTPUT_FILE)
print(f"\nWrote {OUTPUT_FILE} ({size} bytes)")


# ---------------------------------------------------------------------------
# 3. Schema-validate the written file against the bundled ODM 1.3.2 XSD
# ---------------------------------------------------------------------------
validator = P.ODMSchemaValidator(standard="odm", version="1.3.2")
schema_errors = list(validator.xsd.iter_errors(OUTPUT_FILE))
if schema_errors:
    print(f"\nSchema validation FAILED with {len(schema_errors)} error(s):")
    for i, err in enumerate(schema_errors, 1):
        print(f"  {i}. {err.reason}  (path: {err.path})")
else:
    print("\nSchema validation passed (ODM 1.3.2 XSD)")


# ---------------------------------------------------------------------------
# 4. OID ref/def integrity check + unreferenced-OID report
# ---------------------------------------------------------------------------
checker = create_oid_checker("odm_1_3_2")
try:
    odm.verify_oids(checker)
    print("OID ref/def check passed (every *OID reference resolves)")
except OdmlibError as exc:
    print(f"OID ref/def check FAILED: {exc}")

# unreferenced_oids() reports definitions nothing points at. Some are
# definition-only by design: an ArchiveLayout OID is never referenced, and
# the *active* MetaDataVersion is referenced only by prior versions (here
# MDV.ODM.PRIOR is referenced by Include, MDV.ODM.001 is not) -- so a
# non-empty list here is informational, not an error.
orphans = odm.unreferenced_oids(checker)
if orphans:
    print(f"Defined-but-unreferenced OIDs ({len(orphans)}, expected: "
          f"ArchiveLayout + active MDV): {', '.join(sorted(orphans))}")
else:
    print("Every defined OID is referenced somewhere")


# ---------------------------------------------------------------------------
# 5. Round-trip: reload with open_odm() and re-validate
# ---------------------------------------------------------------------------
with open_odm(OUTPUT_FILE) as reloaded:
    rt_errors = reloaded.validate(collect_errors=True,
                                  oid_checker=create_oid_checker("odm_1_3_2"))
    rt_mdv = reloaded.Study[0].MetaDataVersion[1]
    same_file = reloaded.FileOID == odm.FileOID
    same_items = len(rt_mdv.ItemDef) == len(m.ItemDef)

print("\nRound-trip via open_odm():")
print(f"  FileOID preserved: {same_file} ({reloaded.FileOID})")
print(f"  ItemDef count preserved: {same_items} "
      f"({len(rt_mdv.ItemDef)} ItemDefs)")
if rt_errors:
    print(f"  Reloaded-document validation found {len(rt_errors)} issue(s):")
    for i, err in enumerate(rt_errors, 1):
        print(f"    {i}. [{type(err).__name__}] {err}")
else:
    print("  Reloaded document validates clean "
          "(element order + OID ref/def)")