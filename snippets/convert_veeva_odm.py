import odmlib.ns_registry as NS
from odmlib import odm_loader as OL, loader as LO

from veeva_odm_1_0 import model as ODM

"""
Takes a draft odmlib Veeva model and generates an ODM-based version of it. This example reads in the example Veeva model
and transforms it into an ODM-extension version of the model. It is a proof-of-concept that highlights a simple way to 
implement the Veeva model as ODM or to transform the Veeva model into an ODM-extension. The example is not 
intended to be a complete representation of the Veeva ODM. It is intended to show how to create a simple Veeva 
ODM-extension file using odmlib.
"""

INPUT_ODM_FILE = "data/veeva_vodm.xml"
OUTPUT_ODM_FILE = "data/odm_from_veeva.xml"

# load the draft Veeva model
model_package = "veeva_1_0"
loader = LO.ODMLoader(
    OL.XMLODMLoader(model_package=model_package, ns_uri="http://www.cdisc.org/ns/odm/v1.3", local_model=True)
)
loader.open_odm_document(INPUT_ODM_FILE)
v_odm = loader.root()
v_study = loader.load_study()
# print some identifying information from the original model
print(f"Loaded Veeva file with study name is {v_study.Name}")
print(f"Veeva file with MetaDataVersion name: {v_study.MetaDataVersion.Name}")
print(f"Veeva file with EventGroupDef name: {v_study.MetaDataVersion.EventGroupDef[0].Name}")

# switch to the Veeva ODM model
NS.NamespaceRegistry(prefix="vee", uri="http://www.cdisc.org/ns/veeva-odm/v1.0")

root = ODM.ODM(
    FileOID=v_odm.FileOID,
    Granularity=v_odm.Granularity,
    AsOfDateTime=v_odm.AsOfDateTime,
    CreationDateTime=v_odm.CreationDateTime,
    ODMVersion=v_odm.ODMVersion,
    FileType="Snapshot",
    Originator="swhume",
    SourceSystem=v_odm.SourceSystem,
    SourceSystemVersion=v_odm.SourceSystemVersion
)

# create Study and add to ODM
root.Study.append(ODM.Study(OID=v_study.Name))
# create the global variables
root.Study[0].GlobalVariables = ODM.GlobalVariables()
root.Study[0].GlobalVariables.StudyName = ODM.StudyName(_content=v_study.Name.replace(".", " "))
root.Study[0].GlobalVariables.StudyDescription = ODM.StudyDescription(_content="Veeva conversion proof of concept")
root.Study[0].GlobalVariables.ProtocolName = ODM.ProtocolName(_content="Proof of concept")

#  create the BasicDefinitions
mu = ODM.MeasurementUnit(OID="MU." + v_study.MetaDataVersion.UnitDef[0].Name,
                         Name=v_study.MetaDataVersion.UnitDef[0].Name)
mu.Symbol.TranslatedText.append(
    ODM.TranslatedText(_content=v_study.MetaDataVersion.UnitDef[0].UnitChoice[0].Label, lang="en"))
root.Study[0].BasicDefinitions = ODM.BasicDefinitions()
root.Study[0].BasicDefinitions.MeasurementUnit.append(mu)

# create the MetaDataVersion
root.Study[0].MetaDataVersion.append(ODM.MetaDataVersion(OID=v_study.MetaDataVersion.Name,
                                                         Name=v_study.MetaDataVersion.Name.replace(".", " "),
                                                         Description=v_study.MetaDataVersion.Description))

# create Protocol
p = ODM.Protocol()
p.Description.TranslatedText.append(ODM.TranslatedText(_content="Veeva Conversion proof of concept", lang="en"))
p.EventGroupRef.append(ODM.EventGroupRef(EventGroupOID="EG." + v_study.MetaDataVersion.EventGroupDef[0].Name))
root.Study[0].MetaDataVersion[0].Protocol = p
egd = ODM.EventGroupDef(OID="SEG." + v_study.MetaDataVersion.EventGroupDef[0].Name,
                        Name=v_study.MetaDataVersion.EventGroupDef[0].Name.replace(".", " "),
                        RepeatMaximum=v_study.MetaDataVersion.EventGroupDef[0].RepeatMaximum,
                        Repeating="No")
ser = ODM.StudyEventRef(StudyEventOID="SE." + v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].Name,
                        Mandatory="Yes")
egd.StudyEventRef.append(ser)
root.Study[0].MetaDataVersion[0].EventGroupDef.append(egd)

# create a StudyEventDef
sed = ODM.StudyEventDef(OID="SE." + v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].Name,
                        Name=v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].Name.replace(".", " "),
                        Repeating="No",
                        RepeatMaximum=1,
                        Type="Scheduled")
fr = ODM.FormRef(FormOID="F." + v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].FormDef[0].Name,
                 Mandatory="Yes", OrderNumber=1)
sed.FormRef.append(fr)
root.Study[0].MetaDataVersion[0].StudyEventDef.append(sed)

# create a FormDef
fd = ODM.FormDef(OID="F." + v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].FormDef[0].Name,
                 Name=v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].FormDef[0].Name,
                 Repeating="No", RepeatMaximum="1")
fd.ItemGroupRef.append(ODM.ItemGroupRef(
    ItemGroupOID="IG." + v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].FormDef[0].ItemGroupDef[0].Name,
    Mandatory="Yes"))
root.Study[0].MetaDataVersion[0].FormDef.append(fd)

# create an ItemGroupDef
igd = ODM.ItemGroupDef(OID="IG." + v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].FormDef[0].ItemGroupDef[0].Name,
                       Name=v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].FormDef[0].ItemGroupDef[0].Name,
                       Repeating="No", RepeatMaximum="1")
igd.ItemRef.append(ODM.ItemRef(
    ItemOID="IT.DM." + v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].FormDef[0].ItemGroupDef[0].ItemDef[0].Name,
    Mandatory="Yes"))
igd.ItemRef.append(ODM.ItemRef(
    ItemOID="IT.DM." + v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].FormDef[0].ItemGroupDef[0].ItemDef[1].Name,
    Mandatory="Yes"))
root.Study[0].MetaDataVersion[0].ItemGroupDef.append(igd)

# create an ItemDef
itd1 = ODM.ItemDef(
    OID="IT.DM." + v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].FormDef[0].ItemGroupDef[0].ItemDef[0].Name,
    Name=v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].FormDef[0].ItemGroupDef[0].ItemDef[0].Name,
    DataType="integer")
itd1.MeasurementUnitRef.append(ODM.MeasurementUnitRef(MeasurementUnitOID="MU." + v_study.MetaDataVersion.UnitDef[0].Name))
itd2 = ODM.ItemDef(
    OID="IT.DM." + v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].FormDef[0].ItemGroupDef[0].ItemDef[1].Name,
    Name=v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].FormDef[0].ItemGroupDef[0].ItemDef[1].Name,
    DataType=v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].FormDef[0].ItemGroupDef[0].ItemDef[1].DataType,
    Length=v_study.MetaDataVersion.EventGroupDef[0].EventDef[0].FormDef[0].ItemGroupDef[0].ItemDef[1].Length)
itd2.CodeListRef = ODM.CodeListRef(CodeListOID="CL." + v_study.MetaDataVersion.CodeListDef[0].Name)

root.Study[0].MetaDataVersion[0].ItemDef.append(itd1)
root.Study[0].MetaDataVersion[0].ItemDef.append(itd2)

# create a CodeListDef
sex_cl = ODM.CodeList(OID="CL." + v_study.MetaDataVersion.CodeListDef[0].Name,
                      Name=v_study.MetaDataVersion.CodeListDef[0].Name,
                      DataType="text")
cli1 = ODM.CodeListItem(CodedValue=v_study.MetaDataVersion.CodeListDef[0].CodeListItem[0].Code)
# cli1.Decode = ODM.Decode()
cli1.Decode.TranslatedText.append(
    ODM.TranslatedText(_content=v_study.MetaDataVersion.CodeListDef[0].CodeListItem[0].Label, lang="en"))
sex_cl.CodeListItem.append(cli1)
cli2 = ODM.CodeListItem(CodedValue=v_study.MetaDataVersion.CodeListDef[0].CodeListItem[1].Code)
# cli2.Decode = ODM.Decode()
cli2.Decode.TranslatedText.append(
    ODM.TranslatedText(_content=v_study.MetaDataVersion.CodeListDef[0].CodeListItem[1].Label, lang="en"))
sex_cl.CodeListItem.append(cli2)
root.Study[0].MetaDataVersion[0].CodeList.append(sex_cl)

# save the new ODM document to a file
root.write_xml(OUTPUT_ODM_FILE)
