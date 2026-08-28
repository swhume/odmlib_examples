"""
odm20-odm-builder.py  --  odmlib v0.2.0 ODMBuilder for the ODM v2.0 model.

ODM v2.0 is structurally very different from ODM v1.3.2, and the v0.2.0
``ODMBuilder`` was expanded to drive the 2.0 model. This snippet builds a
*complete, schema-valid* ODM 2.0 study-metadata document, exercises the whole
builder surface, and validates + round-trips the result. It is the ODM 2.0
companion to ``odm132-odm-builder.py`` and goes well beyond ``fluid_api.py``.

What is different in ODM 2.0 (see data/vital_signs_odmv2-0.xml for the shape):

  * Study uses scalar ``StudyName`` / ``ProtocolName`` attributes and an
    object-valued ``Description`` (no ``GlobalVariables``).
  * ``MetaDataVersion.Description`` is object-valued (not a string attribute).
  * There is no ``FormDef`` / ``FormRef`` layer. Forms are modeled as
    *nested* ``ItemGroupDef`` elements with a ``Type`` of Form / Section /
    Concept, an ``ItemGroupDef`` referencing child groups via ``ItemGroupRef``.
  * ``StudyEventDef`` references ``ItemGroupRef`` directly.
  * New 2.0 metadata: ``Coding`` (biomedical-concept / dataset-specialization
    links), ``Prompt``, ``Definition``, ``Standards``/``Standard``,
    ``StudyStructure`` (Arm/Epoch), ``WorkflowDef`` (Transition), and
    ``MethodSignature``.
  * ``CodeList`` has only ``CodeListItem`` (no ``EnumeratedItem``); a value
    without a decode is a ``CodeListItem`` carrying only ``Coding``.
  * ``MetaDataVersion.Standards`` is a single container (``maxOccurs=1``);
    the repeating list is ``Standards.Standard``.

Honest scope note -- where odmlib's odm_2_0 model and the published ODM 2.0
XSD disagree, this example keeps the document *schema-valid* and documents
the gap rather than emitting invalid XML.

odmlib v0.2.0 closed the safe subset of these gaps, so the example no longer
needs its old workarounds: TranslatedText/@Type is now required and the
builder defaults it to 'text/plain' (the normalize_tt_type() post-pass is
gone); the duplicate odm_2_0 Arm/CheckValue classes were de-duplicated (the
model_cls() descriptor shim is gone); and ReturnValue.DataType now has an
odm_2_0 valueset entry. The remaining gaps are structural and deferred to
v0.2.1 (see ROADMAP "v0.2.1 -- ODM v2.0 Model/XSD Alignment" and
ODM20-MODEL-XSD-DIFFERENCES_PLAN.md §6); this example still routes around
them to stay schema-valid:

  * ConditionDef: the XSD requires a ``MethodSignature`` child, but the
    odmlib ConditionDef class has no such field, so a schema-valid
    ConditionDef cannot be produced -- it (and every
    ``CollectionExceptionConditionOID``) is omitted.
  * StudyTiming / StudyEventGroupDef: the odmlib model exposes these as
    direct MetaDataVersion children, but the XSD does not allow them there
    (timing lives under Protocol; a StudyEventGroupDef needs a
    StudyEvent(Group)Ref the model can't hold) -- omitted.
  * Protocol: the odmlib Protocol carries ``StudyEventRef``, which the 2.0
    schema removed, so Protocol is built with Description/StudyStructure/
    Alias only (no StudyEventRef; ``add_study_event_ref`` is not used).
  * FormalExpression: the 2.0 XSD makes it element-based (Code |
    ExternalCodeLib); the odmlib FormalExpression class is text-based, so
    no FormalExpression is emitted (MethodDef = Description + signature).
  * ItemDef: SDSVarName / FractionDigits exist on the odmlib class but not
    in the 2.0 XSD ItemDef, so they are not set.

Builder coverage:
  set_file / add_study / add_metadata_version / add_study_event_def /
  add_item_group_ref / add_item_group_def / add_item_ref / add_item_def /
  add_code_list / add_method_def / with_description / with_question /
  with_codelist_ref / with_alias / attach / current

The escape hatch (``attach`` + ``current``) is used for every 2.0 element
with no dedicated method: Include, Standards, Protocol/StudyStructure
(Arm/Epoch), WorkflowDef, Coding, Prompt, Definition,
CRFCompletionInstructions/ImplementationNotes/CDISCNotes, Origin, RangeCheck,
MethodSignature, nested ItemGroupRef, and element-level Description/Alias.

Run:  python odm20-odm-builder.py
"""
import datetime
import os

from odmlib import open_odm, create_oid_checker, OdmlibError
from odmlib import odm_parser as P
from odmlib.builder import ODMBuilder
import odmlib.odm_2_0.model as M

OUTPUT_FILE = os.path.join("data", "odm20_complete.xml")
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()


def tt(text, lang="en"):
    """A TranslatedText with the ODM 2.0 Type='text/plain' qualifier."""
    return M.TranslatedText(_content=text, lang=lang, Type="text/plain")


def desc(text):
    return M.Description(TranslatedText=[tt(text)])


# ---------------------------------------------------------------------------
# 1. Build the ODM 2.0 document with the fluent ODMBuilder
# ---------------------------------------------------------------------------
builder = ODMBuilder("odm_2_0")

(
    builder
    .set_file(
        FileOID="ODM.VS20.001",
        FileType="Snapshot",
        Granularity="Metadata",
        CreationDateTime=NOW,
        ODMVersion="2.0",
        Originator="odmlib ODMBuilder demo",
        SourceSystem="odmlib",
        SourceSystemVersion="0.2.0",
    )
    # ODM 2.0 Study: scalar StudyName/ProtocolName + object Description.
    .add_study(
        OID="S.VS20",
        study_name="Vital Signs Study",
        study_description="ODM 2.0 vital signs study-metadata example",
        protocol_name="VS20-PROTOCOL",
    )
)

# A minimal prior MetaDataVersion so Include resolves during OID checking.
builder.add_metadata_version(OID="MDV.PRIOR", Name="Baseline v0.9")

# The main MetaDataVersion. In ODM 2.0 the description is object-valued;
# with_description() builds the right shape automatically.
builder.add_metadata_version(OID="MDV.001", Name="Vital Signs Metadata v1.0")
builder.with_description("First production ODM 2.0 metadata version")
mdv = builder.current["mdv"]

# --- Include + Standards (escape hatch) ------------------------------------
builder.attach(mdv, M.Include(StudyOID="S.VS20",
                              MetaDataVersionOID="MDV.PRIOR"))
builder.attach(mdv, M.Standards(Standard=[
    M.Standard(OID="STD.SDTMIG", Name="SDTMIG", Type="IG", Version="3.4",
               Status="Final")]))

# --- Protocol (built directly; the 2.0 schema has no StudyEventRef) --------
builder.attach(mdv, M.Protocol(
    Description=desc("Screening followed by treatment visits"),
    StudyStructure=M.StudyStructure(
        Description=desc("One arm, two epochs"),
        Arm=[M.Arm(OID="ARM.A", Name="Treatment A",
                    Description=desc("Single treatment arm"),
                    WorkflowRef=M.WorkflowRef(WorkflowOID="WF.MAIN"))],
        Epoch=[
            M.Epoch(OID="EP.SCREEN", Name="Screening", SequenceNumber=1),
            M.Epoch(OID="EP.TREAT", Name="Treatment", SequenceNumber=2),
        ],
        WorkflowRef=[M.WorkflowRef(WorkflowOID="WF.MAIN")]),
    Alias=[M.Alias(Context="ClinicalTrials.gov", Name="NCT00000000")]))

# --- WorkflowDef (escape hatch) --------------------------------------------
builder.attach(mdv, M.WorkflowDef(
    OID="WF.MAIN", Name="Main Workflow",
    Description=desc("Screening to treatment workflow"),
    WorkflowStart=M.WorkflowStart(StartOID="SE.SCREEN"),
    Transition=[M.Transition(OID="T.1", Name="Screen to Visit",
                             SourceOID="SE.SCREEN", TargetOID="SE.VISIT")],
    WorkflowEnd=[M.WorkflowEnd(EndOID="SE.VISIT")]))

# --- StudyEventDefs (ItemGroupRef directly -- no FormDef in ODM 2.0) -------
builder.add_study_event_def(OID="SE.SCREEN", Name="Screening",
                            Repeating="No", Type="Scheduled")
builder.attach(builder.current["study_event_def"], desc("Screening visit"))
builder.add_item_group_ref(ItemGroupOID="IG.FORM.VS", Mandatory="Yes",
                           OrderNumber=1)
builder.attach(builder.current["study_event_def"],
               M.WorkflowRef(WorkflowOID="WF.MAIN"))
builder.attach(builder.current["study_event_def"],
               M.Alias(Context="SDTM", Name="SCREENING"))

builder.add_study_event_def(OID="SE.VISIT", Name="Treatment Visit",
                            Repeating="Yes", Type="Scheduled")
builder.add_item_group_ref(ItemGroupOID="IG.FORM.VS", Mandatory="Yes",
                           OrderNumber=1)

# --- Nested ItemGroupDef hierarchy: Form -> Section -> Concept -------------
# add_item_group_ref() always targets the current StudyEventDef in ODM 2.0,
# so the *nested* ItemGroupRefs (group-in-group) use the attach() hatch.
builder.add_item_group_def(OID="IG.FORM.VS", Name="Vital Signs Form",
                           Repeating="No", Type="Form",
                           StandardOID="STD.SDTMIG")
form_igd = builder.current["item_group_def"]
builder.with_description("Vital Signs CRF form")
builder.with_alias("formAnnotation", "DOMAIN = VS")
builder.attach(form_igd, M.ItemGroupRef(ItemGroupOID="IG.SEC.VS",
                                        Mandatory="Yes", OrderNumber=1))
builder.attach(form_igd, M.Coding(
    System="/mdr/bc/biomedicalconcepts/C82525", Code="C82525",
    SystemName="CDISC Biomedical Concept"))

builder.add_item_group_def(OID="IG.SEC.VS", Name="Vital Signs Section",
                           Repeating="No", Type="Section")
sec_igd = builder.current["item_group_def"]
builder.with_description("Vital Signs section")
builder.attach(sec_igd, M.ItemGroupRef(ItemGroupOID="IG.CON.SYSBP",
                                       Mandatory="Yes", OrderNumber=1))
builder.attach(sec_igd, M.ItemGroupRef(ItemGroupOID="IG.CON.WEIGHT",
                                       Mandatory="Yes", OrderNumber=2))

builder.add_item_group_def(OID="IG.CON.SYSBP",
                           Name="Systolic Blood Pressure (Concept)",
                           Repeating="No", Type="Concept")
sysbp_igd = builder.current["item_group_def"]
builder.with_description("Systolic blood pressure biomedical concept")
builder.add_item_ref(ItemOID="IT.VSDAT", Mandatory="No", OrderNumber=1)
builder.add_item_ref(ItemOID="IT.SYSBP", Mandatory="Yes", OrderNumber=2,
                     UnitsItemOID="IT.SYSBPU")
builder.add_item_ref(ItemOID="IT.SYSBPU", Mandatory="Yes", OrderNumber=3,
                     PreSpecifiedValue="mmHg")
builder.attach(sysbp_igd, M.Coding(
    System="/mdr/bc/biomedicalconcepts/C25298", Code="C25298",
    SystemName="CDISC Biomedical Concept"))
builder.attach(sysbp_igd, M.Coding(
    System="/mdr/specializations/sdtm/datasetspecializations/SYSBP",
    Code="SYSBP", SystemName="CDISC SDTM Dataset Specialization"))
builder.attach(sysbp_igd, M.Origin(Type="Collected",
                                   Description=desc("Collected on the CRF")))

builder.add_item_group_def(OID="IG.CON.WEIGHT", Name="Weight (Concept)",
                           Repeating="No", Type="Concept")
builder.add_item_ref(ItemOID="IT.VSDAT", Mandatory="No", OrderNumber=1)
builder.add_item_ref(ItemOID="IT.WEIGHT", Mandatory="Yes", OrderNumber=2,
                     MethodOID="M.DERIVE", Role="RESULT",
                     RoleCodeListOID="CL.NY")

# --- ItemDefs (+ enrichers and escape-hatch sub-elements) ------------------
builder.add_item_def(OID="IT.VSDAT", Name="VSDAT", DataType="date",
                     Length=10)
builder.with_description("Date of assessment")
builder.with_question("Date of Assessment")
builder.attach(builder.current["item_def"],
               M.Prompt(TranslatedText=[tt("Assessment date")]))
builder.attach(builder.current["item_def"],
               M.Definition(TranslatedText=[tt("The date the vital sign "
                                                "was measured")]))
builder.with_alias("SDTM", "VSDTC")
builder.attach(builder.current["item_def"], M.Coding(
    System="https://www.cdisc.org/standards/terminology", Code="C25164",
    SystemName="CDISC/NCI CT"))

builder.add_item_def(OID="IT.SYSBP", Name="SYSBP", DataType="integer",
                     Length=3)
builder.with_description("Systolic blood pressure result")
builder.with_question("Systolic Blood Pressure")
# RangeCheck attached through the escape hatch (no dedicated builder method).
builder.attach(builder.current["item_def"], M.RangeCheck(
    Comparator="GE", SoftHard="Soft",
    CheckValue=[M.CheckValue(_content="0")],
    ErrorMessage=M.ErrorMessage(TranslatedText=[tt("Value must be >= 0")])))
builder.attach(builder.current["item_def"],
               M.CRFCompletionInstructions(
                   TranslatedText=[tt("Record the measured value")]))
builder.attach(builder.current["item_def"],
               M.ImplementationNotes(
                   TranslatedText=[tt("Integer mmHg, no decimals")]))
builder.attach(builder.current["item_def"],
               M.CDISCNotes(TranslatedText=[tt("Maps to VSORRES/VSSTRESN")]))
builder.with_alias("SDTM", "VSORRES when VSTESTCD = SYSBP")

builder.add_item_def(OID="IT.SYSBPU", Name="SYSBPU", DataType="text",
                     Length=10)
builder.with_question("Systolic Blood Pressure Unit")
builder.with_codelist_ref("CL.UNIT")
builder.with_alias("SDTM", "VSORRESU when VSTESTCD = SYSBP")

builder.add_item_def(OID="IT.WEIGHT", Name="WEIGHT", DataType="decimal",
                     Length=6)
builder.with_description("Body weight (derived to kg)")
builder.attach(builder.current["item_def"],
               M.Prompt(TranslatedText=[tt("Weight")]))
builder.with_alias("SDTM", "VSORRES when VSTESTCD = WEIGHT")

# --- CodeLists (CodeListItem only -- no EnumeratedItem in ODM 2.0) ---------
builder.add_code_list(
    OID="CL.UNIT", Name="Units", DataType="text",
    StandardOID="STD.SDTMIG",
    items=[
        {"CodedValue": "mmHg", "Decode": "mmHg"},
        {"CodedValue": "kg", "Decode": "kilograms"},
    ],
)
cl_unit = mdv.CodeList[-1]
# A CodeListItem that carries only a Coding (no Decode) -- the ODM 2.0
# replacement for 1.3.2's EnumeratedItem; build it and attach it.
builder.attach(cl_unit, M.CodeListItem(
    CodedValue="mg",
    Coding=[M.Coding(System="https://www.cdisc.org/standards/terminology",
                     Code="C28253", SystemName="CDISC/NCI CT")]))
builder.attach(cl_unit, M.Coding(
    System="https://www.cdisc.org/standards/terminology", Code="C66770",
    SystemName="CDISC/NCI CT"))
builder.attach(cl_unit, desc("Units of measure"))

builder.add_code_list(
    OID="CL.NY", Name="No Yes Response", DataType="text",
    items=[
        {"CodedValue": "N", "Decode": "No"},
        {"CodedValue": "Y", "Decode": "Yes"},
    ],
)

# --- MethodDef (+ MethodSignature via escape hatch) ------------------------
# ConditionDef is intentionally omitted: the ODM 2.0 XSD requires a
# MethodSignature child inside ConditionDef, which the odmlib ConditionDef
# class cannot represent. MethodDef *can* carry a MethodSignature.
# formal_expression is intentionally not passed: ODM 2.0 FormalExpression
# is element-based (Code | ExternalCodeLib), but the odmlib FormalExpression
# class is text-based, so a text expression is not schema-valid in 2.0.
builder.add_method_def(
    OID="M.DERIVE", Name="Derive Weight in kg", Type="Computation",
    description="Convert collected weight to kilograms")
builder.attach(mdv.MethodDef[-1], M.MethodSignature(
    Parameter=[M.Parameter(Name="WEIGHT_LB", DataType="float",
                           OrderNumber=1)]))

odm = builder.build()

m = odm.Study[0].MetaDataVersion[1]
print("Built ODM 2.0 document with the fluent ODMBuilder")
print(f"  FileOID:           {odm.FileOID}")
print(f"  Study:             {odm.Study[0].OID} "
      f"(StudyName={odm.Study[0].StudyName})")
print(f"  MetaDataVersions:  {len(odm.Study[0].MetaDataVersion)}")
print(f"  Standards:         {len(m.Standards.Standard)}")
print(f"  Protocol:          {'present' if m.Protocol else 'absent'} "
      f"(arms={len(m.Protocol.StudyStructure.Arm)}, "
      f"epochs={len(m.Protocol.StudyStructure.Epoch)})")
print(f"  WorkflowDefs:      {len(m.WorkflowDef)}")
print(f"  StudyEventDefs:    {len(m.StudyEventDef)}")
print(f"  ItemGroupDefs:     {len(m.ItemGroupDef)}")
print(f"  ItemDefs:          {len(m.ItemDef)}")
print(f"  CodeLists:         {len(m.CodeList)}")
print(f"  MethodDefs:        {len(m.MethodDef)} "
      f"(MethodSignature: "
      f"{'yes' if m.MethodDef[0].MethodSignature else 'no'})")


# ---------------------------------------------------------------------------
# 2. Serialize to XML
# ---------------------------------------------------------------------------
# ODM 2.0 requires TranslatedText/@Type; ODMBuilder now defaults it to
# 'text/plain' for the odm_2_0 model shape, so no post-pass is needed.
odm.write_xml(OUTPUT_FILE)
print(f"\nWrote {OUTPUT_FILE} ({os.path.getsize(OUTPUT_FILE)} bytes)")


# ---------------------------------------------------------------------------
# 3. Schema-validate the written file against the bundled ODM 2.0 XSD
# ---------------------------------------------------------------------------
validator = P.ODMSchemaValidator(standard="odm", version="2.0")
schema_errors = list(validator.xsd.iter_errors(OUTPUT_FILE))
if schema_errors:
    print(f"\nSchema validation FAILED with {len(schema_errors)} error(s):")
    for i, err in enumerate(schema_errors, 1):
        print(f"  {i}. {err.reason}  (path: {err.path})")
else:
    print("\nSchema validation passed (ODM 2.0 XSD)")


# ---------------------------------------------------------------------------
# 4. OID ref/def integrity check + unreferenced-OID report
# ---------------------------------------------------------------------------
checker = create_oid_checker("odm_2_0")
try:
    odm.verify_oids(checker)
    print("OID ref/def check passed (every validated *OID reference resolves)")
except OdmlibError as exc:
    print(f"OID ref/def check FAILED: {exc}")

# Many ODM 2.0 structural definitions (the active MDV, Epochs, the
# StudyEventDefs, Transition, ...) are definition-only and are never the
# target of a *Ref attribute -- a non-empty list here is informational.
orphans = odm.unreferenced_oids(checker)
if orphans:
    print(f"Defined-but-unreferenced OIDs ({len(orphans)}, informational): "
          f"{', '.join(sorted(orphans))}")
else:
    print("Every defined OID is referenced somewhere")


# ---------------------------------------------------------------------------
# 5. Round-trip: reload with open_odm(model_package='odm_2_0') and re-validate
# ---------------------------------------------------------------------------
with open_odm(OUTPUT_FILE, model_package="odm_2_0") as reloaded:
    rt_errors = reloaded.validate(
        collect_errors=True, oid_checker=create_oid_checker("odm_2_0"))
    rt_mdv = reloaded.Study[0].MetaDataVersion[1]
    same_file = reloaded.FileOID == odm.FileOID
    same_groups = len(rt_mdv.ItemGroupDef) == len(m.ItemGroupDef)

print("\nRound-trip via open_odm(model_package='odm_2_0'):")
print(f"  FileOID preserved: {same_file} ({reloaded.FileOID})")
print(f"  ItemGroupDef count preserved: {same_groups} "
      f"({len(rt_mdv.ItemGroupDef)} ItemGroupDefs)")
if rt_errors:
    print(f"  Reloaded-document validation found {len(rt_errors)} issue(s):")
    for i, err in enumerate(rt_errors, 1):
        print(f"    {i}. [{type(err).__name__}] {err}")
else:
    print("  Reloaded document validates clean "
          "(element order + OID ref/def)")
