"""
This odmlib v0.2.0 snippet was created and used to demonstrate new features to convert Define-XML v2.1 metadata
into Pandas DataFrames for easy processing by applications that prefer tabular data structures.
"""
import pandas as pd
from odmlib.dataframe import dataframe_to_dataset_json, dataset_json_to_dataframe
import odmlib.define_loader as DL
import odmlib.loader as LD
from odmlib.dataframe import define_metadata_to_dataframes
from odmlib.dataset_json_1_1.model import DatasetJSON, Column
from odmlib.dataframe import dataset_json_to_dataframe

# load the example define.xml file
loader = LD.ODMLoader(DL.XMLDefineLoader(
    model_package='define_2_1',
    ns_uri='http://www.cdisc.org/ns/def/v2.1',
))
loader.open_odm_document('data/defineV21-SDTM.xml')
odm = loader.root()

# generate the define.xml metadata as Pandas DataFrames
dfs = define_metadata_to_dataframes(odm)

# describe the DataFrames
for name, df in dfs.items():
    print(f"{name}: {len(df)} rows, {len(df.columns)} columns")

# filter variables for a specific dataset
dm_vars = dfs['variables'][dfs['variables']['DatasetOID'] == 'IG.DM']
print(dm_vars[['ItemOID', 'Name', 'DataType', 'Mandatory']].to_string())


# create a DataFrame
df = pd.DataFrame({
    'STUDYID': ['CDISC01', 'CDISC01', 'CDISC01'],
    'USUBJID': ['001', '002', '003'],
    'AGE': [65, 72, 58],
    'WEIGHT': [75.5, 80.0, None],
})

# convert the dataframe to Dataset-JSON
ds = dataframe_to_dataset_json(df, 'DM', 'Demographics', 'IG.DM')
ds.write_json('data/dm.json')

# read the Dataset-JSON dataset and convert it back into a DataFrame
ds2 = DatasetJSON.read_json('data/dm.json')
df2 = dataset_json_to_dataframe(ds2)
print(df2.to_string())

# generate a Dataset-JSON object
ds = DatasetJSON(
    datasetJSONCreationDateTime='2026-03-20T10:00:00Z',
    datasetJSONVersion='1.1.0',
    itemGroupOID='IG.AE',
    records=2,
    name='AE',
    label='Adverse Events',
    columns=[
        Column(itemOID='IT.AETERM', name='AETERM', label='AE Term', dataType='string'),
        Column(itemOID='IT.AESEV', name='AESEV', label='Severity', dataType='string'),
    ],
)
ds.rows = [['Headache', 'MILD'], ['Nausea', 'MODERATE']]

# convert the Dataset-JSON object to a DataFrame
df = dataset_json_to_dataframe(ds)
print(df.to_string())
