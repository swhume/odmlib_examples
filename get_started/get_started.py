from odmlib import odm_loader as OL, loader as LO
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_1_3_2.rules.oid_ref as OID
import xml.etree.ElementTree as ET
import odmlib.odm_parser as P
import os
import datetime

# update this path to point to your ODM1-3-2 schema file
SCHEMA_FILE = os.path.join(os.sep, 'home', 'sam', 'standards', 'odm1-3-2', 'ODM1-3-2.xsd')


class ODMProcessor:
    def __init__(self, odm_file):
        """ odmlib example that demonstrates how to read and process a basic ODM file """
        self.odm_file = odm_file
        self.schema_file = SCHEMA_FILE
        self._validate_metadata()
        loader = LO.ODMLoader(OL.XMLODMLoader())
        loader.open_odm_document(odm_file)
        self.mdv = loader.MetaDataVersion()
        self._oid_check()

    def _validate_metadata(self):
        self.validator = P.ODMSchemaValidator(self.schema_file)
        self.parser = P.ODMParser(self.odm_file)
        tree = self.parser.parse_tree()
        print(f"Is ODM valid: {self.validator.validate_tree(tree)}")

    def _oid_check(self):
        self.oid_checker = OID.OIDRef()
        try:
            self.mdv.verify_oids(self.oid_checker)
            self.oid_checker.check_oid_refs()
        except ValueError as ve:
            print(f"OID def/ref validation error: {str(ve)}\n")

    def list_metadata(self):
        self._list_forms()
        self._list_item_groups()
        self._list_items()
        self._list_code_lists()
        self._list_methods()

    def _list_forms(self):
        print("FormDefs:")
        for form in self.mdv.FormDef:
            print(f"FormDef OID = {form.OID} with Name = {form.Name}")

    def _list_item_groups(self):
        print("\nItemGroupDefs:")
        for igd in self.mdv.ItemGroupDef:
            print(f"ItemGroupDef OID = {igd.OID} with Name = {igd.Name}")

    def _list_items(self):
        print("\nItemDefs:")
        for item in self.mdv.ItemDef:
            print(f"ItemDef OID = {item.OID} with Name = {item.Name}")

    def _list_code_lists(self):
        print("\nCodeList:")
        for cl in self.mdv.CodeList:
            print(f"CodeList OID = {cl.OID} with Name = {cl.Name}")

    def _list_methods(self):
        print("\nMethodDef:")
        for method in self.mdv.MethodDef:
            print(f"MethodDef OID = {method.OID} with Name = {method.Name}")


class ODMCreator:
    def __init__(self, odm_file):
        """ odmlib example that demonstrates how to create a basic ODM file """
        self.odm_file = odm_file

    def create_document(self):
        root = ODM.ODM(FileOID="ODM.DEMO.001", Granularity="Metadata", AsOfDateTime=self._set_datetime(),
                       CreationDateTime=self._set_datetime(), ODMVersion="1.3.2", FileType="Snapshot",
                       Originator="swhume", SourceSystem="odmlib", SourceSystemVersion="0.1")
        root.Study = self._add_study()
        root.Study[0].MetaDataVersion.append(ODM.MetaDataVersion(OID="MDV.DEMO-ODM-01", Name="Get Started MDV", Description="Get Started Demo"))
        self._add_mdv_elements(root.Study[0].MetaDataVersion[0])
        root.write_xml(self.odm_file)

    def _add_study(self):
        study = ODM.Study(OID="ODM.GET.STARTED")
        study.GlobalVariables = ODM.GlobalVariables()
        study.GlobalVariables.StudyName = ODM.StudyName(_content="Get Started with ODM XML")
        study.GlobalVariables.StudyDescription = ODM.StudyDescription(_content="Demo to get started with odmlib")
        study.GlobalVariables.ProtocolName = ODM.ProtocolName(_content="ODM XML Get Started")
        return [study]

    def _add_mdv_elements(self, mdv):
        mdv.Protocol = self._add_protocol()
        mdv.StudyEventDef.append(self._add_study_event_def())
        mdv.FormDef = self._add_form_def()
        mdv.ItemGroupDef = self._add_item_group_def()
        mdv.ItemDef = self._add_item_def()
        mdv.CodeList = self._add_code_list()
        mdv.MethodDef = self._add_method_def()
        self._convert_elements()

    def _convert_elements(self):
        itd1, itd2 = self._add_item_def()
        item_xml = itd1.to_xml()
        print(f"ItemDef OID attribute: {item_xml.attrib['OID']}")
        print(f"ItemDef as XML:\n {ET.tostring(item_xml, encoding='utf8', method='xml')}")
        item_json = itd2.to_json()
        print(f"\nItemDef as JSON:\n {item_json}\n")

    def _add_method_def(self):
        md = ODM.MethodDef(OID="ODM.MT.DOB", Name="Create BRTHDTC from date ELEMENTS", Type="Computation")
        md.Description = ODM.Description()
        md.Description.TranslatedText.append(ODM.TranslatedText(_content="Concatenation of BRTHYR, BRTHMO, and BRTHDY in ISO 8601 format", lang="en"))
        return [md]

    def _add_code_list(self):
        cl = ODM.CodeList(OID="ODM.CL.NY_SUB_Y_N", Name="No Yes Response", DataType="text")
        cli1 = ODM.CodeListItem(CodedValue="N")
        cli1.Decode = ODM.Decode()
        cli1.Decode.TranslatedText.append(ODM.TranslatedText(_content="No", lang="en"))
        cl.CodeListItem.append(cli1)
        cli2 = ODM.CodeListItem(CodedValue="Y")
        cli2.Decode = ODM.Decode()
        cli2.Decode.TranslatedText.append(ODM.TranslatedText(_content="Yes", lang="en"))
        cl.CodeListItem.append(cli2)
        return [cl]

    def _add_item_def(self):
        # ItemDef 1
        itd1 = ODM.ItemDef(OID="ODM.IT.VS.VSDAT", Name="Date", DataType="partialDate")
        itd1.Description = ODM.Description()
        itd1.Description.TranslatedText.append(ODM.TranslatedText(_content="Date of measurements", lang="en"))
        itd1.Question = ODM.Question()
        itd1.Question.TranslatedText.append(ODM.TranslatedText(_content="Date", lang="en"))
        itd1.Alias.append(ODM.Alias(Context="CDASH", Name="VSDAT"))
        # ItemDef 2
        itd2 = ODM.ItemDef(OID="ODM.IT.VS.BP.VSORRESU", Name="BP Units", DataType="text")
        itd2.Description = ODM.Description()
        itd2.Description.TranslatedText.append(ODM.TranslatedText(_content="Result of the vital signs measurement as originally received or collected.", lang="en"))
        itd2.Question = ODM.Question()
        itd2.Question.TranslatedText.append(ODM.TranslatedText(_content="Diastolic", lang="en"))
        itd2.Alias.append(ODM.Alias(Context="CDASH", Name="BP.DIABP.VSORRES"))
        itd2.Alias.append(ODM.Alias(Context="CDASH/SDTM", Name="VSORRES+VSORRESU"))
        return [itd1, itd2]

    def _add_item_group_def(self):
        igd1 = ODM.ItemGroupDef(OID="ODM.IG.VS", Name="Vital Sign Measurement", Repeating="Yes")
        igd1.ItemRef.append(ODM.ItemRef(ItemOID="ODM.IT.VS.VSDAT", Mandatory="Yes"))
        igd1.ItemRef.append(ODM.ItemRef(ItemOID="ODM.IT.VS.BP.DIABP.VSORRES", Mandatory="Yes"))
        igd1.ItemRef.append(ODM.ItemRef(ItemOID="ODM.IT.VS.BP.SYSBP.VSORRES", Mandatory="Yes"))
        igd2 = ODM.ItemGroupDef(OID="ODM.IG.DM", Name="Demographics", Repeating="No")
        igd2.ItemRef.append(ODM.ItemRef(ItemOID="ODM.IT.DM.BRTHYR", Mandatory="Yes"))
        igd2.ItemRef.append(ODM.ItemRef(ItemOID="ODM.IT.DM.SEX", Mandatory="Yes"))
        return [igd1, igd2]

    def _add_form_def(self):
        fd1 = ODM.FormDef(OID="ODM.F.VS", Name="Vital Signs", Repeating="No")
        fd1.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.Common", Mandatory="Yes", OrderNumber=1))
        fd1.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS_GENERAL", Mandatory="Yes", OrderNumber=2))
        fd1.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS", Mandatory="Yes", OrderNumber=3))
        fd2 = ODM.FormDef(OID="ODM.F.DM", Name="Demographics", Repeating="No")
        fd2.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.Common", Mandatory="Yes", OrderNumber=1))
        fd2.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.DM", Mandatory="Yes", OrderNumber=2))
        return [fd1, fd2]

    def _add_study_event_def(self):
        sed = ODM.StudyEventDef(OID="BASELINE", Name="Baseline Visit", Repeating="No", Type="Scheduled")
        sed.FormRef.append(ODM.FormRef(FormOID="ODM.F.DM", Mandatory="Yes", OrderNumber=1))
        sed.FormRef.append(ODM.FormRef(FormOID="ODM.F.VS", Mandatory="Yes", OrderNumber=2))
        return sed

    def _add_protocol(self):
        p = ODM.Protocol()
        p.Description = ODM.Description()
        p.Description.TranslatedText.append(ODM.TranslatedText(_content="Get Started Protocol", lang="en"))
        p.StudyEventRef.append(ODM.StudyEventRef(StudyEventOID="BASELINE", OrderNumber=1, Mandatory="Yes"))
        return p


    def _set_datetime(self):
        """return the current datetime in ISO 8601 format"""
        return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()


if __name__ == '__main__':
    creator = ODMCreator("./data/odm_demo.xml")
    creator.create_document()
    process = ODMProcessor("./data/odm_demo.xml")
    process.list_metadata()
