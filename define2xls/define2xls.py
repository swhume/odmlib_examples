import argparse
import odmlib.define_loader as OL
import odmlib.loader as LD
import excel_define_file as EX
import odmlib.odm_parser as P
import xmlschema as XSD
import os
import study, datasets, variables, value_level as valuelevel, where_clauses as whereclauses, codelists, dictionaries
import methods, comments, documents

WORKSHEETS = ["Study", "Datasets", "Variables", "ValueLevel", "WhereClauses", "CodeLists", "Dictionaries", "Methods",
              "Comments", "Documents"]
EXCEL_NAME = "odmlib-define-metadata.xlsx"

"""
define2xls.py - an example program using odmlib to convert a Define-XML file into a metadata spreadsheet
ex. cmd-line args: -d ./data/sdtm-xls-define.xml -p ./data/
ex. cmd-line args: -d C:\\Users\\shume\\Dropbox\\odm_api\\odm_360\\xls2define\\data\\sdtm-xls-define.xml -p ./data/ -v
-s "C:\\Users\\shume\\Dropbox\\04. XML Tech\\Define-XML\\define_xml_2_0\\define_xml_2_0_releasepackage20140424\\schema\\cdisc-define-2.0\\define2-0-0.xsd"
"""

class Define2Xls:
    """ generate a metadata spreadsheet from a Define-XML v2.0 file """
    def __init__(self, define_file, excel_path, excel_filename=EXCEL_NAME, language="en"):
        self.define_file = define_file
        self.data_path = excel_path
        self.excel_filename = excel_filename
        self.lang = language

    def create(self):
        loader = LD.ODMLoader(OL.XMLDefineLoader())
        loader.open_odm_document(self.define_file)
        mdv_odmlib = loader.MetaDataVersion()
        study_odmlib = loader.Study()
        ws_files = []
        for worksheet in WORKSHEETS:
            if worksheet == "Study":
                ws = eval(worksheet.lower() + "." + worksheet + "(study_odmlib, mdv_odmlib, self.data_path, self.lang)")
            else:
                ws = eval(worksheet.lower() + "." + worksheet + "(mdv_odmlib, self.data_path)")
            ws.extract()
            ws_files.append(ws.file_name)
        self._write_excel(ws_files)

    def _write_excel(self, ws_files):
        excel = EX.ExcelDefineFile(ws_files, WORKSHEETS, self.data_path, self.excel_filename)
        excel.create_excel()


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
    get the command-line arguments needed to convert the Define-XML input file into Excel
    :return: return the argparse object with the command-line parameters
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--define", help="path and file name of Define-XML v2 input file", required=True,
                        dest="define_file")
    parser.add_argument("-p", "--path", help="path to write the generated Excel file to", required=False,
                        dest="excel_path", default="./")
    parser.add_argument("-e", "--excel", help="Name of Excel file without path", required=False,
                        dest="excel_filename", default=EXCEL_NAME)
    parser.add_argument("-s", "--schema", help="path and file name of Define-XML schema", dest="schema_file")
    parser.add_argument("-v", "--validate", help="schema validate the Define-XML file", default=False, const=True,
                        nargs='?', dest="is_validate")
    parser.add_argument("-l", "--lang", help="language code", default="en", dest="language", required=False)
    args = parser.parse_args()
    return args


def main():
    """ main driver method that generates an Excel file using tje Define-XML v2.0 metadata """
    args = set_cmd_line_args()
    if args.is_validate:
        validator = DefineValidator(args.schema_file, args.define_file)
        validator.validate()
    d2x = Define2Xls(args.define_file, args.excel_path, args.excel_filename, args.language)
    d2x.create()


if __name__ == "__main__":
    main()
