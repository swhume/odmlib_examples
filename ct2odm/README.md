# ct2odm

Convert a CDISC **Controlled Terminology** tab-delimited (TSV) export into a CT-XML ODM file using
[odmlib](https://github.com/swhume/odmlib) v0.2.0.

The program reads the TSV row-by-row, builds `CodeList` / `EnumeratedItem` objects with the `ct_1_1_1`
model package, and serializes the result with `write_xml()`. It is the inverse of
[`../ct2json/`](../ct2json/).

## v0.2.0 features shown

- Building an ODM media type from scratch with the `ct_1_1_1` model classes.
- Object → XML serialization with `write_xml()`.

## Input format

A tab-delimited file with the CDISC CT columns, including: `Code`, `Codelist Code`,
`Codelist Extensible (Yes/No)`, `CDISC Submission Value`, `CDISC Synonym(s)`, `CDISC Definition`,
and `NCI Preferred Term`. A codelist header row (has `Code` + extensibility but no `Codelist Code`) is
expected before its member terms.

## Prerequisites

```bash
pip install -r requirements.txt
```

(installs `odmlib>=0.2.0rc1`)

## Run

```bash
cd ct2odm
python ct2odm.py -c ./data/sdtm-ct.txt -x ./data/sdtm-ct.xml -s SDTM -d 2021-06-25
```

| Flag | Meaning | Default |
|------|---------|---------|
| `-c` / `--csv` | tab-delimited CT input file | `./data/sdtm-ct.txt` |
| `-x` / `--xml` | CT-XML ODM output file | `./data/sdtm-ct.xml` |
| `-s` / `--standard` | standard name (e.g. `SDTM`) | `SDTM` |
| `-d` / `--date` | CT package date (`YYYY-MM-DD`) | `2021-06-25` |

> The sample input/output files are large (~10 MB+); a full run may take a moment.
