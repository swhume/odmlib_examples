import csv
import os


class Study:
    HEADERS = ["Attribute", "Value"]

    def __init__(self, odmlib_study, odmlib_mdv, data_path, language="en", acrf="LF.acrf"):
        self.study = odmlib_study
        self.mdv = odmlib_mdv
        self.path = data_path
        self.acrf = acrf
        self.language = language
        self.file_name = os.path.join(self.path, "study.csv")

    def extract(self):
        print(f"Study OID: {self.study.OID}")
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            writer.writerow(["StudyName", self.study.GlobalVariables.StudyName])
            writer.writerow(["StudyDescription", self.study.GlobalVariables.StudyDescription])
            writer.writerow(["ProtocolName", self.study.GlobalVariables.ProtocolName])
            writer.writerow(["Language", self.language])
            writer.writerow(["Annotated CRF", self.acrf])
            # for multiple Suppdocs, create a csl
            avars = []
            for sd in self.mdv.SupplementalDoc.DocumentRef:
                # annotated CRF is a specialized attribute so only add additional suppdocs
                if sd.leafID != self.acrf:
                    avars.append(sd.leafID)
            writer.writerow(["SupplementalDocuments", ",".join(avars)])
