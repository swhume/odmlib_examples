from odmlib.arm_1_0 import model as ARM
import define_object

class AnalysisResults(define_object.DefineObject):

    def __init__(self):
        super().__init__()

    def create_define_objects(self, sheet, objects, lang, acrf, suppdocs):
        self.lang = lang
        self.sheet = sheet
        num_cols = self.sheet.max_column
        header = self.load_header(num_cols)
        objects["AnalysisResults"] = []
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=num_cols, values_only=True):
            row_content = self.load_row(row, header)
            ar = self._create_analysisresult_object(row_content)
            objects["AnalysisResults"].append(ar)
            ### link up to the display
            display_oid=row_content["DisplayOID"]
            ard = self.find_object(objects["AnalysisResultDisplays"], display_oid)
            if ard is None:
                raise ValueError(f"AnalysisResultDisplay with OID {display_oid} is missing from the ResultDisplays tab")
            ard.AnalysisResult.append(ar)

    def _create_analysisresult_object(self, row):
        """
        use the values from the AnalysisResults worksheet row to create a AnalysisResult odmlib object
        :param row: Datasets worksheet row values as a dictionary
        :return: odmlib ResultDisplay object
        """
        attr = {"OID": row["OID"], "ParameterOID": row["ParameterOID"], "AnalysisReason": row["Reason"], "AnalysisPurpose": row["Purpose"]}
        result = ARM.AnalysisResult(**attr)
        tt = ARM.TranslatedText(_content=row["Description"], lang=self.lang)
        result.Description = ARM.Description()
        result.Description.TranslatedText.append(tt)
        documentation = ARM.TranslatedText(_content=row["Documentation"], lang=self.lang)
        result.Documentation = ARM.Documentation()
        result.Documentation.Description = ARM.Description()
        result.Documentation.Description.TranslatedText.append(documentation)
        if row.get("Document"):
            self._add_document(row, result.Documentation)
        if row.get("DatasetComment"):
            ADC = ARM.AnalysisDatasets(CommentOID=row.get("DatasetComment"))
            result.AnalysisDatasets = ADC
        return result

    def _add_document(self, row, result):
        """
        creates a DocumentRef object using a row from the AnalysisResults Worksheet
        :param row: Methods worksheet row values as a dictionary
        :param result: odmlib AnalysisResult object that gets updated with a DocumentRef object
        """
        dr = ARM.DocumentRef(leafID=row["Document"])
        pdf = ARM.PDFPageRef(PageRefs=row["Pages"],  Type="PhysicalRef", Title=row["Title"] )
        dr.PDFPageRef.append(pdf)
        result.DocumentRef.append(dr)
        return result

