import csv
import os


class ValueLevel:
    # does not include the IsNonStandard and HasNoData attributes for value level ItemRefs
    HEADERS = ["OID", "Order", "Dataset", "Variable", "ItemOID", "Where Clause", "Data Type", "Length",
               "Significant Digits", "Format", "Mandatory", "Codelist", "Origin Type", "Origin Source", "Pages",
               "Method", "Predecessor", "Comment"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "valuelevel.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for vl in self.mdv.ValueListDef:
                dataset = self._get_dataset_name(vl.OID)
                for ir in vl.ItemRef:
                    # assumes all ItemDefs are referenced by an ItemRef
                    ird = self._load_item_ref(ir)
                    idd = self._load_item_def(ir.ItemOID)
                    writer.writerow([vl.OID, ird["Order"], dataset, idd["Variable"], ir.ItemOID, ird["Where Clause"],
                                     idd["Data Type"], idd["Length"], idd["Significant Digits"], idd["Format"],
                                     ird["Mandatory"], idd["Codelist"], idd["Origin Type"], idd["Origin Source"],
                                     idd["Pages"], ird["Method"], idd["Predecessor"], idd["Comment"]])

    def _get_dataset_name(self, vl_oid):
        for item in self.mdv.ItemDef:
            if item.ValueListRef and item.ValueListRef.ValueListOID == vl_oid:
                for igd in self.mdv.ItemGroupDef:
                    ir = igd.find("ItemRef", "ItemOID", item.OID)
                    if ir:
                        return igd.Name
        raise ValueError(f"Dataset for ValueListDef {vl_oid} not found in the Define-XML file")


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
        idd["Codelist"] = it.CodeListRef.CodeListOID if it.CodeListRef else ""
        # TODO add support for multiple Origins
        idd["Origin Type"] = it.Origin[0].Type if it.Origin else ""
        idd["Origin Source"] = it.Origin[0].Source if it.Origin and it.Origin[0].Source else ""
        idd["Pages"] = it.Origin[0].DocumentRef[0].PDFPageRef[0].PageRefs \
            if it.Origin and it.Origin[0].DocumentRef and it.Origin[0].DocumentRef[0].PDFPageRef else ""
        idd["Predecessor"] = it.Origin[0].Description.TranslatedText[0]._content \
            if it.Origin and it.Origin[0].Type == "Predecessor" else ""
        idd["Comment"] = it.CommentOID if it.CommentOID else ""
        return idd

    def _get_where_clause_oid(self, item):
        wc_oids = []
        for wc in item.WhereClauseRef:
            wc_oids.append(wc.WhereClauseOID)
        return "'".join(wc_oids)