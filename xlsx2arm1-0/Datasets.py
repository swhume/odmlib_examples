from odmlib.arm_1_0 import model as DEFINE
import define_object


class Datasets(define_object.DefineObject):
    """ create a Define-XML v2.0 ItemGroupDef element object """
    def __init__(self):
        super().__init__()

    def create_define_objects(self, sheet, objects, lang, acrf, suppdocs):
        """
        parse each row in the Excel sheet and create odmlib objects to return in the objects dictionary
        :param sheet: xlrd Excel sheet object
        :param objects: dictionary of odmlib objects updated by this method
        :param lang: xml:lang setting for TranslatedText
        """
        self.lang = lang
        self.sheet = sheet
        num_cols = self.sheet.max_column
        header = self.load_header(num_cols)
        objects["ItemGroupDef"] = []
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=num_cols, values_only=True):
            row_content = self.load_row(row, header)
            itg = self._create_itemgroupdef_object(row_content)
            objects["ItemGroupDef"].append(itg)

    def _create_itemgroupdef_object(self, row):
        """
        use the values from the Dataset worksheet row to create a ItemGroupDef odmlib object
        NOTE: since this example is based on the SDTMIG sub-class has not been implemented
        :param row: Datasets worksheet row values as a dictionary
        :return: odmlib ItemGroupDef object
        """
        oid = self.generate_oid(["IG", row["Dataset"]])
        attr = {"OID": oid, "Name": row["Dataset"], "Repeating": row["Repeating"],
                "SASDatasetName": row["Dataset"], "IsReferenceData": row["Reference Data"], "Purpose": row["Purpose"],
                "Structure": row["Structure"], "ArchiveLocationID": ".".join(["LF", row["Dataset"]])}
        if row.get("Comment"):
            attr["CommentOID"] = row["Comment"]
        if row.get("IsNonStandard"):
            attr["IsNonStandard"] = row["IsNonStandard"]
        if row.get("StandardOID"):
            attr["StandardOID"] = row["StandardOID"]
        if row.get("HasNoData"):
            attr["HasNoData"] = row["HasNoData"]
        igd = DEFINE.ItemGroupDef(**attr)
        tt = DEFINE.TranslatedText(_content=row["Description"], lang=self.lang)
        igd.Description = DEFINE.Description()
        igd.Description.TranslatedText.append(tt)
        # spreadsheet has up to 1 Class per dataset, but spec allows for nested sub-classes
        if row.get("Class"):
            igd.Class = DEFINE.Class(Name=row["Class"])
        return igd
