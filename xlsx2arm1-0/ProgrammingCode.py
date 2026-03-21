from odmlib.arm_1_0 import model as ARM
import define_object

class ProgrammingCode(define_object.DefineObject):

    def __init__(self):
        super().__init__()

    def create_define_objects(self, sheet, objects, lang, acrf, suppdocs):
        self.lang = lang
        self.sheet = sheet
        num_cols = self.sheet.max_column
        header = self.load_header(num_cols)
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=num_cols, values_only=True):
            row_content = self.load_row(row, header)
            pc = self._create_programmingcode_object(row_content)
            ### link up to the result
            result_oid=row_content["Result"]
            ar = self.find_object(objects["AnalysisResults"], result_oid)
            if ar is None:
                raise ValueError(f"AnalysisResult with OID {result_oid} is missing from the AnalysisResults tab")
            ar.ProgrammingCode = pc

    def _create_programmingcode_object(self, row):
        """
        use the values from the AnalysisResults worksheet row to create a AnalysisResult odmlib object
        :param row: Datasets worksheet row values as a dictionary
        :return: odmlib ResultDisplay object
        """
        attr = {"Context": row["Context"]}
        code = ARM.ProgrammingCode(**attr)
        if row["Code"]:
                code.Code._content = row["Code"]
        if row.get("Document"):
            self._add_document(row, code)
        return code

    def _add_document(self, row, code):
        """
        creates a DocumentRef object using a row from the ProgrammingCode Worksheet
        :param row: ProgrammingCode worksheet row values as a dictionary
        :param result: odmlib ProgrammingCode object that gets updated with a DocumentRef object
        """
        dr = ARM.DocumentRef(leafID=row["Document"])
        code.DocumentRef.append(dr)
        return code