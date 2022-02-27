from odmlib import odm_parser as P
import odmlib.odm_1_3_2.rules.oid_ref as OID
#import cerberus as C
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_loader as OL
import odmlib.loader as LD
import odmlib.odm_1_3_2.rules.metadata_schema as METADATA
import xmlschema as XSD
import os

ODM_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'ODM-SnapShot-Export.xml')
SCHEMA_FILE = os.path.join(os.sep, 'home', 'sam', 'standards', 'odm1-3-2', 'ODM1-3-2.xsd')


def validate_odm_xml_file():
    validator = P.ODMSchemaValidator(SCHEMA_FILE)
    try:
        validator.validate_file(ODM_FILE)
    except XSD.validators.exceptions.XMLSchemaChildrenValidationError as ve:
        print(f"schema validation errors: {ve}")
    else:
        print("ODM XML schema validation completed successfully...")


def load_root():
    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2", ns_uri="http://www.cdisc.org/ns/odm/v1.3"))
    loader.open_odm_document(ODM_FILE)
    root = loader.load_odm()
    return root


def load_mdv():
    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2", ns_uri="http://www.cdisc.org/ns/odm/v1.3"))
    loader.open_odm_document(ODM_FILE)
    mdv = loader.MetaDataVersion()
    return mdv

def verify_oids(root):
    oid_checker = OID.OIDRef()
    try:
        # checks for non-unique OIDs and runs the ref/def check
        root.verify_oids(oid_checker)
    except ValueError as ve:
        print(f"Error verifying OIDs: {ve}")
    else:
        print(f"OIDs verified as valid")


def find_unreferenced_oids(mdv):
    oid_checker = OID.OIDRef()
    mdv.verify_oids(oid_checker)
    orphans = oid_checker.check_unreferenced_oids()
    print(f"found {len(orphans)} missing OID Defs")
    if orphans:
        print(f"Orphaned OIDs: {orphans}")


def verify_schema_rules(root):
    validator = METADATA.MetadataSchema()
    is_valid = validator.verify_conformance(root.to_dict(), "ODM")
    if is_valid:
        print("MetaDataVersion conforms to schema rules...")
    else:
        print("Errors found checking the MetaDataVersion against the schema rules...")


def verify_element_order(mdv):
    try:
        mdv.verify_order()
    except ValueError as ve:
        print(f"Error verifying element order in MetaDataVersion: {ve}")
    else:
        print(f"MetaDataVersion element order is verified")


def main():
    validate_odm_xml_file()
    mdv = load_mdv()
    root = load_root()
    verify_oids(root)
    find_unreferenced_oids(root)
    # TODO schema rules only implemented for metadata at this point
    # verify_schema_rules(root)
    verify_element_order(mdv)


if __name__ == "__main__":
    main()
