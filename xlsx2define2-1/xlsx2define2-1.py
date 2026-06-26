from openpyxl import load_workbook
import argparse

from xmlschema import XMLSchemaValidatorError

import odm as ODM
import supporting_docs as SD
from odmlib import odm_parser as P
from odmlib import (
    OdmlibValidationError, OdmlibOIDError, OdmlibConformanceError,
    create_oid_checker,
)
from odmlib.define_2_1.rules.metadata_schema import MetadataSchema
import os.path
import Study, Standards, Datasets, Variables, ValueLevel, WhereClauses, CodeLists, Dictionaries, Methods, Comments, Documents

ELEMENTS = ["ValueListDef", "WhereClauseDef", "ItemGroupDef", "ItemDef", "CodeList", "MethodDef", "CommentDef", "leaf"]

SHEET_LOADERS = {
    "Study": Study.Study,
    "Standards": Standards.Standards,
    "Datasets": Datasets.Datasets,
    "Variables": Variables.Variables,
    "ValueLevel": ValueLevel.ValueLevel,
    "WhereClauses": WhereClauses.WhereClauses,
    "CodeLists": CodeLists.CodeLists,
    "Dictionaries": Dictionaries.Dictionaries,
    "Methods": Methods.Methods,
    "Comments": Comments.Comments,
    "Documents": Documents.Documents,
}

"""
Example Cmd-line Args:
    example: -e ./data/odmlib-define-metadata.xlsx -d ./data/odmlib-roundtrip-define.xml
    example: -e ./data/odmlib-define-metadata.xlsx -d ./data/odmlib-roundtrip-define.xml -v
             -s "/home/sam/standards/define-xml-2-1/schema/cdisc-define-2.1/define2-1-0.xsd
NOTE: the xlrd library no longer supports .xlsx files and will only work with .xls file
"""


class Xls2Define:
    """ Generate a Define-XML v2.1 file from the SDTM Metadata Worksheet Example Excel file """
    def __init__(self, excel_file, define_file, is_check=False):
        """
        :param excel_file: str - the path and filename for the SDTM metadata worksheet excel input file
        :param define_file: str - the path and filename for the Define-XML v2.1 file to be generated
        :param is_check: boolean - flag that indicates if the conformance checks should be executed
        """
        self.excel_file = excel_file
        self.define_file = define_file
        self.is_check_conformance = is_check
        self._check_file_existence()
        self.workbook = load_workbook(filename=self.excel_file, read_only=True, data_only=True)
        self.lang = "en"
        self.acrf = "LF.acrf"
        self.define_objects = {}

    def create(self):
        """
        public method to create the Define-XML v2.1 file from the excel input file
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
        run odmlib v0.2.0 collect-all-errors validation against the Define-XML content
        :param odm: instantiated odmlib Define-XML model
        """
        oid_checker = create_oid_checker("define_2_1")
        conformance_checker = MetadataSchema()
        # validate() on Study collects OID, conformance, and element-order errors in one pass.
        # The conformance schema is rooted at Study, so we call validate on odm.Study.
        errors = odm.Study.validate(collect_errors=True, oid_checker=oid_checker,
                                    conformance_checker=conformance_checker)
        if errors:
            print(f"Validation found {len(errors)} error(s):")
            for i, err in enumerate(errors, 1):
                print(f"  {i}. {err}")
        else:
            print("Define-XML passes all validation checks (OIDs, conformance, element order)...")
        orphans = oid_checker.check_unreferenced_oids()
        if orphans:
            print(f"Warning: unreferenced OID Defs: {orphans}")

    def _load(self, sheet_name, sheet):
        loader_cls = SHEET_LOADERS.get(sheet_name)
        if loader_cls is None:
            raise OdmlibValidationError(f"Unknown worksheet: {sheet_name}")
        loader = loader_cls()
        loader.create_define_objects(sheet, self.define_objects, self.lang, self.acrf)
        if sheet_name == "Study":
            self.lang = loader.lang
            self.acrf = loader.acrf

    def _build_doc(self):
        """
        after processing the content in the Excel input file organize the odmlib objects for use as a Define-XML v2.1
        :return: instantiated odmlib Define-XML v2.1 model
        """
        odm_elem = ODM.ODM()
        odm = odm_elem.create_define_objects()
        odm.Study = self.define_objects["Study"]
        odm.Study.MetaDataVersion = self.define_objects["MetaDataVersion"]
        odm.Study.MetaDataVersion.Standards = self.define_objects["Standards"]
        supp_docs = SD.SupportingDocuments()
        odm.Study.MetaDataVersion.AnnotatedCRF = supp_docs.create_annotatedcrf(self.acrf)
        if "leaf" in self.define_objects and len(self.define_objects["leaf"]) > 0:
            odm.Study.MetaDataVersion.SupplementalDoc = supp_docs.create_supplementaldoc(self.acrf, self.define_objects["leaf"])
        for elem in ELEMENTS:
            self._load_elements(odm, elem)
        return odm

    def _load_elements(self, odm, elem_name):
        """
        when building the doc, add the instantiated objects to the odmlib MetaDataVersion
        :param odm: odmlib Define-XML objects created to represent Define-XML v2.1
        :param elem_name: name of the element objects to add to MetaDataVersion
        """
        target_list = getattr(odm.Study.MetaDataVersion, elem_name)
        for obj in self.define_objects[elem_name]:
            target_list.append(obj)

    def _write_define(self, odm):
        """
        write the odmlib Define-XML out as an XML file
        :param odm: the instantiated odmlib Define-XML
        """
        odm.write_xml(self.define_file)

    def _check_file_existence(self):
        """ throw an error if the Excel input file cannot be found """
        if not os.path.isfile(self.excel_file):
            raise OdmlibValidationError("The Excel file specified on the command-line cannot be found.")


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
        except P.OdmlibSchemaValidationError as ve:
            print(f"schema validation errors: {ve}")
        except XMLSchemaValidatorError as ve:
            # TODO this should be captured and returned by odmlib - use this Define-XML as a test
            print(f"schema validation errors: {ve}")

    def _check_file_existence(self):
        """ throw an error if the schema of Define-XML file cannot be found """
        if not os.path.isfile(self.schema_file):
            raise OdmlibValidationError("The schema validate flag is set, but the schema file cannot be found.")
        if not os.path.isfile(self.define_file):
            raise OdmlibValidationError("The define-xml file cannot be found.")


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
    parser.add_argument("-s", "--schema", help="path and file name of Define-XML schema", dest="schema_file",
                        default="../schema/cdisc-define-2.1/define2-1-0.xsd")
    parser.add_argument("-c", "--check", help="run the conformance check before creating the Define-XML file",
                        default=False, const=True, nargs='?', dest="is_check")
    parser.add_argument("-v", "--validate", help="schema validate the Define-XML file", default=False, const=True,
                        nargs='?', dest="is_validate")
    args = parser.parse_args()
    return args


def main():
    """ main driver method that generates Define-XML v2.1 from the Excel spreadsheet and optionally validates it """
    args = set_cmd_line_args()
    x2d = Xls2Define(args.excel_file, args.define_file, args.is_check)
    x2d.create()
    if args.is_validate:
        validator = DefineValidator(args.schema_file, args.define_file)
        validator.validate()


if __name__ == "__main__":
    main()
