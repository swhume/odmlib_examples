# Copyright 2022 Sam Hume. Licensed under the MIT-0 license https://opensource.org/licenses/MIT-0
import odmlib.define_2_1.model as DEFINE
import datetime

"""
This is the code presented at the PHUSE US Connect 2022 and described in paper PAP_OS01.
The purpose of this code is to demonstrate using odmlib to create and process a very simple Define-XML v2.1 file.
NOTE: In places where paths are referenced, you will need to update them to reflect your system.
"""

current_datetime = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
odm = DEFINE.ODM(FileOID="DEF.COSA.DEMO",
              AsOfDateTime=current_datetime,
              CreationDateTime=current_datetime,
              ODMVersion="1.3.2",
              FileType="Snapshot",
              Originator="Sam Hume",
              SourceSystem="odmlib",
              SourceSystemVersion="0.1.4",
              Context="Other")

study = DEFINE.Study(OID="ST.DEFINE.COSA.001")
study.GlobalVariables.StudyName = DEFINE.StudyName(_content="TEST Define-XML ItemGroupDef")
study.GlobalVariables.StudyDescription = DEFINE.StudyDescription(_content="ItemGroupDef 001")
study.GlobalVariables.ProtocolName = DEFINE.ProtocolName(_content="Define-XML ItemGroupDef")
odm.Study = study

mdv = DEFINE.MetaDataVersion(OID="MDV.COSA.IGD.001", Name="ItemGroupDefDemo001",
                                     Description="ItemGroupDef COSA Demo", DefineVersion="2.1.0")

mdv.Standards.Standard.append(DEFINE.Standard(OID="STD.1", Name="SDTMIG", Type="IG", Version="3.2", Status="Final"))
mdv.Standards.Standard.append(DEFINE.Standard(OID="STD.2", Name="CDISC/NCI", Type="CT", PublishingSet="SDTM",
                                              Version="2021-12-17", Status="Final"))

igd = DEFINE.ItemGroupDef(OID="IG.VS",
                          Name="VS",
                          Repeating="Yes",
                          Domain="VS",
                          SASDatasetName="VS",
                          IsReferenceData="No",
                          Purpose="Tabulation",
                          ArchiveLocationID="LF.VS",
                          Structure="One record per vital sign measurement per visit per subject",
                          StandardOID="STD.1",
                          IsNonStandard="Yes",
                          HasNoData="Yes")

igd.Description.TranslatedText.append(DEFINE.TranslatedText(_content="Vital Signs", lang="en"))
igd.ItemRef.append(DEFINE.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", OrderNumber=1, KeySequence=1))
igd.ItemRef.append(DEFINE.ItemRef(ItemOID="IT.VS.DOMIAN", Mandatory="Yes", OrderNumber=2))
igd.ItemRef.append(DEFINE.ItemRef(ItemOID="IT.USUBJID", Mandatory="Yes", OrderNumber=3, KeySequence=2))
igd.ItemRef.append(DEFINE.ItemRef(ItemOID="IT.VS.VSSEQ", Mandatory="Yes", OrderNumber=4))
igd.ItemRef.append(DEFINE.ItemRef(ItemOID="IT.VS.VSTESTCD", Mandatory="Yes", OrderNumber=5, KeySequence=3))
igd.ItemRef.append(DEFINE.ItemRef(ItemOID="IT.VS.VSTEST", Mandatory="Yes", OrderNumber=6))

try:
    ir = DEFINE.ItemRef(Mandatory="Yes", OrderNumber=1)
except ValueError as ve:
    print(f"Error creating ItemRef: {ve}")

igd.Class = DEFINE.Class(Name="FINDINGS")

odm.Study.MetaDataVersion = mdv
odm.Study.MetaDataVersion.ItemGroupDef.append(igd)

# update the path to reflect your system
odm.write_xml(odm_file="./data/cosa_define_demo.xml")

odm.write_json(odm_file="./data/cosa_define_demo.json")

# update the path to reflect your system
with open("./data/cosa_define_demo.xml", 'r') as file:
    cosa_odm = file.read()
print(cosa_odm)

from odmlib import odm_parser as P
# relpace the path below to your Define-XML v2.1 schema
schema_file = "/home/sam/standards/DefineV211/schema/cdisc-define-2.1/define2-1-0.xsd"

validator = P.ODMSchemaValidator(schema_file)
try:
    # update the path to reflect your system
    validator.validate_file("./data/cosa_define_demo.xml")
    print("define-XML schema validation completed successfully...")
except P.OdmlibSchemaValidationError as ve:
    print(f"schema validation errors: {ve}")

from odmlib import define_loader as DL, loader as LD
loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1", ns_uri="http://www.cdisc.org/ns/def/v2.1"))
loader.open_odm_document("./data/cosa_define_demo.xml")

odm = loader.load_odm()
print(f"Study OID is {odm.Study.OID}")
print(f"Study Name is {odm.Study.GlobalVariables.StudyName}")
print(f"Study Description is {odm.Study.GlobalVariables.StudyDescription}")
print(f"Protocol Name is {odm.Study.GlobalVariables.ProtocolName}")

cosa_dict = odm.to_dict()
print(cosa_dict)

cosa_json = odm.to_json()
