from datetime import datetime, timezone
import odmlib.ns_registry as NS
from veeva_1_0 import model as ODM

"""
Uses a draft odmlib Veeva data exchange model and creates a very simple example ODM-like file. This example
follows a draft Veeva schema and is not a valid ODM extension as the model differs from the ODM spec in some ways. 
This example is a proof of concept, and is not intended to be a complete representation of the Veeva ODM. 
This example is intended to show how to create a simple Veeva ODM-like file using odmlib.

Since this is just a simple example developed to show how to create a Veeva ODM-like file, there are not command-line
arguments or other options. You can run this example directly from the command line. The output file will be saved to
the data directory.
"""

ODM_FILE = "data/veeva_vodm.xml"
NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
NS.NamespaceRegistry(prefix="vee", uri="http://www.cdisc.org/ns/vee-xml/v1.0")

current_datetime = datetime.now(timezone.utc).isoformat()
root = ODM.ODM(FileOID="ODM.VEEVA", Granularity="Metadata", AsOfDateTime=current_datetime,
               CreationDateTime=current_datetime, ODMVersion="1.3.2", FileType="Snapshot",
               Originator="swhume", SourceSystem="odmlib", SourceSystemVersion="0.1")

# create Study and add to ODM
root.Study.append(ODM.Study(Name="ODM.STUDY.VEEVA"))
# create the MetaDataVersion
mdv = ODM.MetaDataVersion(Name="MDV.VEEVA-ODM", Description="Proof of Concept")
# create EventGroupDefs
egd = ODM.EventGroupDef(Name="Treatment", RepeatMaximum=1)
# create EventDefs
ed = ODM.EventDef(Name="BaselineVisit")
# create FormDefs
fd = ODM.FormDef(Name="DM", RepeatMaximum=1)
# create ItemGroupDefs
igd = ODM.ItemGroupDef(Name="IG.DM", RepeatMaximum=1)
# create ItemDefs
age_item = ODM.ItemDef(Name="Age", Label="Age", DataType="integer", UnitDef="unit.age")
sex_item = ODM.ItemDef(Name="Sex", Label="Sex", DataType="text", Length="1", CodeListDef="cl.sex")
# create UnitDefs
age_units = ODM.UnitDef(Name="Age.Units")
age_units_year = ODM.UnitChoice(Name="Age.Units.Year", Label="Year")
# create CodeListDefs
sex_cl = ODM.CodeListDef(Name="CL.SEX")
sex_cl_m = ODM.CodeListItem(Code="M", Label="Male")
sex_cl_f = ODM.CodeListItem(Code="F", Label="Female")

# assemble the components to create the Veeva ODM document
age_units.UnitChoice.append(age_units_year)
sex_cl.CodeListItem.append(sex_cl_m)
sex_cl.CodeListItem.append(sex_cl_f)
igd.ItemDef.append(age_item)
igd.ItemDef.append(sex_item)
fd.ItemGroupDef.append(igd)
ed.FormDef.append(fd)
egd.EventDef.append(ed)
mdv.EventGroupDef.append(egd)
mdv.CodeListDef.append(sex_cl)
mdv.UnitDef.append(age_units)
root.Study[0].MetaDataVersion = mdv

# save the example Veeva ODM document to a file
root.write_xml(ODM_FILE)
