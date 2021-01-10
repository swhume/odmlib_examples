from odmlib.define_2_0 import model as DEFINE
import define_object


class CodeLists(define_object.DefineObject):
    """ create a Define-XML v2.0 CodeList element object """
    def __init__(self):
        super().__init__()
        self.igd = None

    def create_define_objects(self, sheet, objects, lang):
        """
        parse the Excel sheet and create a odmlib objects to return in the objects dictionary
        :param sheet: xlrd Excel sheet object
        :param objects: dictionary of odmlib objects updated by this method
        :param lang: xml:lang setting for TranslatedText

        """
        self.lang = lang
        self.sheet = sheet
        header = self.load_header(self.sheet.max_column)
        objects["CodeList"] = []
        cl_c_code = ""
        cl_name = ""
        cl = None
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=self.sheet.max_column, values_only=True):
            row_content = self.load_row(row, header)
            # when this is a new code list the names will not be the same
            if row_content["Name"] != cl_name:
                if cl_name:
                    self._add_previous_codelist_to_objects(cl_c_code, cl, objects)
                cl = self._create_codelist_object(row_content)
                cl_c_code = row_content.get("NCI Codelist Code")
                cl_name = row_content.get("Name")
            if row_content["Decoded Value"]:
                cl_item = self._create_codelistitem_object(row_content)
                cl.CodeListItem.append(cl_item)
            else:
                en_item = self._create_enumerateditem_object(row_content)
                cl.EnumeratedItem.append(en_item)
        self._add_previous_codelist_to_objects(cl_c_code, cl, objects)

    def _add_previous_codelist_to_objects(self, cl_c_code, cl, objects):
        """
        finish creating a codelist by adding Alias of a c-code exists and adding the object to the list of codelists
        :param row_idx: positive integer indicating which row - skip processing the first row
        :param cl_c_code: codelist c-code
        :param cl: odmlib codelist object
        :param objects: dictionary of odmlib objects created from the Excel input file and updated in this method
        """
        # finish processing the first list before saving it
        # if row_idx > 1 and cl:
        # if the code list has an associated c-code add it to the code list as an Alias element
        if cl_c_code:
            alias = DEFINE.Alias(Context="nci:ExtCodeID", Name=cl_c_code)
            cl.Alias.append(alias)
        # add the code list to the list of code list objects
        objects["CodeList"].append(cl)

    def _create_codelist_object(self, row):
        """
        using the row from the Codelists worksheet create an odmlib CodeList object
        :param row: dictionary with contents from a row in the Codelists worksheet
        :return: CodeList odmlib object
        """
        cl = DEFINE.CodeList(OID=row["OID"], Name=row["Name"], DataType=row["Data Type"])
        return cl

    def _create_enumerateditem_object(self, row):
        """
        using the row from the Codelists worksheet create an odmlib EnumeratedItem object
        :param row: dictionary with contents from a row in the Codelists worksheet
        :return: EnumeratedItem odmlib object
        """
        attr = {"CodedValue": row["Term"]}
        if row.get("Order"):
            attr["OrderNumber"] = row["Order"]
        en_item = DEFINE.EnumeratedItem(**attr)
        if row.get("NCI Term Code"):
            alias = DEFINE.Alias(Context="nci:ExtCodeID", Name=row["NCI Term Code"])
            en_item.Alias.append(alias)
        return en_item

    def _create_codelistitem_object(self, row):
        """
        using the row from the Codelists worksheet create an odmlib CodeListItem object
        :param row: dictionary with contents from a row in the Codelists worksheet
        :return: CodeListItem odmlib object
        """
        attr = {"CodedValue": row["Term"]}
        if row.get("Order"):
            attr["OrderNumber"] = row["Order"]
        cl_item = DEFINE.CodeListItem(**attr)
        decode = DEFINE.Decode()
        tt = DEFINE.TranslatedText(_content=row["Decoded Value"], lang="en")
        decode.TranslatedText.append(tt)
        cl_item.Decode = decode
        if row.get("NCI Term Code"):
            alias = DEFINE.Alias(Context="nci:ExtCodeID", Name=row["NCI Term Code"])
            cl_item.Alias.append(alias)
        return cl_item
