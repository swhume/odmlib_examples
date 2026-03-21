import csv
import os


class CodeLists:
    HEADERS = ["OID", "Name", "NCI Codelist Code", "Data Type", "Rank", "Order", "Term", "NCI Term Code", "Decoded Value",
               "Comment", "IsNonStandard", "StandardOID"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "codelists.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for cl in self.mdv.CodeList:
                if cl.EnumeratedItem:
                    self._write_enumerated_item_row(cl, writer)
                elif cl.CodeListItem:
                    self._write_code_list_item_row(cl, writer)

    def _write_enumerated_item_row(self, cl, writer):
        attr = self._conditional_codelist_content(cl)
        for ei in cl.EnumeratedItem:
            order_number = ""
            if ei.OrderNumber:
                order_number = ei.OrderNumber
            rank_number = ""
            if ei.Rank:
                rank_number = ei.Rank
            ei_c_code = ""
            if ei.Alias:
                ei_c_code = ei.Alias[0].Name
            writer.writerow([cl.OID, cl.Name, attr["cl_c_code"], cl.DataType, rank_number, order_number, ei.CodedValue, ei_c_code, "",
                             attr["comment_oid"], attr["is_non_std"], attr["standard_oid"]])

    def _write_code_list_item_row(self, cl, writer):
        attr = self._conditional_codelist_content(cl)
        for cli in cl.CodeListItem:
            order_number = ""
            if cli.OrderNumber:
                order_number = cli.OrderNumber
            rank_number = ""
            if cli.Rank:
                rank_number = cli.Rank
            cli_c_code = ""
            if cli.Alias:
                cli_c_code = cli.Alias[0].Name
            decode = cli.Decode.TranslatedText[0]._content
            writer.writerow([cl.OID, cl.Name, attr["cl_c_code"], cl.DataType, rank_number, order_number, cli.CodedValue, cli_c_code,
                             decode, attr["comment_oid"], attr["is_non_std"], attr["standard_oid"]])

    def _conditional_codelist_content(self ,cl):
        attr = {"cl_c_code": ""}
        if cl.Alias:
            attr["cl_c_code"] = cl.Alias[0].Name
        attr["comment_oid"] = ""
        if cl.CommentOID:
            attr["comment_oid"] = cl.CommentOID
        attr["is_non_std"] = ""
        if cl.IsNonStandard:
            attr["is_non_std"] = cl.IsNonStandard
        attr["standard_oid"] = ""
        if cl.StandardOID:
            attr["standard_oid"] = cl.StandardOID
        return attr
