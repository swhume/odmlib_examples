import csv
import os


class WhereClauses:
    HEADERS = ["OID", "Dataset", "Variable", "Comparator", "Value", "Comment"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "whereclauses.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            wc_oid = ""
            for wc in self.mdv.WhereClauseDef:
                # using OID to get dataset is a hack, but dataset column only used to create the OID for def:ItemOID
                dataset = wc.OID.split(".")[1]
                comment_oid = ""
                if wc.CommentOID:
                    comment_oid = wc.CommentOID
                for rc in wc.RangeCheck:
                    value = self._load_check_values(rc)
                    variable_name = self._extract_variable_name(rc.ItemOID)
                    writer.writerow([wc.OID, dataset, variable_name, rc.Comparator, value, comment_oid])

    def _load_check_values(self, rc):
        check_values = []
        for cv in rc.CheckValue:
            check_values.append(cv._content)
        return ",".join(check_values)

    def _extract_variable_name(self, item_oid):
        return item_oid.split(".")[-1]