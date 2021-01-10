import csv
import os


class CodeLists:
    HEADERS = ["OID", "Name", "NCI Codelist Code", "Data Type", "Order", "Term", "NCI Term Code", "Decoded Value"]

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
        cl_c_code = ""
        if cl.Alias:
            cl_c_code = cl.Alias[0].Name
        for ei in cl.EnumeratedItem:
            order_number = ""
            if ei.OrderNumber:
                order_number = ei.OrderNumber
            ei_c_code = ""
            if ei.Alias:
                ei_c_code = ei.Alias[0].Name
            writer.writerow([cl.OID, cl.Name, cl_c_code, cl.DataType, order_number, ei.CodedValue, ei_c_code, ""])

    def _write_code_list_item_row(self, cl, writer):
        cl_c_code = ""
        if cl.Alias:
            cl_c_code = cl.Alias[0].Name
        for cli in cl.CodeListItem:
            order_number = ""
            if cli.OrderNumber:
                order_number = cli.OrderNumber
            cli_c_code = ""
            if cli.Alias:
                cli_c_code = cli.Alias[0].Name
            decode = cli.Decode.TranslatedText[0]._content
            writer.writerow([cl.OID, cl.Name, cl_c_code, cl.DataType, order_number, cli.CodedValue, cli_c_code, decode])
