from odmlib.arm_1_0 import model as DEFINE
import define_object


class Dictionaries(define_object.DefineObject):
    """ create a Define-XML v2.0 CodeList element object """
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
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=self.sheet.max_column, values_only=True):
            row_content = self.load_row(row, header)
            cl = self._create_codelist_object(row_content)
            objects["CodeList"].append(cl)

    def _create_codelist_object(self, row):
        """
        using the row from the Dictionaries worksheet create an odmlib CodeList object and add ExternalCodeList
        :param row: dictionary with contents from a row in the Dictionaries worksheet
        :return: CodeList odmlib object with ExternalCodeList
        """
        cl = DEFINE.CodeList(OID=row["OID"], Name=row["Name"], DataType=row["Data Type"], IsNonStandard= "Yes")
        attr = {"Dictionary": row["Dictionary"]}
        if row.get("Version"):
            attr["Version"] = row["Version"]
        if row.get("Href"):
            attr["href"] = row["Href"]
        exd = DEFINE.ExternalCodeList(**attr)
        cl.ExternalCodeList = exd
        return cl
