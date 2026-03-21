from odmlib.arm_1_0 import model as ARM
import define_object

class ResultDisplays(define_object.DefineObject):
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
        displays=ARM.AnalysisResultDisplays()
        self.lang = lang
        self.sheet = sheet
        num_cols = self.sheet.max_column
        header = self.load_header(num_cols)
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=num_cols, values_only=True):
            row_content = self.load_row(row, header)
            itg = self._create_resultdisplay_object(row_content)
            displays.ResultDisplay.append(itg)
        objects["AnalysisResultDisplays"] = displays

    def _create_resultdisplay_object(self, row):
        """
        use the values from the ResultDisplays worksheet row to create a ResultDisplay odmlib object
        :param row: Datasets worksheet row values as a dictionary
        :return: odmlib ResultDisplay object
        """
        attr = {"OID": row["OID"], "Name": row["Name"]}
        display = ARM.ResultDisplay(**attr)
        tt = ARM.TranslatedText(_content=row["Description"], lang=self.lang)
        display.Description = ARM.Description()
        display.Description.TranslatedText.append(tt)
        if row.get("Document"):
            self._add_document_ref(row, display)
        return display

    def _add_document_ref(self, row, display):
        dr = ARM.DocumentRef(leafID= row["Document"])
        pdf = ARM.PDFPageRef(PageRefs=row["Pages"],  Type="PhysicalRef", Title=row["Title"] )
        dr.PDFPageRef.append(pdf)
        display.DocumentRef.append(dr)
        return display