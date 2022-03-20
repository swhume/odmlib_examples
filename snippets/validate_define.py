from odmlib import odm_parser as P
import odmlib.define_2_1.rules.oid_ref as OID
import odmlib.define_loader as OL
import odmlib.loader as LD
import odmlib.define_2_1.rules.metadata_schema as METADATA
import xmlschema as XSD
import os

from odmlib.define_2_1.rules import metadata_schema as METADATA
from odmlib.define_2_1.rules import oid_ref as OID


# DEF_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'defineV21-SDTM.xml')
DEF_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 't1d-define.xml')
SCHEMA_FILE = os.path.join(os.sep, 'home', 'sam', 'standards', 'DefineV211', 'schema', 'cdisc-define-2.1', 'define2-1-0.xsd')


def validate_odm_xml_file():
    validator = P.ODMSchemaValidator(SCHEMA_FILE)
    try:
        validator.validate_file(DEF_FILE)
    except XSD.validators.exceptions.XMLSchemaChildrenValidationError as ve:
        print(f"schema validation errors: {ve}")
    else:
        print("Define-XML schema validation completed successfully...")


def load_root():
    loader = LD.ODMLoader(OL.XMLDefineLoader(model_package="define_2_1", ns_uri="http://www.cdisc.org/ns/def/v2.1"))
    loader.open_odm_document(DEF_FILE)
    root = loader.load_odm()
    return root


def load_mdv():
    loader = LD.ODMLoader(OL.XMLDefineLoader(model_package="define_2_1", ns_uri="http://www.cdisc.org/ns/def/v2.1"))
    loader.open_odm_document(DEF_FILE)
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
    verify_element_order(mdv)


if __name__ == "__main__":
    main()
