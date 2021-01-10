import csv
import os


class ValueLevel:
    HEADERS = ["Order", "Dataset", "Variable", "Where Clause", "Data Type", "Length", "Significant Digits", "Format",
               "Mandatory", "Codelist", "Origin", "Pages", "Method", "Predecessor", "Comment"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "valuelevel.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for vl in self.mdv.ValueListDef:
                for ir in vl.ItemRef:
                    # assumes all ItemDefs are referenced by an ItemRef
                    ird = self._load_item_ref(ir)
                    idd = self._load_item_def(ir.ItemOID)
                    # using OID to get dataset is a hack, but dataset column only used to create the OID for VLD
                    dataset = vl.OID.split(".")[1]
                    writer.writerow([ird["Order"], dataset, idd["Variable"], ird["Where Clause"], idd["Data Type"],
                                     idd["Length"], idd["Significant Digits"], idd["Format"], ird["Mandatory"],
                                     idd["Codelist"], idd["Origin"], idd["Pages"], ird["Method"],
                                    idd["Predecessor"], idd["Comment"]])

    def _load_item_ref(self, ir):
        ird = {}
        ird["Order"] = ir.OrderNumber
        ird["Mandatory"] = ir.Mandatory
        ird["Method"] = ir.MethodOID
        ird["Where Clause"] = self._get_where_clause_oid(ir)
        return ird

    def _load_item_def(self, item_oid):
        idd = {}
        it = self.mdv.find("ItemDef", "OID", item_oid)
        idd["Variable"] = it.Name
        idd["Data Type"] = it.DataType
        idd["Length"] = it.Length
        idd["Significant Digits"] = it.SignificantDigits
        idd["Format"] = it.DisplayFormat
        idd["Codelist"] = it.CodeListRef.CodeListOID if it.CodeListRef is not None else ""
        idd["Origin"] = it.Origin.Type if it.Origin else ""
        idd["Pages"] = it.Origin.DocumentRef[0].PDFPageRef[0].PageRefs \
            if it.Origin.DocumentRef and it.Origin.DocumentRef[0].PDFPageRef else ""
        idd["Predecessor"] = it.Origin.Description.TranslatedText[0]._content if it.Origin.Type == "Predecessor" else ""
        idd["Comment"] = it.CommentOID if it.CommentOID else ""
        return idd

    def _get_where_clause_oid(self, item):
        wc_oids = []
        for wc in item.WhereClauseRef:
            wc_oids.append(wc.WhereClauseOID)
        return "'".join(wc_oids)