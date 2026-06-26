"""
This odmlib v0.2.0 snippet was created and used to demonstrate new features that support basic Dataset-JSON v1.1
reading and writing. This feature may be further enhanced prior to v1.0.
"""
import json, jsonschema
from odmlib.dataset_json_1_1 import DatasetJSON, Column, SourceSystem

# create a Dataset-JSON object
dsj = DatasetJSON(
    datasetJSONCreationDateTime="2024-06-28T15:38:43",
    datasetJSONVersion="1.1.0",
    fileOID="www.example.com.DM",
    originator="HDL LLC",
    sourceSystem=SourceSystem(name="odmlib", version="0.2.0"),
    studyOID="CDISCPILOT01",
    metaDataVersionOID="MDV.CDISCPILOT01",
    itemGroupOID="IG.DM",
    records=2,
    name="DM",
    label="Demographics",
    columns=[
        Column(itemOID="IT.STUDYID", name="STUDYID", label="Study Identifier",
               dataType="string", keySequence=1),
        Column(itemOID="IT.AGE", name="AGE", label="Age",
               dataType="integer", length=3),
    ],
    rows=[
        ["CDISCPILOT01", 84],
        ["CDISCPILOT01", 76],
    ],
)

# generate JSON output for review
print(json.dumps(dsj.to_dict(), indent=2))

# write the Dataset-JSON object to a file as NDJSON
dsj.write_ndjson("data/test_dm.ndjson")

# inspect the file
with open("data/test_dm.ndjson") as f:
    for i, line in enumerate(f):
        print(f"Line {i}: {line.rstrip()[:80]}...")

# read in the newly written file, test the round-trip
dsj2 = DatasetJSON.read_ndjson("data/test_dm.ndjson")
assert dsj.to_dict() == dsj2.to_dict()
print("NDJSON round-trip OK")

# validate the Dataset-JSON against the schema - start by loading the schema
with open("schemas/dataset.schema.json") as f:
    schema = json.load(f)

jsonschema.validate(dsj.to_dict(), schema)
print("Schema validation passed")
