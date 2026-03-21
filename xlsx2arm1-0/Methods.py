from odmlib.arm_1_0 import model as DEFINE
import define_object


class Methods(define_object.DefineObject):
    """ create a Define-XML v2.0 MethodDef element object """
    def __init__(self):
        super().__init__()

    def create_define_objects(self, sheet, objects, lang, acrf, suppdocs):
        """
        parse the Excel sheet and create a odmlib objects to return in the objects dictionary
        :param sheet: xlrd Excel sheet object
        :param objects: dictionary of odmlib objects updated by this method
        :param lang: xml:lang setting for TranslatedText
        """
        self.lang = lang
        self.sheet = sheet
        header = self.load_header(self.sheet.max_column)
        objects["MethodDef"] = []
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=self.sheet.max_column, values_only=True):
            row_content = self.load_row(row, header)
            item = self._create_methoddef_object(row_content)
            objects["MethodDef"].append(item)

    def _create_methoddef_object(self, row):
        """
        use the values from the Methods worksheet row to create a MethodDef odmlib object
        :param row: Methods worksheet row values as a dictionary
        :return: a MethodDef odmlib object
        """
        attr = {"OID": row["OID"], "Name": row["Name"], "Type": row["Type"]}
        method = DEFINE.MethodDef(**attr)
        tt = DEFINE.TranslatedText(_content=row["Description"], lang=self.lang)
        method.Description = DEFINE.Description()
        method.Description.TranslatedText.append(tt)
        if row.get("Expression Context"):
            method.FormalExpression.append(DEFINE.FormalExpression(Context=row["Expression Context"], _content=row["Expression Code"]))
        if row.get("Document"):
            self._add_document(row, method)
        return method

    def _add_document(self, row, method):
        """
        creates a DocumentRef object using a row from the Methods Worksheet
        :param row: Methods worksheet row values as a dictionary
        :param method: odmlib MethodDef object that gets updated with a DocumentRef object
        """
        dr = DEFINE.DocumentRef(leafID=row["Document"])
        type = ""
        pages = row.get("Pages")
        if pages:
            if pages.isdigit():
                type = "PhysicalRef";
            else:
                type = "NamedDestination"
            pdf = DEFINE.PDFPageRef(PageRefs=pages, Type=type)
            dr.PDFPageRef.append(pdf)
        method.DocumentRef.append(dr)
        return method