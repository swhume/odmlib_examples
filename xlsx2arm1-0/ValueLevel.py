from odmlib.arm_1_0 import model as DEFINE

import define_object


class ValueLevel(define_object.DefineObject):
    """ create a Define-XML v2.0 ValueListDef element object """
    def __init__(self):
        super().__init__()
        self.lookup_oid = None
        self.vld = None

    def create_define_objects(self, sheet, objects, lang, acrf, suppdocs):
        """
        parse the Excel sheet and create a odmlib objects to return in the objects dictionary
        :param sheet: xlrd Excel sheet object
        :param objects: dictionary of odmlib objects updated by this method
        :param lang: xml:lang setting for TranslatedText
        """
        self.lang = lang
        self.acrf = acrf
        self.sheet = sheet
        header = self.load_header(self.sheet.max_column)
        objects["ValueListDef"] = []
        vl_oid = ""
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=self.sheet.max_column, values_only=True):
            row_content = self.load_row(row, header)
            if vl_oid != row_content["OID"]:
                self._create_valuelistdef_object(row_content, objects)
                vl_oid = row_content["OID"]
            self._create_itemref_object(row_content)
            self._create_itemdef_object(row_content, objects)

    def _create_valuelistdef_object(self, row, objects):
        """
        use the values from the ValueLevel worksheet row to create a ValueListDef odmlib object
        :param row: ValueList worksheet row values as a dictionary
        :param objects: dictionary of odmlib objects updated by this method
        """
        self.vld = DEFINE.ValueListDef(OID=row["OID"])
        objects["ValueListDef"].append(self.vld)

    def _create_itemref_object(self, row):
        """
        use the values from the ValueLevel worksheet row to create ItemRef objects for ValueListDef
        :param row: ValueList worksheet row values as a dictionary
        """
        # oid = self.generate_oid(["IT", row["Dataset"], row["Variable"], row["Where Clause"][3:]])
        attr = {"ItemOID": row["ItemOID"], "Mandatory": row["Mandatory"], "OrderNumber": int(row["Order"])}
        if row.get("Method"):
            attr["MethodOID"] = self.generate_oid(["MT", row["Method"]])
        item = DEFINE.ItemRef(**attr)
        wc = DEFINE.WhereClauseRef(WhereClauseOID=row["Where Clause"])
        item.WhereClauseRef.append(wc)
        self.vld.ItemRef.append(item)

    def _create_itemdef_object(self, row, objects):
        """
        use the values from the ValueLevel worksheet row to create ItemDef objects referenced by ValueListDef ItemRefs
        :param row: ValueList worksheet row values as a dictionary
        :param objects: dictionary of odmlib objects updated by this method
        """
        # oid = self.generate_oid(["IT", row["Dataset"], row["Variable"], row["Where Clause"][3:]])
        attr = {"OID": row["ItemOID"], "Name": row["Variable"], "DataType": row["Data Type"]}
        self._add_optional_itemdef_attributes(attr, row)
        item = DEFINE.ItemDef(**attr)
        self._add_optional_itemdef_elements(item, row)
        objects["ItemDef"].append(item)

    def _add_optional_itemdef_elements(self, item, row):
        """
        use the values from the ValueList worksheet row to add the optional ELEMENTS to the ItemDef object
        :param item: ItemDef odmlib object updated with optional ELEMENTS
        :param row: ValueList worksheet row values as a dictionary
        """
        if row.get("Codelist"):
            cl = DEFINE.CodeListRef(CodeListOID=row.get("Codelist"))
            item.CodeListRef = cl
        if row.get("Origin Type"):
            # spreadsheet input only provides for 1 Origin, but multiple are supported by the spec
            attr = {"Type": row["Origin Type"]}
            if row.get("Origin Source"):
                attr["Source"] = row["Origin Source"]
            item.Origin.append(DEFINE.Origin(**attr))
            if row.get("Predecessor"):
                item.Origin[0].Description = DEFINE.Description()
                item.Origin[0].Description.TranslatedText.append(DEFINE.TranslatedText(_content=row["Predecessor"]))
            if row.get("Pages"):
                dr = DEFINE.DocumentRef(leafID=self.acrf)
                dr.PDFPageRef.append(DEFINE.PDFPageRef(PageRefs=row["Pages"], Type="PhysicalRef"))
                item.Origin[0].DocumentRef.append(dr)

    def _add_optional_itemdef_attributes(self, attr, row):
        """
        use the values from the ValueList worksheet row to add the optional attributes to the ItemDef object
        :param item: ItemDef odmlib object updated with optional attributes
        :param row: ValueList worksheet row values as a dictionary
        """
        if len(row["Variable"]) < 9:
            attr["SASFieldName"] = row["Variable"]
        else:
            print(f"Skipping SASFieldName for ItemDef {row['Variable']} because it exceeds the 8 character limit")
        if row.get("Length"):
            attr["Length"] = row["Length"]
        if row.get("Significant Digits"):
            attr["SignificantDigits"] = row["Significant Digits"]
        if row.get("Format"):
            attr["DisplayFormat"] = row["Format"]
        if row.get("Comment"):
            attr["CommentOID"] = self.generate_oid(["COM", row["Comment"]])
