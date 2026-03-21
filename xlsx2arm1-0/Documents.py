from odmlib.arm_1_0 import model as DEFINE
import define_object


class Documents(define_object.DefineObject):
    """ create a Define-XML v2.0 leaf element object """
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
        objects["leaf"] = []
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=self.sheet.max_column, values_only=True):
            row_content = self.load_row(row, header)
            leaf = self._create_leaf_object(row_content)
            objects["leaf"].append(leaf)

    def _create_leaf_object(self, row):
        """
        use the values from the Documents   worksheet row to create a leaf odmlib object
        :param row: Documents worksheet row values as a dictionary
        :return: a leaf odmlib object
        """
        lf = DEFINE.leaf(ID=row["ID"], href=row["Href"])
        title = DEFINE.title(_content=row["Title"])
        lf.title = title
        return lf
