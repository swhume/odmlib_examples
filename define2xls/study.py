import csv
import os


class Study:
    HEADERS = ["Attribute", "Value"]

    def __init__(self, odmlib_study, odmlib_mdv, data_path, language="en"):
        self.study = odmlib_study
        self.mdv = odmlib_mdv
        self.path = data_path
        self.language = language
        self.file_name = os.path.join(self.path, "study.csv")

    def extract(self):
        print(f"Study OID: {self.study.StudyName}")
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            writer.writerow(["StudyName", self.study.StudyName])
            writer.writerow(["StudyDescription", self.study.StudyDescription])
            writer.writerow(["ProtocolName", self.study.ProtocolName])
            writer.writerow(["StandardName", self.mdv.StandardName])
            writer.writerow(["StandardVersion", self.mdv.StandardVersion])
            writer.writerow(["Language", self.language])
