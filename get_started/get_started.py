"""
get_started.py -- the "start here" odmlib example (odmlib >= 0.2.1).

Two classes cover the two most common odmlib jobs:

  ODMCreator    Build an ODM 1.3.2 study-metadata document with the fluent
                ``ODMBuilder``, validate it (element order + OID ref/def +
                conformance) before writing, write it, and show how to
                serialize a single element to an XML string and to JSON.
  ODMProcessor  XSD-validate the written file against the bundled ODM 1.3.2
                schema, load it read-only with ``open_odm()``, run the same
                ``validate()`` pass on the loaded document, and list metadata.

Run:  cd get_started && python get_started.py
"""
import datetime

from odmlib import ODMBuilder, create_oid_checker, open_odm
from odmlib.odm_parser import ODMSchemaValidator
from odmlib.odm_1_3_2.rules.metadata_schema import MetadataSchema
import odmlib.odm_1_3_2.model as ODM

MODEL = "odm_1_3_2"


def validate(odm):
    """Run odmlib's unified validator and report every problem it finds.

    ``collect_errors=True`` returns all element-order, OID and conformance
    errors in one pass (instead of raising on the first). A *fresh* OID
    checker is created per call: a checker accumulates OIDs, so reusing one
    across documents reports false duplicates.
    """
    errors = odm.validate(
        collect_errors=True,
        oid_checker=create_oid_checker(MODEL),
        conformance_checker=MetadataSchema(),
    )
    if errors:
        print(f"Validation found {len(errors)} issue(s):")
        for i, err in enumerate(errors, 1):
            print(f"  {i}. [{type(err).__name__}] {str(err).splitlines()[0]}")
    else:
        print("Validation passed (element order + OID ref/def + conformance)")
    return not errors


class ODMCreator:
    def __init__(self, odm_file):
        """ odmlib example that demonstrates how to create a basic ODM file """
        self.odm_file = odm_file

    def create_document(self):
        odm = self._build()
        validate(odm)
        odm.write_xml(self.odm_file)
        print(f"Wrote {self.odm_file}")
        self._serialize_one_element(odm)

    def _build(self):
        """Build the document with ODMBuilder -- it creates the right Study
        shape for the model (GlobalVariables in 1.3.2) and keeps children in
        schema order, so there is no element ordering to get wrong."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        builder = ODMBuilder(MODEL)
        (
            builder
            .set_file(FileOID="ODM.DEMO.001", FileType="Snapshot",
                      Granularity="Metadata", AsOfDateTime=now,
                      CreationDateTime=now, ODMVersion="1.3.2",
                      Originator="swhume", SourceSystem="odmlib",
                      SourceSystemVersion="0.2.1")
            .add_study(OID="ODM.GET.STARTED",
                       study_name="Get Started with ODM XML",
                       study_description="Demo to get started with odmlib",
                       protocol_name="ODM XML Get Started")
            .add_metadata_version(OID="MDV.DEMO-ODM-01", Name="Get Started MDV",
                                  Description="Get Started Demo")
        )
        # Escape hatch for elements with no dedicated builder method: build
        # the model object and attach() it to a parent from builder.current.
        # A Protocol with a Description goes on first; add_study_event_ref()
        # below then appends to this Protocol (schema order is Description,
        # StudyEventRef, Alias).
        builder.attach(builder.current["mdv"], ODM.Protocol(
            Description=ODM.Description(TranslatedText=[
                ODM.TranslatedText(_content="Get Started Protocol", lang="en")])))
        (
            builder
            .add_study_event_ref(StudyEventOID="BASELINE", OrderNumber=1,
                                 Mandatory="Yes")
            # --- StudyEventDef -> FormRefs
            .add_study_event_def(OID="BASELINE", Name="Baseline Visit",
                                 Repeating="No", Type="Scheduled")
            .add_form_ref(FormOID="ODM.F.DM", Mandatory="Yes", OrderNumber=1)
            .add_form_ref(FormOID="ODM.F.VS", Mandatory="Yes", OrderNumber=2)
            # --- FormDefs -> ItemGroupRefs
            .add_form_def(OID="ODM.F.DM", Name="Demographics", Repeating="No")
            .add_item_group_ref(ItemGroupOID="ODM.IG.DM", Mandatory="Yes",
                                OrderNumber=1)
            .add_form_def(OID="ODM.F.VS", Name="Vital Signs", Repeating="No")
            .add_item_group_ref(ItemGroupOID="ODM.IG.VS", Mandatory="Yes",
                                OrderNumber=1)
            # --- ItemGroupDefs -> ItemRefs
            .add_item_group_def(OID="ODM.IG.DM", Name="Demographics",
                                Repeating="No")
            .add_item_ref(ItemOID="ODM.IT.DM.BRTHDTC", Mandatory="Yes",
                          OrderNumber=1, MethodOID="ODM.MT.DOB")
            .add_item_ref(ItemOID="ODM.IT.DM.SEX", Mandatory="Yes",
                          OrderNumber=2)
            .add_item_group_def(OID="ODM.IG.VS", Name="Vital Sign Measurement",
                                Repeating="Yes")
            .add_item_ref(ItemOID="ODM.IT.VS.VSDAT", Mandatory="Yes",
                          OrderNumber=1)
            .add_item_ref(ItemOID="ODM.IT.VS.BP.DIABP.VSORRES", Mandatory="Yes",
                          OrderNumber=2)
            .add_item_ref(ItemOID="ODM.IT.VS.BP.SYSBP.VSORRES", Mandatory="Yes",
                          OrderNumber=3)
            .add_item_ref(ItemOID="ODM.IT.VS.BP.VSORRESU", Mandatory="Yes",
                          OrderNumber=4)
            # --- ItemDefs (+ with_* enrichers act on the most recent ItemDef)
            .add_item_def(OID="ODM.IT.DM.BRTHDTC", Name="Birth Date",
                          DataType="date")
            .with_description("Date of birth in ISO 8601 format")
            .with_question("Birth Date")
            .with_alias("SDTM", "BRTHDTC")
            .add_item_def(OID="ODM.IT.DM.SEX", Name="Sex", DataType="text",
                          Length=1)
            .with_question("Sex")
            .with_codelist_ref("ODM.CL.SEX")
            .with_alias("CDASH", "SEX")
            .add_item_def(OID="ODM.IT.VS.VSDAT", Name="Date",
                          DataType="partialDate")
            .with_description("Date of measurements")
            .with_question("Date")
            .with_alias("CDASH", "VSDAT")
            .add_item_def(OID="ODM.IT.VS.BP.DIABP.VSORRES", Name="Diastolic",
                          DataType="integer", Length=3)
            .with_question("Diastolic")
            .with_alias("CDASH", "BP.DIABP.VSORRES")
            .add_item_def(OID="ODM.IT.VS.BP.SYSBP.VSORRES", Name="Systolic",
                          DataType="integer", Length=3)
            .with_question("Systolic")
            .with_alias("CDASH", "BP.SYSBP.VSORRES")
            .add_item_def(OID="ODM.IT.VS.BP.VSORRESU", Name="BP Units",
                          DataType="text", Length=10)
            .with_description("Unit of the vital signs measurement as "
                              "originally received or collected.")
            .with_question("Units")
            .with_alias("CDASH/SDTM", "VSORRES+VSORRESU")
            # --- CodeList: items= builds the CodeListItem/Decode tree
            .add_code_list(OID="ODM.CL.SEX", Name="Sex", DataType="text",
                           items=[{"CodedValue": "M", "Decode": "Male"},
                                  {"CodedValue": "F", "Decode": "Female"}])
            # --- MethodDef (referenced by the BRTHDTC ItemRef above)
            .add_method_def(OID="ODM.MT.DOB",
                            Name="Create BRTHDTC from date ELEMENTS",
                            Type="Computation",
                            description="Concatenation of BRTHYR, BRTHMO, and "
                                        "BRTHDY in ISO 8601 format")
        )
        return builder.build()

    def _serialize_one_element(self, odm):
        """Serialize a single element -- the string and tree paths."""
        mdv = odm.Study[0].MetaDataVersion[0]     # ODM: Study and MDV are lists
        item = mdv.find("ItemDef", "OID", "ODM.IT.VS.VSDAT")
        # to_xml_string() declares the ODM namespace itself, so the result is
        # self-contained and re-parses/validates on its own. Do not use
        # ET.tostring(obj.to_xml()) -- that buffer carries no xmlns and reloads
        # silently into the wrong namespace.
        print(f"\nItemDef as XML:\n {item.to_xml_string()}")
        # to_element() is the namespace-aware ElementTree tree when you need one.
        elem = item.to_element()
        print(f"ItemDef tag (Clark notation): {elem.tag}")
        print(f"ItemDef OID attribute: {elem.attrib['OID']}")
        print(f"\nItemDef as JSON:\n {item.to_json()}\n")


class ODMProcessor:
    def __init__(self, odm_file):
        """ odmlib example that demonstrates how to read and process a basic ODM file """
        self.odm_file = odm_file

    def run(self):
        self._xsd_validate()
        # open_odm() is read-only by default: nothing is written back on exit.
        # Pass output_file= or write_on_exit=True to make it a read-modify-write.
        with open_odm(self.odm_file, model_package=MODEL) as odm:
            validate(odm)
            self._list_metadata(odm.Study[0].MetaDataVersion[0])

    def _xsd_validate(self):
        # odmlib bundles the ODM 1.3.2 schema; resolve it by (standard, version)
        # instead of hard-coding a local path.
        validator = ODMSchemaValidator(standard="odm", version="1.3.2")
        schema_errors = list(validator.xsd.iter_errors(self.odm_file))
        if schema_errors:
            print(f"Schema validation FAILED with {len(schema_errors)} error(s):")
            for i, err in enumerate(schema_errors, 1):
                print(f"  {i}. {err.reason}  (path: {err.path})")
        else:
            print("Schema validation passed (bundled ODM 1.3.2 XSD)")

    def _list_metadata(self, mdv):
        for element in ("FormDef", "ItemGroupDef", "ItemDef", "CodeList",
                        "MethodDef"):
            print(f"\n{element}:")
            for obj in getattr(mdv, element):
                print(f"{element} OID = {obj.OID} with Name = {obj.Name}")


if __name__ == '__main__':
    ODMCreator("./data/odm_demo.xml").create_document()
    print()
    ODMProcessor("./data/odm_demo.xml").run()
