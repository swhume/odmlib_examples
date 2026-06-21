import csv
import os


class Dictionaries:
    HEADERS = ["OID", "Name", "Data Type", "Dictionary", "Version"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "dictionaries.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for cl in self.mdv.CodeList:
                if cl.ExternalCodeList.Dictionary:
                    self._write_external_code_list_row(cl, writer)

    def _write_external_code_list_row(self, cl, writer):
        ext_cl = cl.ExternalCodeList
        version = ""
        if ext_cl.Version:
            version = ext_cl.Version
        writer.writerow([cl.OID, cl.Name, cl.DataType, ext_cl.Dictionary, version])
