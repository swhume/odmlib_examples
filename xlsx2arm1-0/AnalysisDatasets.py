from odmlib.arm_1_0 import model as ARM
import define_object

class AnalysisDatasets(define_object.DefineObject):

    def __init__(self):
        super().__init__()

    def create_define_objects(self, sheet, objects, lang, acrf, suppdocs):
        self.lang = lang
        self.sheet = sheet
        num_cols = self.sheet.max_column
        header = self.load_header(num_cols)
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=num_cols, values_only=True):
            row_content = self.load_row(row, header)
            ad = self._create_analysisdataset_object(row_content)
            ### link up to the result
            result_oid=row_content["Result"]
            ar = self.find_object(objects["AnalysisResults"], result_oid)
            if ar is None:
                raise ValueError(f"AnalysisResult with OID {result_oid} is missing from the AnalysisResults tab")
            ar.AnalysisDatasets.AnalysisDataset.append(ad)

    def _create_analysisdataset_object(self, row):
        """
        use the values from the AnalysisResults worksheet row to create a AnalysisResult odmlib object
        :param row: Datasets worksheet row values as a dictionary
        :return: odmlib ResultDisplay object
        """
        attr = {"ItemGroupOID": row["Dataset"]}
        dataset = ARM.AnalysisDataset(**attr)
        wc = ARM.WhereClauseRef(WhereClauseOID=row["Where Clause"])
        dataset.WhereClauseRef = wc
        ### analysis variables need to be parsed from a comma delimited String
        vars = row["Variables"]
        if vars:
            result = [item.strip() for item in vars.split(',')]
            for var in result:
                newvar = ARM.AnalysisVariable(ItemOID=var)
                dataset.AnalysisVariable.append(newvar)

        return dataset