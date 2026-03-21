from odmlib.arm_1_0 import model as DEFINE
import define_object


class WhereClauses(define_object.DefineObject):
    """ create a Define-XML v2.0 WhereClauseDef element object """
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
        objects["WhereClauseDef"] = []
        prev_oid = ""
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=self.sheet.max_column, values_only=True):
            row_content = self.load_row(row, header)
            # if the current id is the same as the previous, we're just adding another range_check
            oid = row_content["OID"]
            if oid != prev_oid:
                wcd = self._create_whereclausedef_object(row_content)
                objects["WhereClauseDef"].append(wcd)
                prev_oid = oid
            else:
                rc = self._create_rangecheck(row_content)
                objects["WhereClauseDef"][-1].RangeCheck.append(rc)

    def _create_whereclausedef_object(self, row):
        """
        use the values from the WhereClauses worksheet row to create a WhereClauseDef odmlib object
        :param row: WhereClauses worksheet row values as a dictionary
        :return: a WhereClause odmlib object
        """
        attr = {"OID": row["OID"]}
        if row.get("Comment"):
            attr["CommentOID"] = self.generate_oid(["COM", row["Comment"]])
        wc = DEFINE.WhereClauseDef(**attr)
        item_oid = self.generate_oid(["IT", row["Dataset"], row["Variable"]])
        rc_attr = {"Comparator": row["Comparator"], "SoftHard": "Soft", "ItemOID": item_oid }
        rc = DEFINE.RangeCheck(**rc_attr)
        values = row["Value"]
        if values:
            val = [item.strip() for item in values.split(",")]
            for var in val:
                cv = DEFINE.CheckValue(_content=var)
                rc.CheckValue.append(cv)
        else:
            cv = DEFINE.CheckValue(_content="")
            rc.CheckValue.append(cv)
        wc.RangeCheck.append(rc)
        return wc

    def _create_rangecheck(self, row):
        """
        use the values from the WhereClauses worksheet to create a RangeCheck odmlinb object
        :param row: WhereClauses worksheet row values as a dictionary
        :return: a RangeCheck odmlib object
        """
        item_oid = self.generate_oid(["IT", row["Dataset"], row["Variable"]])
        rc_attr = {"Comparator": row["Comparator"], "SoftHard": "Soft", "ItemOID": item_oid}
        rc = DEFINE.RangeCheck(**rc_attr)
        for value in row["Value"].split(", "):
            cv = DEFINE.CheckValue(_content=value)
            rc.CheckValue.append(cv)
        return rc
