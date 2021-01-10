from odmlib.define_2_0 import model as DEFINE
import define_object


class Variables(define_object.DefineObject):
    """ create a Define-XML v2.0 ItemDef element object """
    def __init__(self):
        super().__init__()
        self.lookup_oid = None
        self.igd = None

    def create_define_objects(self, sheet, objects, lang):
        """
        parse the Excel sheet and create a odmlib objects to return in the objects dictionary
        :param sheet: xlrd Excel sheet object
        :param objects: dictionary of odmlib objects updated by this method
        :param lang: xml:lang setting for TranslatedText
        """
        self.lang = lang
        self.sheet = sheet
        header = self.load_header(self.sheet.max_column)
        objects["ItemDef"] = []
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=self.sheet.max_column, values_only=True):
            row_content = self.load_row(row, header)
            item = self._create_itemdef_object(row_content)
            self._create_itemref_object(row_content, objects)
            objects["ItemDef"].append(item)
        self._create_leaf_objects(objects)

    def _create_itemdef_object(self, row):
        """
        use the values from the Variables worksheet row to create a ItemDef odmlib object
        :param row: Variables worksheet row values as a dictionary
        :return: odmlib ItemDef object
        """
        oid = self.generate_oid(["IT", row["Dataset"], row["Variable"]])
        attr = {"OID": oid, "Name": row["Variable"], "DataType": row["Data Type"], "SASFieldName": row["Variable"]}
        self._add_optional_itemdef_attributes(attr, row)
        item = DEFINE.ItemDef(**attr)
        tt = DEFINE.TranslatedText(_content=row["Label"], lang=self.lang)
        item.Description = DEFINE.Description()
        item.Description.TranslatedText.append(tt)
        self._add_optional_itemdef_elements(item, row)
        return item

    def _add_optional_itemdef_elements(self, item, row):
        """
        use the values from the Variables worksheet row to add the optional ELEMENTS to the ItemDef object
        :param item: ItemDef odmlib object updated with optional ELEMENTS
        :param row: Variables worksheet row values as a dictionary
        """
        if row.get("CodeList"):
            cl = DEFINE.CodeListRef(CodeListOID=row["CodeList"])
            item.CodeListRef = cl
        item.Origin = DEFINE.Origin(Type=row["Origin"])
        if row.get("Pages"):
            dr = DEFINE.DocumentRef(leafID="LF.blankcrf")
            pr = DEFINE.PDFPageRef(PageRefs=row["Pages"], Type="PhysicalRef")
            dr.PDFPageRef.append(pr)
            item.Origin.DocumentRef.append(dr)
        if row.get("Predecessor"):
            item.Origin.Description = DEFINE.Description()
            tt = DEFINE.TranslatedText(_content=row["Predecessor"])
            item.Origin.Description.TranslatedText.append(tt)
        if row.get("Valuelist"):
            vl = DEFINE.ValueListRef(ValueListOID=row["Valuelist"])
            item.ValueListRef = vl

    def _add_optional_itemdef_attributes(self, attr, row):
        """
        use the values from the Variables worksheet row to add the optional attributes to the ItemDef object
        :param item: ItemDef odmlib object updated with optional attributes
        :param row: Variables worksheet row values as a dictionary
        """
        if row.get("Length"):
            attr["Length"] = row["Length"]
        if row.get("Significant Digits"):
            attr["SignificantDigits"] = row["Significant Digits"]
        if row.get("Format"):
            attr["DisplayFormat"] = row["Format"]
        if row.get("Comment"):
            attr["CommentOID"] = row["Comment"]

    def _create_itemref_object(self, row, objects):
        """
        use the values from the Variables worksheet row to create the ItemRef object and add it to ItemGroupDef
        :param row: Variables worksheet row values as a dictionary
        :param objects: dictionary of odmlib objects updated by this method
        """
        dataset_oid = self.generate_oid(["IG", row["Dataset"]])
        if dataset_oid != self.lookup_oid:
            self.lookup_oid = dataset_oid
            self.igd = self.find_object(objects["ItemGroupDef"], self.lookup_oid)
        if self.igd is None:
            raise ValueError(f"ItemGroupDef with OID {dataset_oid} is missing from the Datasets tab")
        oid = self.generate_oid(["IT", row["Dataset"], row["Variable"]])
        attr = {"ItemOID": oid, "Mandatory": row["Mandatory"]}
        self._add_optional_itemref_attributes(attr, row)
        item = DEFINE.ItemRef(**attr)
        self.igd.ItemRef.append(item)

    def _add_optional_itemref_attributes(self, attr, row):
        """
        use the values from the Variables worksheet row to add the optional attributes to the attr dictionary
        :param attr: ItemRef object attributes to update with optional values
        :param row: Variables worksheet row values as a dictionary
        """
        if row.get("Method"):
            attr["MethodOID"] = row["Method"]
        if row.get("Order"):
            attr["OrderNumber"] = int(row["Order"])
        if row.get("KeySequence"):
            attr["KeySequence"] = int(row["KeySequence"])
        if row.get("Role"):
            attr["Role"] = row["Role"]

    def _create_leaf_objects(self, objects):
        """
        each ItemGroupDef object in objects is updated to add a leaf object
        :param objects: dictionary of odmlib objects updated by this method
        """
        for igd in objects["ItemGroupDef"]:
            id = self.generate_oid(["LF", igd.Name])
            xpt_name = igd.Name + ".xpt"
            leaf = DEFINE.leaf(ID=id, href=xpt_name.lower())
            title = DEFINE.title(_content=xpt_name.lower())
            leaf.title = title
            igd.leaf = leaf
