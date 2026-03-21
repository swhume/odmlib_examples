from odmlib.arm_1_0 import model as DEFINE
import define_object


class Standards(define_object.DefineObject):
    """ create a Define-XML v2.1 Standards element object """
    def __init__(self):
        super().__init__()

    def create_define_objects(self, sheet, objects, lang, acrf, suppdocs):
        """
        parse each row in the Standards Excel sheet and create odmlib objects to return in the objects dictionary
        :param sheet: Excel sheet object
        :param objects: dictionary of odmlib objects updated by this method
        :param lang: xml:lang setting for TranslatedText
        """
        standards = DEFINE.Standards()
        self.lang = lang
        self.sheet = sheet
        header = self.load_header(self.sheet.max_column)
        objects["ItemGroupDef"] = []
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=self.sheet.max_column, values_only=True):
            if row[0]:
                row_content = self.load_row(row, header)
                std = self._create_standard_object(row_content)
                standards.Standard.append(std)
        objects["Standards"] = standards

    def _create_standard_object(self, row):
        """
        use the values from the Standards worksheet row to create a Standard odmlib object
        :param row: Standards worksheet row values as a dictionary
        :return: odmlib Standard object
        """
        attr = {"OID": row["OID"], "Name": row["Name"], "Type": row["Type"], "Status": row["Status"],
                "Version": str(row["Version"]), }
        if row.get("Publishing Set"):
            attr["PublishingSet"] = row["Publishing Set"]
        if row.get("Comment"):
            attr["CommentOID"] = row["Comment"]
        return DEFINE.Standard(**attr)
