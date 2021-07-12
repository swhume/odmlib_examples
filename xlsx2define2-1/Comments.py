from odmlib.define_2_1 import model as DEFINE
import define_object


class Comments(define_object.DefineObject):
    """ create a Define-XML v2.0 CommentDef element object """
    def __init__(self):
        super().__init__()
        self.lookup_oid = None
        self.igd = None

    def create_define_objects(self, sheet, objects, lang, acrf):
        """
        parse the Excel sheet and create a odmlib objects to return in the objects dictionary
        :param sheet: xlrd Excel sheet object
        :param objects: dictionary of odmlib objects updated by this method
        :param lang: xml:lang setting for TranslatedText
        """
        self.lang = lang
        self.sheet = sheet
        header = self.load_header(self.sheet.max_column)
        objects["CommentDef"] = []
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=self.sheet.max_column, values_only=True):
            row_content = self.load_row(row, header)
            comment = self._create_commentdef_object(row_content)
            objects["CommentDef"].append(comment)

    def _create_commentdef_object(self, row):
        """
        use the values from the Comments worksheet row to create a CommentDef odmlib object
        :param row: Comments worksheet row values as a dictionary
        :return: a CommentDef odmlib object
        """
        com = DEFINE.CommentDef(OID=row["OID"])
        tt = DEFINE.TranslatedText(_content=row["Description"], lang=self.lang)
        com.Description = DEFINE.Description()
        com.Description.TranslatedText.append(tt)
        if row.get("Document"):
            self._add_document(row, com)
        return com

    def _add_document(self, row, com):
        """
        creates a DocumentRef object using a row from the Comments Worksheet
        :param row: Comments worksheet row values as a dictionary
        :param method: odmlib CommentDef object that gets updated with a DocumentRef object
        """
        dr = DEFINE.DocumentRef(leafID=row["Document"])
        if row.get("Pages"):
            pdf = DEFINE.PDFPageRef(PageRefs=row["Pages"], Type="NamedDestination")
            dr.PDFPageRef.append(pdf)
        com.DocumentRef.append(dr)
