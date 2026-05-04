import odmlib.odm_loader as OL
import odmlib.loader as LD
import odmlib.ns_registry as NS
import os

OSB_ODM_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'osb_vs_crf.xml')


model_package = "osb_odm_1_0"
loader = OL.XMLODMLoader(model_package=model_package, ns_uri="http://www.cdisc.org/ns/odm/v1.3", local_model=True)
loader.create_document(OSB_ODM_FILE)

odm = loader.load_odm()
print(f"Study OID is {odm.Study[0].OID}")
print(f"Study Name is {odm.Study[0].GlobalVariables.StudyName}")
print(f"Study Description is {odm.Study[0].GlobalVariables.StudyDescription}")
print(f"Protocol Name is {odm.Study[0].GlobalVariables.ProtocolName}")
