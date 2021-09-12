import argparse
import odmlib.loader as LD
import odmlib.odm_loader as OL
import odmlib.odm_parser as P
import xmlschema as XSD
import os

CT_SCHEMA = "./schema/controlledterminology1-1-1.xsd"

"""
ct2json.py - an example program using odmlib to read a CT-XML ODM file and convert it to JSON.
Command-line examples:
python ct2json.py -x ./data/sdtm-ct.xml -j ./data/sdtm-ct.json
python ct2json.py -v -x ./data/sdtm-ct.xml -j ./data/sdtm-ct.json
python ct2json.py -v -x ./data/sdtm-ct.xml -j ./data/sdtm-ct.json -s "/home/sam/src/ct2json/schema/controlledterminology1-1-1.xsd
"""


class CT2Json:
    """ generate a CT JSON file from a CT-XML ODM file """
    def __init__(self, ct_file, json_file, language="en"):
        self.ct_file = ct_file
        self.json_file = json_file
        self.lang = language

    def create(self):
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="ct_1_1_1", ns_uri="http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC"))
        loader.open_odm_document(self.ct_file)
        ct_odmlib = loader.root()
        ct_odmlib.write_json(self.json_file)


class CTValidator:
    """ CT-XML schema validation """
    def __init__(self, schema, ct_file):
        """
        :param schema: str - the path and filename for the Define-XML schema
        :param define_file: str - the path and filename for the Define-XML to validate
        """
        self.schema_file = schema
        self.ct_file = ct_file

    def validate(self):
        """" execute the schema validation and report the results """
        validator = P.ODMSchemaValidator(self.schema_file)
        try:
            validator.validate_file(self.ct_file)
            print("CT-XML schema validation completed successfully...")
        except XSD.validators.exceptions.XMLSchemaChildrenValidationError as ve:
            print(f"schema validation errors: {ve}")

    def _check_file_existence(self):
        """ throw an error if the schema of Define-XML file cannot be found """
        if not os.path.isfile(self.schema_file):
            raise ValueError("The schema validate flag is set, but the schema file cannot be found.")
        if not os.path.isfile(self.ct_file):
            raise ValueError("The CT-XML file cannot be found.")


def set_cmd_line_args():
    """
    get the command-line arguments needed to convert the CT-XML input file into JSON
    :return: return the argparse object with the command-line parameters
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-x", "--ct", help="path and file name of CT-XML input file", required=True,
                        dest="ct_file")
    parser.add_argument("-j", "--json", help="path and file to write the generated JSON file to", required=False,
                        dest="json_file", default="./")
    parser.add_argument("-s", "--schema", help="path and file name of CT-XML schema", dest="schema_file",
                        default=CT_SCHEMA)
    parser.add_argument("-v", "--validate", help="schema validate the CT-XML file", default=False, const=True,
                        nargs='?', dest="is_validate")
    parser.add_argument("-l", "--lang", help="language code", default="en", dest="language", required=False)
    args = parser.parse_args()
    return args


def main():
    """ main driver method that generates an Excel file using tje Define-XML v2.0 metadata """
    args = set_cmd_line_args()
    if args.is_validate:
        validator = CTValidator(args.schema_file, args.ct_file)
        validator.validate()
    ct2json = CT2Json(args.ct_file, args.json_file, args.language)
    ct2json.create()


if __name__ == "__main__":
    main()
