import odmlib.odm_1_3_2.model as ODM
import datetime

ODM_FILE = "./data/simple_create.xml"

current_datetime = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
root = ODM.ODM(FileOID="ODM.DEMO.001", Granularity="Metadata", AsOfDateTime=current_datetime,
               CreationDateTime=current_datetime, ODMVersion="1.3.2", FileType="Snapshot",
               Originator="swhume", SourceSystem="odmlib", SourceSystemVersion="0.1")

# create Study and add to ODM
root.Study.append(ODM.Study(OID="ODM.GET.STARTED"))

# create the global variables
root.Study[0].GlobalVariables = ODM.GlobalVariables()
root.Study[0].GlobalVariables.StudyName = ODM.StudyName(_content="Get Started with ODM XML")
root.Study[0].GlobalVariables.StudyDescription = ODM.StudyDescription(_content="Demo to get started with odmlib")
root.Study[0].GlobalVariables.ProtocolName = ODM.ProtocolName(_content="ODM XML Get Started")

# create the MetaDataVersion
root.Study[0].MetaDataVersion.append(ODM.MetaDataVersion(OID="MDV.DEMO-ODM-01", Name="Get Started MDV",
                                                         Description="Get Started Demo"))
# create Protocol
p = ODM.Protocol()
p.Description = ODM.Description()
p.Description.TranslatedText.append(ODM.TranslatedText(_content="Get Started Protocol", lang="en"))
p.StudyEventRef.append(ODM.StudyEventRef(StudyEventOID="BASELINE", OrderNumber=1, Mandatory="Yes"))
root.Study[0].MetaDataVersion[0].Protocol = p

# create a StudyEventDef
sed = ODM.StudyEventDef(OID="BASELINE", Name="Baseline Visit", Repeating="No", Type="Scheduled")
sed.FormRef.append(ODM.FormRef(FormOID="ODM.F.DM", Mandatory="Yes", OrderNumber=1))
root.Study[0].MetaDataVersion[0].StudyEventDef.append(sed)

# create a FormDef
fd = ODM.FormDef(OID="ODM.F.DM", Name="Demographics", Repeating="No")
fd.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.DM", Mandatory="Yes", OrderNumber=2))
root.Study[0].MetaDataVersion[0].ItemGroupDef.append(fd)

# create an ItemGroupDef
igd = ODM.ItemGroupDef(OID="ODM.IG.DM", Name="Demographics", Repeating="No")
igd.ItemRef.append(ODM.ItemRef(ItemOID="ODM.IT.DM.BRTHYR", Mandatory="Yes"))
root.Study[0].MetaDataVersion[0].ItemGroupDef.append(igd)

# create an ItemDef
itd = ODM.ItemDef(OID="ODM.IT.DM.BRTHYR", Name="Birth Year", DataType="integer")
itd.Description = ODM.Description()
itd.Description.TranslatedText.append(ODM.TranslatedText(_content="Year of the subject's birth", lang="en"))
itd.Question = ODM.Question()
itd.Question.TranslatedText.append(ODM.TranslatedText(_content="Birth Year", lang="en"))
itd.Alias.append(ODM.Alias(Context="CDASH", Name="BRTHYR"))
itd.Alias.append(ODM.Alias(Context="SDTM", Name="BRTHDTC"))
root.Study[0].MetaDataVersion[0].ItemDef.append(itd)

# save the new ODM document to a file
root.write_xml(ODM_FILE)
