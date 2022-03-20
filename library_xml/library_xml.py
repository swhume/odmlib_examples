import requests
import os
import argparse
import odmlib.ns_registry as NS
import odmlib.define_loader as DL
import odmlib.odm_loader as OL

"""
Example Cmd-line Args:
    SDTMIG v3.4: -d -e "/mdr/sdtmig/3-4" -k e5a7d2b9bg1a4066ae4b25133a091574
    CDASHIG v2.2: -e "/mdr/cdashig/2-2" -f library-odmlib-cdashig2-2.json  -k e5a7d2b9bg1a4066ae4b25133a091574
NOTE: you will need to replace the -k arg with our own CDISC Library API key
"""


def write_odm_as_json(odm, filename):
    print(f"Saving {odm.Study[0].GlobalVariables.StudyName} in Library-XML version {odm.LibraryXMLVersion} as JSON")
    with open(filename, 'w') as f:
        f.write(odm.to_json())


def load_odmlib(endpoint, filename, model_package, ns, api_key):
    base_url = "https://library.cdisc.org/api"
    headers = {"Accept": "application/odm+xml", "User-Agent": "crawler", "api-key": api_key}
    r = requests.get(base_url + endpoint, headers=headers)
    if r.status_code == 200:
        if "define" in model_package:
            loader = DL.XMLDefineLoader(model_package=model_package, ns_uri="http://www.cdisc.org/ns/library-xml/v1.0", local_model=True)
        else:
            loader = OL.XMLODMLoader(model_package=model_package, ns_uri="http://www.cdisc.org/ns/library-xml/v1.0", local_model=True)
        loader.create_document_from_string(r.text, ns)
        odm = loader.load_odm()
        write_odm_as_json(odm, filename)
    else:
        if r.status_code == "406":
            print(f"{endpoint} is not available from CDISC Library as odm+xml")
        else:
            print(f"HTTPError {r.status_code} for url {base_url + endpoint}")


def set_cmd_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="json file name to write output", required=False,
                        dest="file_out", default="library-odmlib.json")
    parser.add_argument("-e", "--endpoint", help="CDISC Library API endpoint to retrieve", required=True,
                        dest="endpoint", )
    parser.add_argument("-k", "--apikey", help="the CDISC Library API Key", required=True, dest="api_key")
    parser.add_argument("-d", "--define", help="is the Library-XML content in Define-XML?", default=False, const=True,
                        nargs='?', dest="is_define")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = set_cmd_line_args()
    if args.is_define:
        model_package = "library_define_1_0"
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.1")
    else:
        model_package = "library_odm_1_0"
    ns = NS.NamespaceRegistry(prefix="mdr", uri="http://www.cdisc.org/ns/library-xml/v1.0")

    print(f"Requesting {args.endpoint} from the CDISC Library...")
    odmlib_json_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', args.file_out)
    load_odmlib(args.endpoint, odmlib_json_file, model_package, ns, args.api_key)
