"""
This odmlib v0.2.0 snippet was created and used to demonstrate new features to convert Define-XML v2.1 metadata
into Dataset-JSON v1.1 datasets for easy processing by applications that prefer tabular data structures.
"""
import json
import odmlib.define_loader as DL
import odmlib.loader as LD
from odmlib.dataset_json_1_1.define_flattener import DefineFlattener

# load a Define-XML v2.1 file to convert to Dataset-JSON v1.1
loader = LD.ODMLoader(DL.XMLDefineLoader(
    model_package='define_2_1',
    ns_uri='http://www.cdisc.org/ns/def/v2.1',
))
loader.open_odm_document('data/defineV21-SDTM.xml')
odm = loader.root()

# flatten the define.xml metadata
flattener = DefineFlattener(odm)
datasets = flattener.flatten_all()

# inspect each of the metadata datasets
for name, ds in datasets.items():
    print(f"{name}: {ds.records} rows, {len(ds.columns)} columns")

# write out the datasets to files
paths = flattener.write_all("data/")
for p in paths:
    print(p)

# print the column names and values from the study dataset
study = datasets["study"]
print(f"\nstudy dataset column names: {study.column_names}")
print(study.rows[0])
print()

# print the variable OID, name, and data type and for each variable in the DM domain
variables = datasets["variables"]
col_names = variables.column_names
dm_vars = [r for r in variables.rows
           if r[col_names.index("DatasetOID")] == "IG.DM"]
for v in dm_vars:
    print(f"  {v[col_names.index('ItemOID')]}: {v[col_names.index('Name')]} ({v[col_names.index('DataType')]})")


# print the datasets dataset
print("\nFor the datasets dataset, print the entire dictionary as JSON:")
ds = datasets["datasets"]
print(json.dumps(ds.to_dict(), indent=2))

