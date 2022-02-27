import unittest
# temporary to test against local development version of odmlib
import sys
sys.path.insert(0, '/home/sam/src/odmlib')

import odmlib.ns_registry as NS
import odmlib.define_loader as DL
import odmlib.odm_loader as OL
from odmlib.define_2_1.rules import oid_ref as OID


class TestLocalLibraryLoader(unittest.TestCase):
    def test_odmlib_sdtmig(self):
        model_package = "library_define_1_0"
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.1")
        ns = NS.NamespaceRegistry(prefix="mdr", uri="http://www.cdisc.org/ns/library-xml/v1.0")
        with open("../data/library-sdtm-3-4.xml", "r", encoding="utf-8") as f:
            odm_string = f.read()
        loader = DL.XMLDefineLoader(model_package=model_package, ns_uri="http://www.cdisc.org/ns/library-xml/v1.0", local_model=True)
        loader.create_document_from_string(odm_string, ns)
        odm = loader.load_odm()
        self.assertEqual(odm.FileOID, "ODM.SDTMIGv3.4.2021-11-29")
        self.assertEqual(odm.LibraryXMLVersion, "1.0.0")
        self.assertEqual(odm.Context, "Other")
        self.assertEqual(odm.Study[0].MetaDataVersion.DatePublished, "2021-11-29")
        self.assertEqual(odm.Study[0].MetaDataVersion.Standards[0].Name, "SDTMIG v3.4")
        self.assertEqual(odm.Study[0].MetaDataVersion.ItemGroupDef[1].OID, "IGD.CM")
        self.assertEqual(odm.Study[0].MetaDataVersion.ItemGroupDef[1].Class.Name, "INTERVENTIONS")
        self.assertEqual(odm.Study[0].MetaDataVersion.ItemDef[0].CDISCNotes.TranslatedText[0]._content, "Unique identifier for a study.")
        self.assertEqual(odm.Study[0].MetaDataVersion.ItemDef[0].CDISCNotes.TranslatedText[0].lang, "en")
        self.assertEqual(odm.Study[0].MetaDataVersion.ItemDef[1].SubmissionDataType, "Char")
        mdv = odm.Study[0].MetaDataVersion
        it = mdv.find("ItemDef", "OID", "IT.DS.DSDECOD")
        self.assertEqual(it.Name, "DSDECOD")
        self.assertEqual(it.AltCodeListRef[0].CodeListOID, "CL.C114118")
        self.assertEqual(it.AltCodeListRef[1].CodeListOID, "CL.C150811")

    def test_odmlib_cdashig(self):
        model_package = "library_odm_1_0"
        NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
        ns = NS.NamespaceRegistry(prefix="mdr", uri="http://www.cdisc.org/ns/library-xml/v1.0")
        with open("../data/library-cdash-2-2.xml", "r", encoding="utf-8") as f:
            odm_string = f.read()
        loader = OL.XMLODMLoader(model_package=model_package, ns_uri="http://www.cdisc.org/ns/library-xml/v1.0", local_model=True)
        loader.create_document_from_string(odm_string, ns)
        odm = loader.load_odm()
        self.assertEqual(odm.FileOID, "ODM.CDASHIGv2.2.2021-09-28")
        self.assertEqual(odm.LibraryXMLVersion, "1.0.0")
        mdv = odm.Study[0].MetaDataVersion
        self.assertEqual(mdv.DatePublished, "2021-09-28")
        self.assertEqual(mdv.ItemGroupDef[1].OID, "IGD.CM")
        self.assertEqual(odm.Study[0].MetaDataVersion.ItemGroupDef[1].Class.Name, "INTERVENTIONS")
        mapping_instructions = odm.Study[0].MetaDataVersion.ItemDef[0].MappingInstructions.TranslatedText[0]._content.replace("\n", "")
        self.assertEqual(" ".join(mapping_instructions.split()), "Maps directly to the SDTMIG variable listed in the SDTMIG Target column.")
        self.assertEqual(odm.Study[0].MetaDataVersion.ItemDef[0].Definition.TranslatedText[0]._content, "A unique identifier for a study.")
        self.assertEqual(odm.Study[0].MetaDataVersion.ItemDef[1].SubmissionDataType, "Char")
        it = mdv.find("ItemDef", "OID", "IT.AG.AGSCAT")
        self.assertEqual(it.Name, "AGSCAT")
        self.assertEqual(it.Core, "O")

    def test_oid_checks(self):
        model_package = "library_define_1_0"
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.1")
        ns = NS.NamespaceRegistry(prefix="mdr", uri="http://www.cdisc.org/ns/library-xml/v1.0")
        with open("../data/library-sdtm-3-4.xml", "r", encoding="utf-8") as f:
            odm_string = f.read()
        loader = DL.XMLDefineLoader(model_package=model_package, ns_uri="http://www.cdisc.org/ns/library-xml/v1.0", local_model=True)
        loader.create_document_from_string(odm_string, ns)
        odm = loader.load_odm()
        oid_checker = OID.OIDRef()
        odm.verify_oids(oid_checker)
        self.assertTrue(oid_checker.check_oid_refs())
        orphans = oid_checker.check_unreferenced_oids()
        self.assertDictEqual(orphans, {'STD.SDTMIGv3.4': 'StandardOID'})

    def test_oid_checks_skip(self):
        model_package = "library_define_1_0"
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.1")
        ns = NS.NamespaceRegistry(prefix="mdr", uri="http://www.cdisc.org/ns/library-xml/v1.0")
        with open("../data/library-sdtm-3-4.xml", "r", encoding="utf-8") as f:
            odm_string = f.read()
        loader = DL.XMLDefineLoader(model_package=model_package, ns_uri="http://www.cdisc.org/ns/library-xml/v1.0", local_model=True)
        loader.create_document_from_string(odm_string, ns)
        odm = loader.load_odm()
        oid_checker = OID.OIDRef(skip_attrs=["StandardOID"], skip_elems=["Standard"])
        odm.verify_oids(oid_checker)
        self.assertTrue(oid_checker.check_oid_refs())
        orphans = oid_checker.check_unreferenced_oids()
        print(f"Orphans: {orphans}")
        self.assertDictEqual(orphans, {})


if __name__ == '__main__':
    unittest.main()
