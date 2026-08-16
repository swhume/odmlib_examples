import odmlib.define_2_1.model as DEFINE
from odmlib.define_2_1.rules.metadata_schema import MetadataSchema
from odmlib.mode import permissive
from odmlib.odm_parser import ODMSchemaValidator

from odmlib import (
    loader as LD,
    define_loader as DL,
    ErrorCollector,
    create_oid_checker,
    odm_parser as P
)

print("\nCollect-all-errors mode: gathering every validation problem in a single pass")
# define_file = "data/define-360i.xml"
define_file = "data/nonconformant_define21.xml"
loader = LD.ODMLoader(DL.XMLDefineLoader(model_package='define_2_1', ns_uri='http://www.cdisc.org/ns/def/v2.1'))
mdv = DEFINE.MetaDataVersion(OID="MDV.DEMO", Name="Demo MDV", DefineVersion="2.1.0")
validator = P.ODMSchemaValidator(standard="define", version="2.1")

with permissive():
    loader.open_odm_document(define_file)
    odm = loader.root()

checker = create_oid_checker("define_2_1")
conformance = MetadataSchema()

print("\nValidating the model using the OID checker and conformance checks")
# use collect_errors=True to gather all errors
errors = odm.validate(collect_errors=True, oid_checker=checker, conformance_checker=conformance)
if errors:
    print(f"Found {len(errors)} validation error(s):\n")
    for i, err in enumerate(errors, 1):
        print(f"  {i}. [{type(err).__name__}] {err}")
else:
    print("No validation errors found.")

collector = ErrorCollector()

print("\nValidating the file using the XSD schema and showing all errors")
validator = ODMSchemaValidator(standard="define", version="2.1")
for err in validator.xsd.iter_errors(define_file):   # or enumerate every error
    print(err.reason, "@", err.path)