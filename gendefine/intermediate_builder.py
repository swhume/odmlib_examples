"""Builds the intermediate JSON from raw spreadsheet data and mapping config."""

import logging

from config_loader import MappingConfig
from oid_generator import OIDGenerator
from value_transformer import ValueTransformer

logger = logging.getLogger(__name__)


class IntermediateBuilder:
    """Builds the intermediate JSON from raw spreadsheet data and mapping config."""

    def __init__(self, config: MappingConfig, oid_generator: OIDGenerator,
                 value_transformer: ValueTransformer):
        self._config = config
        self._oid_gen = oid_generator
        self._transformer = value_transformer
        self._oid_strategy = config.global_settings.get("oid_generation_strategy", "column")
        self._where_clause_source = config.global_settings.get("where_clause_source", "worksheet")
        # Key variables lookup: dataset name -> ordered list of key variable names
        self._key_variables = {}

    @staticmethod
    def _generate_oid(descriptors: list[str]) -> str:
        """Generate an OID from descriptors, avoiding double-prefixing.

        Replicates the behavior of xlsx2define2-1/define_object.py:generate_oid().
        If the second descriptor already starts with the first descriptor + ".",
        the prefix is not prepended again.
        """
        if len(descriptors) > 1 and descriptors[1].startswith(descriptors[0] + "."):
            return ".".join(descriptors[1:]).upper()
        return ".".join(descriptors).upper()

    def _find_worksheet_data(self, raw_data: dict, *candidate_names: str) -> list | dict:
        """Find worksheet data by trying multiple candidate names.

        Returns the data for the first matching name, or an empty list/dict.
        """
        for name in candidate_names:
            if name in raw_data:
                return raw_data[name]
        return []

    def build(self, raw_data: dict) -> dict:
        """Build the complete intermediate JSON from raw spreadsheet data.

        :param raw_data: Output from SpreadsheetReader.read_workbook()
        :returns: Normalized intermediate JSON structure
        """
        intermediate = {
            "gendefine_version": "1.0",
            "source_mapping": self._config.mapping_name,
        }

        # Study metadata — could be "Study" or "Standard" worksheet
        study_data = self._find_worksheet_data(raw_data, "Study", "Standard")
        if isinstance(study_data, list):
            study_data = {}
        intermediate["study"] = self._build_study(study_data)
        intermediate["metadata_version"] = self._build_metadata_version(study_data)

        # Standards
        if self._oid_strategy == "pattern":
            intermediate["standards"] = self._build_standards_from_study(study_data)
        else:
            intermediate["standards"] = self._build_standards(raw_data.get("Standards", []))

        # Datasets (also extracts key variables for pattern mode)
        intermediate["datasets"] = self._build_datasets(raw_data.get("Datasets", []))

        # Variables
        intermediate["variables"] = self._build_variables(raw_data.get("Variables", []))

        # Value Levels and inline Where Clauses
        vl_raw = raw_data.get("ValueLevel", [])
        if self._where_clause_source == "inline" and vl_raw:
            intermediate["value_levels"], inline_wcs = self._build_value_levels_inline(vl_raw)
            intermediate["where_clauses"] = inline_wcs
        else:
            intermediate["value_levels"] = self._build_value_levels(vl_raw)
            intermediate["where_clauses"] = self._build_where_clauses(
                raw_data.get("WhereClauses", []))

        # CodeLists — from worksheet or generate stubs from variable references
        cl_raw = raw_data.get("CodeLists", [])
        if cl_raw:
            intermediate["codelists"] = self._build_codelists(cl_raw)
        else:
            intermediate["codelists"] = self._build_codelist_stubs(
                intermediate["variables"], intermediate["value_levels"])

        # Dictionaries
        intermediate["dictionaries"] = self._build_dictionaries(
            raw_data.get("Dictionaries", []))

        # Methods
        intermediate["methods"] = self._build_methods(raw_data.get("Methods", []))

        # Comments
        intermediate["comments"] = self._build_comments(raw_data.get("Comments", []))

        # Documents
        intermediate["documents"] = self._build_documents(raw_data.get("Documents", []))

        return intermediate

    def _build_study(self, raw_data: dict) -> dict:
        """Build study metadata from Study worksheet data."""
        study_name = raw_data.get("StudyName", "")
        return {
            "oid": f"ODM.{study_name}".upper(),
            "study_name": study_name,
            "study_description": raw_data.get("StudyDescription", ""),
            "protocol_name": raw_data.get("ProtocolName", ""),
            "language": raw_data.get("Language",
                                     self._config.global_settings.get("language", "en")),
            "annotated_crf": raw_data.get("Annotated CRF",
                                          self._config.global_settings.get("annotated_crf_leaf_id", "LF.acrf")),
        }

    def _build_metadata_version(self, study_data: dict) -> dict:
        """Build MetaDataVersion from study data."""
        study_name = study_data.get("StudyName", "")
        return {
            "oid": f"MDV.{study_name}".upper(),
            "name": f"MDV {study_name}",
            "description": f"Data Definitions for {study_name}",
            "define_version": "2.1.0",
        }

    def _build_standards(self, raw_rows: list) -> list[dict]:
        """Build standards list from a dedicated Standards worksheet."""
        standards = []
        for row in raw_rows:
            if row.get("OID") is None:
                continue
            std = {
                "oid": row["OID"],
                "name": row["Name"],
                "type": row["Type"],
                "version": str(row["Version"]),
                "status": row["Status"],
            }
            if row.get("Publishing Set"):
                std["publishing_set"] = row["Publishing Set"]
            if row.get("Comment"):
                std["comment_oid"] = row["Comment"]
            standards.append(std)
        return standards

    def _build_standards_from_study(self, study_data: dict) -> list[dict]:
        """Build standards list from Study/Standard worksheet data (pattern mode).

        When no Standards worksheet exists, generate a single Standard from the study data.
        """
        std_name = study_data.get("StandardName", "")
        std_version = study_data.get("StandardVersion", "")
        if not std_name:
            return []
        defaults = self._config.defaults
        return [{
            "oid": "STD.1",
            "name": std_name,
            "type": defaults.get("StandardType", "IG"),
            "version": str(std_version),
            "status": defaults.get("StandardStatus", "Final"),
        }]

    def _build_datasets(self, raw_rows: list) -> list[dict]:
        """Build dataset definitions."""
        datasets = []
        for row in raw_rows:
            ds_name = row.get("Dataset", "")
            ds = {
                "oid": f"IG.{ds_name}".upper(),
                "name": ds_name,
                "description": row.get("Description", ""),
                "structure": row.get("Structure", ""),
                "purpose": row.get("Purpose",
                                   self._config.defaults.get("Purpose", "Tabulation")),
                "repeating": row.get("Repeating",
                                     self._config.defaults.get("Repeating", "No")),
                "is_reference_data": row.get("Reference Data",
                                             self._config.defaults.get("IsReferenceData", "No")),
                "archive_location_id": f"LF.{ds_name}",
            }
            if row.get("Class"):
                ds["class_name"] = row["Class"]
            if row.get("Subclass"):
                ds["subclass_name"] = row["Subclass"]
            if row.get("Comment"):
                ds["comment_oid"] = row["Comment"]
            if row.get("IsNonStandard"):
                ds["is_non_standard"] = row["IsNonStandard"]
            if row.get("StandardOID"):
                ds["standard_oid"] = row["StandardOID"]
            if row.get("HasNoData"):
                ds["has_no_data"] = row["HasNoData"]

            # Parse Key Variables for this dataset
            key_vars_str = row.get("Key Variables", "")
            if key_vars_str:
                key_vars = [v.strip() for v in str(key_vars_str).split(",") if v.strip()]
                self._key_variables[ds_name] = key_vars

            datasets.append(ds)
        return datasets

    def _build_variables(self, raw_rows: list) -> list[dict]:
        """Build variable definitions."""
        variables = []
        for row in raw_rows:
            # For column-based strategy, OID comes from the spreadsheet
            # For pattern-based strategy, generate OID from Dataset + Variable
            if self._oid_strategy == "column":
                if row.get("OID") is None:
                    continue
                oid = row["OID"]
            else:
                dataset = row.get("Dataset", "")
                variable = row.get("Variable", "")
                oid = f"IT.{dataset}.{variable}".upper()

            dataset = row.get("Dataset", "")
            variable_name = row.get("Variable", "")

            # Handle Mandatory — could come directly or via Core transform
            mandatory = row.get("Mandatory")
            if mandatory is None:
                core = row.get("Core")
                if core:
                    mandatory = self._transformer.transform(core, "core_to_mandatory")
                else:
                    mandatory = self._config.defaults.get("Mandatory", "No")

            var = {
                "oid": oid,
                "dataset": dataset,
                "name": variable_name,
                "label": row.get("Label", ""),
                "data_type": row.get("Data Type", ""),
                "sas_field_name": variable_name,
                "mandatory": mandatory,
            }
            if row.get("Length"):
                var["length"] = row["Length"]
            if row.get("Significant Digits"):
                var["significant_digits"] = row["Significant Digits"]
            if row.get("Format"):
                var["display_format"] = row["Format"]
            if row.get("Order"):
                var["order"] = int(row["Order"])

            # Key Sequence: from column or from dataset's key variables list
            if row.get("KeySequence"):
                var["key_sequence"] = int(row["KeySequence"])
            elif dataset in self._key_variables:
                key_vars = self._key_variables[dataset]
                if variable_name in key_vars:
                    var["key_sequence"] = key_vars.index(variable_name) + 1

            # Codelist reference
            codelist_ref = row.get("CodeList") or row.get("Codelist")
            if codelist_ref:
                if self._oid_strategy == "pattern":
                    var["codelist_oid"] = f"CL.{codelist_ref}".upper()
                else:
                    var["codelist_oid"] = codelist_ref

            if row.get("Valuelist"):
                var["valuelist_oid"] = row["Valuelist"]
            if row.get("Origin Type"):
                var["origin_type"] = row["Origin Type"]
            if row.get("Origin Source"):
                var["origin_source"] = row["Origin Source"]
            if row.get("Pages"):
                var["pages"] = row["Pages"]
            if row.get("Method"):
                if self._oid_strategy == "pattern":
                    var["method_oid"] = f"MT.{row['Method']}".upper()
                else:
                    var["method_oid"] = row["Method"]
            if row.get("Predecessor"):
                var["predecessor"] = row["Predecessor"]
            if row.get("Role"):
                var["role"] = row["Role"]
            if row.get("Comment"):
                if self._oid_strategy == "pattern":
                    var["comment_oid"] = f"COM.{row['Comment']}".upper()
                else:
                    var["comment_oid"] = row["Comment"]
            if row.get("IsNonStandard"):
                var["is_non_standard"] = row["IsNonStandard"]
            if row.get("HasNoData"):
                var["has_no_data"] = row["HasNoData"]
            variables.append(var)
        return variables

    def _build_value_levels(self, raw_rows: list) -> list[dict]:
        """Build value-level definitions from a worksheet with explicit OIDs."""
        value_levels = []
        for row in raw_rows:
            vl = {
                "vl_oid": row["OID"],
                "item_oid": row["ItemOID"],
                "dataset": row["Dataset"],
                "name": row["Variable"],
                "data_type": row["Data Type"],
                "mandatory": row["Mandatory"],
                "order": int(row["Order"]),
                "where_clause_oid": row["Where Clause"],
            }
            # SASFieldName: only if <= 8 chars
            if len(row["Variable"]) <= 8:
                vl["sas_field_name"] = row["Variable"]
            if row.get("Method"):
                vl["method_oid"] = self._generate_oid(["MT", row["Method"]])
            if row.get("Codelist"):
                vl["codelist_oid"] = row["Codelist"]
            if row.get("Origin Type"):
                vl["origin_type"] = row["Origin Type"]
            if row.get("Origin Source"):
                vl["origin_source"] = row["Origin Source"]
            if row.get("Pages"):
                vl["pages"] = row["Pages"]
            if row.get("Predecessor"):
                vl["predecessor"] = row["Predecessor"]
            if row.get("Length"):
                vl["length"] = row["Length"]
            if row.get("Significant Digits"):
                vl["significant_digits"] = row["Significant Digits"]
            if row.get("Format"):
                vl["display_format"] = row["Format"]
            if row.get("Comment"):
                vl["comment_oid"] = self._generate_oid(["COM", row["Comment"]])
            value_levels.append(vl)
        return value_levels

    def _build_value_levels_inline(self, raw_rows: list) -> tuple[list[dict], list[dict]]:
        """Build value-level definitions with inline where clause parsing.

        Returns (value_levels, where_clauses) tuple.
        """
        from where_clause_parser import WhereClauseParser

        parser = WhereClauseParser()
        value_levels = []
        # Track unique where clause expressions -> OID
        wc_expression_map = {}
        where_clauses = []
        wc_counter = 0

        for row in raw_rows:
            dataset = row.get("Dataset", "")
            variable = row.get("Variable", "")
            wc_expr = row.get("Where Clause", "")
            order = int(row.get("Order", 0))

            # Handle Mandatory via Core transform if needed
            mandatory = row.get("Mandatory")
            if mandatory is None:
                core = row.get("Core")
                if core:
                    mandatory = self._transformer.transform(core, "core_to_mandatory")
                else:
                    mandatory = self._config.defaults.get("Mandatory", "No")

            # Generate OIDs
            vl_oid = f"VL.{dataset}.{variable}".upper()
            item_oid = f"IT.{dataset}.{variable}".upper()

            # Parse inline where clause and get/create OID
            wc_oid = ""
            if wc_expr:
                if wc_expr in wc_expression_map:
                    wc_oid = wc_expression_map[wc_expr]
                else:
                    wc_counter += 1
                    conditions = parser.parse(wc_expr, dataset)
                    if conditions:
                        first = conditions[0]
                        val = first["value"]
                        if isinstance(val, list):
                            val = val[0]
                        wc_oid = f"WC.{dataset}.{first['variable']}.{val}".upper()

                        range_checks = []
                        for cond in conditions:
                            cond_item_oid = f"IT.{cond['dataset']}.{cond['variable']}".upper()
                            check_values = cond["value"] if isinstance(cond["value"], list) else [cond["value"]]
                            range_checks.append({
                                "item_oid": cond_item_oid,
                                "comparator": cond["comparator"],
                                "check_values": check_values,
                            })

                        where_clauses.append({
                            "oid": wc_oid,
                            "range_checks": range_checks,
                        })
                        wc_expression_map[wc_expr] = wc_oid

                # Make item_oid unique by appending where clause info
                if conditions:
                    first = conditions[0]
                    val = first["value"]
                    if isinstance(val, list):
                        val = val[0]
                    item_oid = f"IT.{dataset}.{variable}.{first['variable']}.{val}".upper()

            vl = {
                "vl_oid": vl_oid,
                "item_oid": item_oid,
                "dataset": dataset,
                "name": variable,
                "data_type": row.get("Data Type", ""),
                "mandatory": mandatory,
                "order": order,
                "where_clause_oid": wc_oid,
            }
            if len(variable) <= 8:
                vl["sas_field_name"] = variable
            if row.get("Method"):
                vl["method_oid"] = f"MT.{row['Method']}".upper()
            if row.get("Codelist"):
                vl["codelist_oid"] = f"CL.{row['Codelist']}".upper()
            if row.get("Origin Type"):
                vl["origin_type"] = row["Origin Type"]
            if row.get("Origin Source"):
                vl["origin_source"] = row["Origin Source"]
            if row.get("Pages"):
                vl["pages"] = row["Pages"]
            if row.get("Predecessor"):
                vl["predecessor"] = row["Predecessor"]
            if row.get("Length"):
                vl["length"] = row["Length"]
            if row.get("Significant Digits"):
                vl["significant_digits"] = row["Significant Digits"]
            if row.get("Format"):
                vl["display_format"] = row["Format"]
            if row.get("Comment"):
                vl["comment_oid"] = f"COM.{row['Comment']}".upper()
            value_levels.append(vl)

        return value_levels, where_clauses

    def _build_where_clauses(self, raw_rows: list) -> list[dict]:
        """Build where clause definitions, handling grouping by OID."""
        where_clauses = []
        current_wc = None
        for row in raw_rows:
            oid = row["OID"]
            range_check = {
                "item_oid": self._generate_oid(["IT", row["Dataset"], row["Variable"]]),
                "comparator": row["Comparator"],
            }
            # Parse values
            value_str = row.get("Value", "")
            if value_str:
                range_check["check_values"] = [v.strip() for v in str(value_str).split(", ")]
            else:
                range_check["check_values"] = [""]

            if current_wc is None or current_wc["oid"] != oid:
                # New WhereClauseDef
                current_wc = {
                    "oid": oid,
                    "range_checks": [range_check],
                }
                if row.get("Comment"):
                    current_wc["comment_oid"] = self._generate_oid(["COM", row["Comment"]])
                where_clauses.append(current_wc)
            else:
                current_wc["range_checks"].append(range_check)
        return where_clauses

    def _build_codelists(self, raw_rows: list) -> list[dict]:
        """Build codelist definitions, handling grouping by name."""
        codelists = []
        current_cl = None
        current_name = None

        for row in raw_rows:
            name = row.get("Name")
            if name != current_name:
                # Finalize previous codelist
                if current_cl is not None:
                    codelists.append(current_cl)
                # Start new codelist
                current_name = name
                current_cl = {
                    "oid": row["OID"],
                    "name": row["Name"],
                    "data_type": row["Data Type"],
                    "terms": [],
                }
                if row.get("Comment"):
                    current_cl["comment_oid"] = row["Comment"]
                if row.get("IsNonStandard"):
                    current_cl["is_non_standard"] = row["IsNonStandard"]
                if row.get("StandardOID"):
                    current_cl["standard_oid"] = row["StandardOID"]
                if row.get("NCI Codelist Code"):
                    current_cl["nci_codelist_code"] = row["NCI Codelist Code"]
                # Determine if this codelist uses decoded values
                current_cl["has_decode"] = bool(row.get("Decoded Value"))

            # Add term
            term = {
                "coded_value": row["Term"],
            }
            if row.get("Order"):
                term["order"] = row["Order"]
            if row.get("NCI Term Code"):
                term["nci_term_code"] = row["NCI Term Code"]
            if row.get("Decoded Value"):
                term["decoded_value"] = row["Decoded Value"]
            current_cl["terms"].append(term)

        # Don't forget the last codelist
        if current_cl is not None:
            codelists.append(current_cl)
        return codelists

    def _build_codelist_stubs(self, variables: list[dict],
                               value_levels: list[dict]) -> list[dict]:
        """Generate codelist stubs from codelist references in variables and value levels.

        Used when no CodeLists worksheet exists in the spreadsheet.
        """
        codelist_names = set()

        for var in variables:
            cl_oid = var.get("codelist_oid", "")
            if cl_oid:
                codelist_names.add(cl_oid)

        for vl in value_levels:
            cl_oid = vl.get("codelist_oid", "")
            if cl_oid:
                codelist_names.add(cl_oid)

        if not codelist_names:
            return []

        stubs = []
        for cl_oid in sorted(codelist_names):
            # Extract name from OID (e.g., "CL.SEX" -> "SEX", or use as-is)
            if cl_oid.startswith("CL."):
                name = cl_oid[3:]
            else:
                name = cl_oid
            stubs.append({
                "oid": cl_oid,
                "name": name,
                "data_type": "text",
                "terms": [],
                "has_decode": False,
            })

        if stubs:
            logger.warning(
                "Generated %d codelist stub(s) — terms are not populated: %s",
                len(stubs), ", ".join(s["name"] for s in stubs)
            )
        return stubs

    def _build_dictionaries(self, raw_rows: list) -> list[dict]:
        """Build external dictionary codelist definitions."""
        dictionaries = []
        for row in raw_rows:
            d = {
                "oid": row["OID"],
                "name": row["Name"],
                "data_type": row["Data Type"],
                "dictionary": row["Dictionary"],
            }
            if row.get("Version"):
                d["version"] = row["Version"]
            dictionaries.append(d)
        return dictionaries

    def _build_methods(self, raw_rows: list) -> list[dict]:
        """Build method definitions."""
        methods = []
        for row in raw_rows:
            # OID from column or generate from pattern
            if self._oid_strategy == "column":
                oid = row["OID"]
            else:
                oid = f"MT.{row['Name']}".upper()

            m = {
                "oid": oid,
                "name": row["Name"],
                "type": row["Type"],
                "description": row["Description"],
            }
            if row.get("Expression Context"):
                m["expression_context"] = row["Expression Context"]
                m["expression_code"] = row.get("Expression Code", "")
            if row.get("Document"):
                m["document"] = row["Document"]
                m["pages"] = row.get("Pages")
            methods.append(m)
        return methods

    def _build_comments(self, raw_rows: list) -> list[dict]:
        """Build comment definitions."""
        comments = []
        for i, row in enumerate(raw_rows, 1):
            # OID from column or generate from pattern
            if self._oid_strategy == "column":
                oid = row["OID"]
            else:
                oid = f"COM.{i}"

            c = {
                "oid": oid,
                "description": row["Description"],
            }
            if row.get("Document"):
                c["document"] = row["Document"]
                if row.get("Pages"):
                    c["pages"] = row["Pages"]
            comments.append(c)
        return comments

    def _build_documents(self, raw_rows: list) -> list[dict]:
        """Build document/leaf definitions."""
        documents = []
        for row in raw_rows:
            documents.append({
                "id": row["ID"],
                "title": row["Title"],
                "href": row["Href"],
            })
        return documents
