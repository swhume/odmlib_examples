"""Builds odmlib Define-XML objects from intermediate JSON."""

import datetime

from odmlib.define_2_1 import model as DEFINE


class DefineBuilder:
    """Builds odmlib Define-XML objects from intermediate JSON."""

    def __init__(self, intermediate: dict, lang: str = "en"):
        self._data = intermediate
        self._lang = lang

    def build(self):
        """Build and return the complete ODM object tree.

        Returns an odmlib ODM object ready for write_xml().
        """
        odm = self._create_odm()
        odm.Study = self._create_study()
        odm.Study.MetaDataVersion = self._create_metadata_version()
        odm.Study.MetaDataVersion.Standards = self._create_standards()

        # AnnotatedCRF
        acrf_id = self._data["study"].get("annotated_crf", "LF.acrf")
        acrf = DEFINE.AnnotatedCRF()
        acrf.DocumentRef = DEFINE.DocumentRef(leafID=acrf_id)
        odm.Study.MetaDataVersion.AnnotatedCRF = acrf

        # SupplementalDoc
        leaf_objects = self._create_leaves()
        if leaf_objects:
            sdoc = DEFINE.SupplementalDoc()
            for lo in leaf_objects:
                if lo.ID != acrf_id:
                    sdoc.DocumentRef.append(DEFINE.DocumentRef(leafID=lo.ID))
            odm.Study.MetaDataVersion.SupplementalDoc = sdoc

        # Build datasets (ItemGroupDef) first — Variables need to find them
        item_group_defs = self._create_item_group_defs()

        # Build variables (ItemDef + ItemRef added to ItemGroupDef)
        item_defs = self._create_item_defs(item_group_defs)

        # Build value levels (ValueListDef + additional ItemDef)
        value_list_defs, vl_item_defs = self._create_value_list_defs()
        item_defs.extend(vl_item_defs)

        # Build where clauses
        where_clause_defs = self._create_where_clause_defs()

        # Build codelists (from CodeLists + Dictionaries)
        code_lists = self._create_code_lists()

        # Build methods and comments
        method_defs = self._create_method_defs()
        comment_defs = self._create_comment_defs()

        # Create leaf objects for each dataset, add to ItemGroupDef
        self._add_dataset_leaves(item_group_defs)

        # Assembly order per Define-XML v2.1 spec:
        # ValueListDef, WhereClauseDef, ItemGroupDef, ItemDef, CodeList, MethodDef, CommentDef, leaf
        for vld in value_list_defs:
            odm.Study.MetaDataVersion.ValueListDef.append(vld)
        for wcd in where_clause_defs:
            odm.Study.MetaDataVersion.WhereClauseDef.append(wcd)
        for igd in item_group_defs:
            odm.Study.MetaDataVersion.ItemGroupDef.append(igd)
        for item in item_defs:
            odm.Study.MetaDataVersion.ItemDef.append(item)
        for cl in code_lists:
            odm.Study.MetaDataVersion.CodeList.append(cl)
        for md in method_defs:
            odm.Study.MetaDataVersion.MethodDef.append(md)
        for cd in comment_defs:
            odm.Study.MetaDataVersion.CommentDef.append(cd)
        for lf in leaf_objects:
            odm.Study.MetaDataVersion.leaf.append(lf)

        return odm

    def _create_odm(self):
        """Create root ODM element."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return DEFINE.ODM(
            FileOID="ODM.DEFINE21.TEST.001",
            AsOfDateTime=now,
            CreationDateTime=now,
            ODMVersion="1.3.2",
            FileType="Snapshot",
            Originator="Sam Hume",
            SourceSystem="odmlib",
            SourceSystemVersion="0.2",
            Context="Other",
        )

    def _create_study(self):
        """Create Study with GlobalVariables."""
        study_data = self._data["study"]
        study = DEFINE.Study(OID=study_data["oid"])
        gv = DEFINE.GlobalVariables()
        gv.StudyName = DEFINE.StudyName(_content=study_data["study_name"])
        gv.StudyDescription = DEFINE.StudyDescription(_content=study_data["study_description"])
        gv.ProtocolName = DEFINE.ProtocolName(_content=study_data["protocol_name"])
        study.GlobalVariables = gv
        return study

    def _create_metadata_version(self):
        """Create MetaDataVersion."""
        mdv = self._data["metadata_version"]
        return DEFINE.MetaDataVersion(
            OID=mdv["oid"],
            Name=mdv["name"],
            Description=mdv["description"],
            DefineVersion=mdv["define_version"],
        )

    def _create_standards(self):
        """Create Standards container with Standard elements."""
        standards = DEFINE.Standards()
        for s in self._data.get("standards", []):
            attr = {
                "OID": s["oid"],
                "Name": s["name"],
                "Type": s["type"],
                "Version": s["version"],
                "Status": s["status"],
            }
            if s.get("publishing_set"):
                attr["PublishingSet"] = s["publishing_set"]
            if s.get("comment_oid"):
                attr["CommentOID"] = s["comment_oid"]
            standards.Standard.append(DEFINE.Standard(**attr))
        return standards

    def _create_item_group_defs(self) -> list:
        """Create ItemGroupDef elements."""
        igds = []
        for ds in self._data.get("datasets", []):
            attr = {
                "OID": ds["oid"],
                "Name": ds["name"],
                "Repeating": ds["repeating"],
                "Domain": ds["name"],
                "SASDatasetName": ds["name"],
                "IsReferenceData": ds["is_reference_data"],
                "Purpose": ds["purpose"],
                "Structure": ds["structure"],
                "ArchiveLocationID": ds.get("archive_location_id", f"LF.{ds['name']}"),
            }
            if ds.get("comment_oid"):
                attr["CommentOID"] = ds["comment_oid"]
            if ds.get("is_non_standard"):
                attr["IsNonStandard"] = ds["is_non_standard"]
            if ds.get("standard_oid"):
                attr["StandardOID"] = ds["standard_oid"]
            if ds.get("has_no_data"):
                attr["HasNoData"] = ds["has_no_data"]
            igd = DEFINE.ItemGroupDef(**attr)
            igd.Description = DEFINE.Description()
            igd.Description.TranslatedText.append(
                DEFINE.TranslatedText(_content=ds["description"], lang=self._lang)
            )
            if ds.get("class_name"):
                igd.Class = DEFINE.Class(Name=ds["class_name"])
            igds.append(igd)
        return igds

    def _create_item_defs(self, item_group_defs: list) -> list:
        """Create ItemDef elements and add ItemRef to ItemGroupDefs."""
        # Build lookup from OID to ItemGroupDef
        igd_lookup = {}
        for igd in item_group_defs:
            igd_lookup[igd.OID] = igd

        item_defs = []
        seen_oids = set()
        acrf_id = self._data["study"].get("annotated_crf", "LF.acrf")

        for var in self._data.get("variables", []):
            # Create ItemDef (deduplicate by OID)
            if var["oid"] not in seen_oids:
                attr = {
                    "OID": var["oid"],
                    "Name": var["name"],
                    "DataType": var["data_type"],
                    "SASFieldName": var.get("sas_field_name", var["name"]),
                }
                if var.get("length"):
                    attr["Length"] = var["length"]
                if var.get("significant_digits"):
                    attr["SignificantDigits"] = var["significant_digits"]
                if var.get("display_format"):
                    attr["DisplayFormat"] = var["display_format"]
                if var.get("comment_oid"):
                    attr["CommentOID"] = var["comment_oid"]
                item = DEFINE.ItemDef(**attr)
                item.Description = DEFINE.Description()
                item.Description.TranslatedText.append(
                    DEFINE.TranslatedText(_content=var["label"], lang=self._lang)
                )
                # CodeListRef
                if var.get("codelist_oid"):
                    item.CodeListRef = DEFINE.CodeListRef(CodeListOID=var["codelist_oid"])
                # Origin
                if var.get("origin_type"):
                    origin_attr = {"Type": var["origin_type"]}
                    if var.get("origin_source"):
                        origin_attr["Source"] = var["origin_source"]
                    item.Origin.append(DEFINE.Origin(**origin_attr))
                    if var.get("predecessor"):
                        item.Origin[0].Description = DEFINE.Description()
                        item.Origin[0].Description.TranslatedText.append(
                            DEFINE.TranslatedText(_content=var["predecessor"])
                        )
                    if var.get("pages"):
                        dr = DEFINE.DocumentRef(leafID=acrf_id)
                        dr.PDFPageRef.append(
                            DEFINE.PDFPageRef(PageRefs=var["pages"], Type="PhysicalRef")
                        )
                        item.Origin[0].DocumentRef.append(dr)
                # ValueListRef
                if var.get("valuelist_oid"):
                    item.ValueListRef = DEFINE.ValueListRef(ValueListOID=var["valuelist_oid"])
                item_defs.append(item)
                seen_oids.add(var["oid"])

            # Create ItemRef and add to ItemGroupDef
            dataset_oid = f"IG.{var['dataset']}".upper()
            igd = igd_lookup.get(dataset_oid)
            if igd is None:
                raise ValueError(f"ItemGroupDef with OID {dataset_oid} not found for variable {var['name']}")
            ir_attr = {"ItemOID": var["oid"], "Mandatory": var["mandatory"]}
            if var.get("method_oid"):
                ir_attr["MethodOID"] = var["method_oid"]
            if var.get("order"):
                ir_attr["OrderNumber"] = var["order"]
            if var.get("key_sequence"):
                ir_attr["KeySequence"] = var["key_sequence"]
            if var.get("role"):
                ir_attr["Role"] = var["role"]
            if var.get("is_non_standard"):
                ir_attr["IsNonStandard"] = var["is_non_standard"]
            if var.get("has_no_data"):
                ir_attr["HasNoData"] = var["has_no_data"]
            igd.ItemRef.append(DEFINE.ItemRef(**ir_attr))

        return item_defs

    def _create_value_list_defs(self) -> tuple:
        """Create ValueListDef elements with ItemRef children, and associated ItemDefs.

        Returns (value_list_defs, item_defs) tuple.
        """
        vlds = []
        item_defs = []
        current_vld = None
        current_vl_oid = None
        acrf_id = self._data["study"].get("annotated_crf", "LF.acrf")

        for vl in self._data.get("value_levels", []):
            # New ValueListDef?
            if vl["vl_oid"] != current_vl_oid:
                current_vl_oid = vl["vl_oid"]
                current_vld = DEFINE.ValueListDef(OID=current_vl_oid)
                vlds.append(current_vld)

            # Create ItemRef for ValueListDef
            ir_attr = {
                "ItemOID": vl["item_oid"],
                "Mandatory": vl["mandatory"],
                "OrderNumber": vl["order"],
            }
            if vl.get("method_oid"):
                ir_attr["MethodOID"] = vl["method_oid"]
            item_ref = DEFINE.ItemRef(**ir_attr)
            wc = DEFINE.WhereClauseRef(WhereClauseOID=vl["where_clause_oid"])
            item_ref.WhereClauseRef.append(wc)
            current_vld.ItemRef.append(item_ref)

            # Create ItemDef for value-level item
            id_attr = {
                "OID": vl["item_oid"],
                "Name": vl["name"],
                "DataType": vl["data_type"],
            }
            if vl.get("sas_field_name"):
                id_attr["SASFieldName"] = vl["sas_field_name"]
            if vl.get("length"):
                id_attr["Length"] = vl["length"]
            if vl.get("significant_digits"):
                id_attr["SignificantDigits"] = vl["significant_digits"]
            if vl.get("display_format"):
                id_attr["DisplayFormat"] = vl["display_format"]
            if vl.get("comment_oid"):
                id_attr["CommentOID"] = vl["comment_oid"]
            item = DEFINE.ItemDef(**id_attr)
            # Optional elements
            if vl.get("codelist_oid"):
                item.CodeListRef = DEFINE.CodeListRef(CodeListOID=vl["codelist_oid"])
            if vl.get("origin_type"):
                origin_attr = {"Type": vl["origin_type"]}
                if vl.get("origin_source"):
                    origin_attr["Source"] = vl["origin_source"]
                item.Origin.append(DEFINE.Origin(**origin_attr))
                if vl.get("predecessor"):
                    item.Origin[0].Description = DEFINE.Description()
                    item.Origin[0].Description.TranslatedText.append(
                        DEFINE.TranslatedText(_content=vl["predecessor"])
                    )
                if vl.get("pages"):
                    dr = DEFINE.DocumentRef(leafID=acrf_id)
                    dr.PDFPageRef.append(
                        DEFINE.PDFPageRef(PageRefs=vl["pages"], Type="PhysicalRef")
                    )
                    item.Origin[0].DocumentRef.append(dr)
            item_defs.append(item)

        return vlds, item_defs

    def _create_where_clause_defs(self) -> list:
        """Create WhereClauseDef elements with RangeCheck children."""
        wcds = []
        for wc in self._data.get("where_clauses", []):
            attr = {"OID": wc["oid"]}
            if wc.get("comment_oid"):
                attr["CommentOID"] = wc["comment_oid"]
            wcd = DEFINE.WhereClauseDef(**attr)
            for rc_data in wc["range_checks"]:
                rc = DEFINE.RangeCheck(
                    SoftHard="Soft",
                    ItemOID=rc_data["item_oid"],
                    Comparator=rc_data["comparator"],
                )
                for val in rc_data.get("check_values", [""]):
                    rc.CheckValue.append(DEFINE.CheckValue(_content=val))
                wcd.RangeCheck.append(rc)
            wcds.append(wcd)
        return wcds

    def _create_code_lists(self) -> list:
        """Create CodeList elements from both CodeLists and Dictionaries."""
        cls = []
        # Regular codelists with terms (skip stubs with no terms — they violate XSD)
        for cl_data in self._data.get("codelists", []):
            if not cl_data.get("terms"):
                continue
            attr = {
                "OID": cl_data["oid"],
                "Name": cl_data["name"],
                "DataType": cl_data["data_type"],
            }
            if cl_data.get("comment_oid"):
                attr["CommentOID"] = cl_data["comment_oid"]
            if cl_data.get("is_non_standard"):
                attr["IsNonStandard"] = cl_data["is_non_standard"]
            if cl_data.get("standard_oid"):
                attr["StandardOID"] = cl_data["standard_oid"]
            cl = DEFINE.CodeList(**attr)

            has_decode = cl_data.get("has_decode", False)
            for term in cl_data.get("terms", []):
                term_attr = {"CodedValue": term["coded_value"]}
                if term.get("order"):
                    term_attr["OrderNumber"] = term["order"]

                if has_decode:
                    cl_item = DEFINE.CodeListItem(**term_attr)
                    decode = DEFINE.Decode()
                    decoded_value = term.get("decoded_value")
                    if decoded_value:
                        tt = DEFINE.TranslatedText(_content=decoded_value, lang="en")
                    else:
                        tt = DEFINE.TranslatedText(_content=term["coded_value"], lang="en")
                    decode.TranslatedText.append(tt)
                    cl_item.Decode = decode
                    if term.get("nci_term_code"):
                        cl_item.Alias.append(
                            DEFINE.Alias(Context="nci:ExtCodeID", Name=term["nci_term_code"])
                        )
                    cl.CodeListItem.append(cl_item)
                else:
                    en_item = DEFINE.EnumeratedItem(**term_attr)
                    if term.get("nci_term_code"):
                        en_item.Alias.append(
                            DEFINE.Alias(Context="nci:ExtCodeID", Name=term["nci_term_code"])
                        )
                    cl.EnumeratedItem.append(en_item)

            # Add NCI Codelist Code Alias at the end
            if cl_data.get("nci_codelist_code"):
                cl.Alias.append(
                    DEFINE.Alias(Context="nci:ExtCodeID", Name=cl_data["nci_codelist_code"])
                )
            cls.append(cl)

        # External dictionaries
        for d in self._data.get("dictionaries", []):
            cl = DEFINE.CodeList(OID=d["oid"], Name=d["name"], DataType=d["data_type"])
            ecl_attr = {"Dictionary": d["dictionary"]}
            if d.get("version"):
                ecl_attr["Version"] = d["version"]
            cl.ExternalCodeList = DEFINE.ExternalCodeList(**ecl_attr)
            cls.append(cl)

        return cls

    def _create_method_defs(self) -> list:
        """Create MethodDef elements."""
        methods = []
        for m in self._data.get("methods", []):
            method = DEFINE.MethodDef(OID=m["oid"], Name=m["name"], Type=m["type"])
            method.Description = DEFINE.Description()
            method.Description.TranslatedText.append(
                DEFINE.TranslatedText(_content=m["description"], lang=self._lang)
            )
            if m.get("expression_context"):
                method.FormalExpression.append(
                    DEFINE.FormalExpression(
                        Context=m["expression_context"],
                        _content=m.get("expression_code", ""),
                    )
                )
            if m.get("document"):
                dr = DEFINE.DocumentRef(leafID=m["document"])
                if m.get("pages"):
                    dr.PDFPageRef.append(
                        DEFINE.PDFPageRef(PageRefs=m["pages"], Type="NamedDestination")
                    )
                method.DocumentRef.append(dr)
            methods.append(method)
        return methods

    def _create_comment_defs(self) -> list:
        """Create CommentDef elements."""
        comments = []
        for c in self._data.get("comments", []):
            com = DEFINE.CommentDef(OID=c["oid"])
            com.Description = DEFINE.Description()
            com.Description.TranslatedText.append(
                DEFINE.TranslatedText(_content=c["description"], lang=self._lang)
            )
            if c.get("document"):
                dr = DEFINE.DocumentRef(leafID=c["document"])
                if c.get("pages"):
                    dr.PDFPageRef.append(
                        DEFINE.PDFPageRef(PageRefs=c["pages"], Type="NamedDestination")
                    )
                com.DocumentRef.append(dr)
            comments.append(com)
        return comments

    def _create_leaves(self) -> list:
        """Create leaf elements for document references (from Documents worksheet)."""
        leaves = []
        for d in self._data.get("documents", []):
            lf = DEFINE.leaf(ID=d["id"], href=d["href"])
            lf.title = DEFINE.title(_content=d["title"])
            leaves.append(lf)
        return leaves

    def _add_dataset_leaves(self, item_group_defs: list):
        """Add a leaf element to each ItemGroupDef (for dataset transport files)."""
        for igd in item_group_defs:
            # Move Class to end of __dict__ before adding leaf (matches xlsx2define2-1 behavior)
            if "Class" in igd.__dict__:
                igd_class = igd.__dict__.pop("Class")
                igd.Class = igd_class
            leaf_id = f"LF.{igd.Name}".upper()
            xpt_name = igd.Name + ".xpt"
            lf = DEFINE.leaf(ID=leaf_id, href=xpt_name.lower())
            lf.title = DEFINE.title(_content=xpt_name.lower())
            igd.leaf = lf
