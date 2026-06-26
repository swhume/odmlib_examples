"""
This odmlib v0.2.0 snippet was created and used to validate a 360i define.xml file that functions as a template.
The define.xml template file has placeholders that do not conform the the Define-XML v2.1 data types or value lists.
So, permissive mode is needed to load the define.xml file, and a method to collect all errors provides a useful
way to understand the state of the define.xml template file.
"""
from odmlib import (
    loader as LD,
    define_loader as DL,
    create_oid_checker,
    OdmlibValidationError,
    OdmlibOIDError,
    odm_parser as P
)
from odmlib.mode import permissive

# this 360i define.xml contains placeholders making it a template that is non-conformant to Define-XML v2.1
define_file = "data/define-360i.xml"
output_file = "data/intermediate.xml"
# create the needed odmlib objects
checker = create_oid_checker("define_2_1")
loader = LD.ODMLoader(DL.XMLDefineLoader(model_package='define_2_1', ns_uri='http://www.cdisc.org/ns/def/v2.1'))
validator = P.ODMSchemaValidator(standard="define", version="2.1")

# schema validate the define.xml and collect all validation errors
errors = list(validator.xsd.iter_errors(define_file))
# print out each validation error and report how many are due to the PLACEHOLDER content
placeholder_counter = 0
print(f"Found {len(errors)} schema validation errors:\n")
for i, error in enumerate(errors, 1):
    print(f"{i}. {error.reason}")
    print(f"   Path: {error.path}")
    print()
    if "__PLACEHOLDER__" in error.reason:
            placeholder_counter += 1
print(f"___PLACEHOLDER___ accounted for {placeholder_counter} of the errors.\n")

# open the define.xml using permissive mode (will not load in strict mode) and find all OID errors
with permissive():
    loader.open_odm_document(define_file)
    odm = loader.root()

print(f"Loaded non-conformant ODM: {odm.FileOID}")
try:
    oid_errors = odm.validate(collect_errors=True, oid_checker=checker)
    if oid_errors:
        print(f"Found {len(oid_errors)} validation error(s):\n")
        for i, err in enumerate(oid_errors, 1):
            print(f"  {i}. [{type(err).__name__}] {err}")
    else:
        print("No validation errors found.")
except OdmlibValidationError as e:
    print(f"Validation failed with {type(e).__name__}: {e}")
