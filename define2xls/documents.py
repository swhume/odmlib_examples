import csv
import os


class Documents:
    HEADERS = ["ID", "Title", "Href"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "documents.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for lf in self.mdv.leaf:
                writer.writerow([lf.ID, lf.title._content, lf.href])
