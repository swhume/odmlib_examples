import csv
import os


class AnalysisDatasets:
    HEADERS = ["Result", "Dataset", "Variables", "Where Clause"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "analysisdatasets.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for display in self.mdv.ResultDisplay:
                for result in display.AnalysisResult:
                    for dataset in result.AnalysisDatasets:
                        avars = []
                        for avar in dataset.AnalysisVariable:
                            avars.append(avar.ItemOID)
                        writer.writerow([result.OID, dataset.ItemGroupOID, ",".join(avars), dataset.WhereClauseRef.WhereClauseOID])
