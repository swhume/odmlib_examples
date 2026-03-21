import csv
import os


class Variables:
    HEADERS = ["OID", "Order", "Dataset", "Variable", "Label", "Data Type", "Length", "Significant Digits", "Format",
               "KeySequence", "Mandatory", "CodeList", "Valuelist", "Origin Type", "Origin Source", "Pages", "Method",
               "Predecessor", "Role", "Comment", "IsNonStandard", "HasNoData"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "variables.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for ig in self.mdv.ItemGroupDef:
                for ir in ig.ItemRef:
                    # assumes all ItemDefs are referenced by an ItemRef
                    ird = self._load_item_ref(ir)
                    idd = self._load_item_def(ir.ItemOID)
                    writer.writerow([idd["OID"], ird["Order"], ig.Name, idd["Variable"], idd["Label"], idd["Data Type"], idd["Length"],
                                     idd["Significant Digits"], idd["Format"], ird["KeySequence"], ird["Mandatory"],
                                     idd["Codelist"], idd["Valuelist"], idd["Origin Type"], idd["Origin Source"],
                                     idd["Pages"], ird["Method"], idd["Predecessor"], ird["Role"], idd["Comment"],
                                     ird["IsNonStandard"], ird["HasNoData"]])

    def _load_item_ref(self, ir):
        ird = {}
        ird["Order"] = ir.OrderNumber
        ird["Mandatory"] = ir.Mandatory
        ird["KeySequence"] = ir.KeySequence
        ird["Method"] = ir.MethodOID
        ird["Role"] = ir.Role
        ird["IsNonStandard"] = ir.IsNonStandard if ir.IsNonStandard else ""
        ird["HasNoData"] = ir.HasNoData if ir.HasNoData else ""
        return ird

    def _load_item_def(self, item_oid):
        idd = {}
        it = self.mdv.find("ItemDef", "OID", item_oid)
        idd["OID"] = item_oid
        idd["Variable"] = it.Name
        idd["Data Type"] = it.DataType
        idd["Length"] = it.Length
        idd["Significant Digits"] = it.SignificantDigits
        idd["Format"] = it.DisplayFormat
        idd["Label"] = " ".join(it.Description.TranslatedText[0]._content.split())
        idd["Codelist"] = it.CodeListRef.CodeListOID if it.CodeListRef else ""
        idd["Valuelist"] = it.ValueListRef.ValueListOID if it.ValueListRef else ""
        # TODO add support for multiple Origins
        idd["Origin Type"] = it.Origin[0].Type if it.Origin else ""
        idd["Origin Source"] = it.Origin[0].Source if it.Origin and it.Origin[0].Source else ""
        idd["Pages"] = it.Origin[0].DocumentRef[0].PDFPageRef[0].PageRefs \
            if it.Origin and it.Origin[0].DocumentRef and it.Origin[0].DocumentRef[0].PDFPageRef else ""
        idd["Predecessor"] = it.Origin[0].Description.TranslatedText[0]._content \
            if it.Origin and it.Origin[0].Type == "Predecessor" else ""
        idd["Comment"] = it.CommentOID if it.CommentOID else ""
        return idd
