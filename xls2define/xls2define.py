#import xlrd
from openpyxl import Workbook, load_workbook
import argparse
import odm as ODM
import supporting_docs as SD
from odmlib import odm_parser as P
from odmlib.define_2_0.rules import metadata_schema as METADATA
from odmlib.define_2_0.rules import oid_ref as OID
import xmlschema as XSD
import os.path
import Study, Datasets, Variables, ValueLevel, WhereClauses, CodeLists, Dictionaries, Methods, Comments, Documents

ELEMENTS = ["ValueListDef", "WhereClauseDef", "ItemGroupDef", "ItemDef", "CodeList", "MethodDef", "CommentDef", "leaf"]

"""
Example Cmd-line Args:
    example: -e C:\\Users\\shume\\Dropbox\\odm_api\\odm_360\\define2xls\\data\\odmlib-define-metadata.xls
             -d C:\\Users\\shume\\Dropbox\\odm_api\\odm_360\\xls2define\\data\\odmlib-roundtrip-define.xml

NOTE: the xlrd library no longer supports .xlsx files and will only work with .xls file
"""


class Xls2Define:
    """ Generate a Define-XML v2.0 file from the SDTM Metadata Worksheet Example Excel file """
    def __init__(self, excel_file, define_file, is_check=False):
        """
        :param excel_file: str - the path and filename for the SDTM metadata worksheet excel input file
        :param define_file: str - the path and filename for the Define-XML v2.0 file to be generated
        :param is_check: boolean - flag that indicates if the conformance checks should be executed
        """
        self.excel_file = excel_file
        self.define_file = define_file
        self.is_check_conformance = is_check
        self._check_file_existence()
        self.workbook = load_workbook(filename=self.excel_file, read_only=True, data_only=True)
        self.lang = "en"
        self.define_objects = {}

    def create(self):
        """
        public method to create the Define-XML v2.0 file from the excel input file
        """
        for sheet in self.workbook.worksheets:
            print(sheet.title)
            self._load(sheet.title, sheet)
        odm = self._build_doc()
        if self.is_check_conformance:
            self._conformance_check(odm)
        self._write_define(odm)

    def _conformance_check(self, odm):
        """
        run the conformance rules against the odmlib Define-XML content and report the outcome
        :param odm: instantiated odmlib Define-XML model
        """
        self._check_oids(odm)
        validator = METADATA.MetadataSchema()
        study_dict = odm.Study[0].to_dict()
        try:
            validator.check_conformance(study_dict, "Study")
            print("define-xml passes basic conformance rule check...")
        except ValueError as ve:
            print(f"conformance check rule errors: {ve}")

    def _check_oids(self, odm):
        """
        as part of the conformance check ensure the OIDs are unique, there are Defs for all Refs, and no orphan Defs
        :param odm: instantiated odmlib Define-XML model
        """
        oid_checker = OID.OIDRef()
        odm.verify_oids(oid_checker)
        try:
            if (oid_checker.check_oid_refs()):
                print("OID Refs all check out...")
        except ValueError as ve:
            print(f"OID Ref error: {ve}")

    def _load(self, sheet_name, sheet):
        loader = eval(sheet_name + "." + sheet_name + "()")
        loader.create_define_objects(sheet, self.define_objects, self.lang)
        if sheet_name == "Study":
            self.lang = loader.lang

    def _build_doc(self):
        """
        after processing the content in the Excel input file organize the odmlib objects for use as a Define-XML v2.0
        :return: instantiated odmlib Define-XML v2.0 model
        """
        odm_elem = ODM.ODM()
        odm = odm_elem.create_define_objects()
        odm.Study.append(self.define_objects["Study"])
        odm.Study[0].MetaDataVersion = self.define_objects["MetaDataVersion"]
        supp_docs = SD.SupportingDocuments()
        odm.Study[0].MetaDataVersion.AnnotatedCRF = supp_docs.create_annotatedcrf()
        odm.Study[0].MetaDataVersion.SupplementalDoc = supp_docs.create_supplementaldoc()
        for elem in ELEMENTS:
            self._load_elements(odm, elem)
        return odm

    def _load_elements(self, odm, elem_name):
        """
        when building the doc, add the instantiated objects to the odmlib MetaDataVersion
        :param odm: odmlib Define-XML objects created to represent Define-XML v2.0
        :param elem_name: name of the element objects to add to MetaDataVersion
        """
        for obj in self.define_objects[elem_name]:
            eval("odm.Study[0].MetaDataVersion." + elem_name + ".append(obj)")

    def _write_define(self, odm):
        """
        write the odmlib Define-XML out as an XML file
        :param odm: the instantiated odmlib Define-XML
        """
        odm.write_xml(self.define_file)

    def _check_file_existence(self):
        """ throw an error if the Excel input file cannot be found """
        if not os.path.isfile(self.excel_file):
            raise ValueError("The Excel file specified on the command-line cannot be found.")


class DefineValidator:
    """ Define-XML schema validation """
    def __init__(self, schema, define_file):
        """
        :param schema: str - the path and filename for the Define-XML schema
        :param define_file: str - the path and filename for the Define-XML to validate
        """
        self.schema_file = schema
        self.define_file = define_file

    def validate(self):
        """" execute the schema validation and report the results """
        validator = P.ODMSchemaValidator(self.schema_file)
        try:
            validator.validate_file(self.define_file)
            print("define-XML schema validation completed successfully...")
        except XSD.validators.exceptions.XMLSchemaChildrenValidationError as ve:
            print(f"schema validation errors: {ve}")

    def _check_file_existence(self):
        """ throw an error if the schema of Define-XML file cannot be found """
        if not os.path.isfile(self.schema_file):
            raise ValueError("The schema validate flag is set, but the schema file cannot be found.")
        if not os.path.isfile(self.define_file):
            raise ValueError("The define-xml file cannot be found.")


def set_cmd_line_args():
    """
    get the command-line arguments needed to convert the Excel input file into Define-XML
    :return: return the argparse object with the command-line parameters
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--define", help="path and file name of Define-XML v2 file to create", required=False,
                        dest="define_file", default="./odmlib-define-xml.xml")
    parser.add_argument("-e", "--excel", help="path and file name of Excel file to load", required=True,
                        dest="excel_file", )
    parser.add_argument("-s", "--schema", help="path and file name of Define-XML schema", dest="schema_file")
    parser.add_argument("-c", "--check", help="run the conformance check before creating the Define-XML file",
                        default=False, const=True, nargs='?', dest="is_check")
    parser.add_argument("-v", "--validate", help="schema validate the Define-XML file", default=False, const=True,
                        nargs='?', dest="is_validate")
    args = parser.parse_args()
    return args


def main():
    """ main driver method that generates Define-XML v2.0 from the Excel spreadsheet and optionally validates it """
    args = set_cmd_line_args()
    x2d = Xls2Define(args.excel_file, args.define_file, args.is_check)
    x2d.create()
    if args.is_validate:
        validator = DefineValidator(args.schema_file, args.define_file)
        validator.validate()


if __name__ == "__main__":
    main()
