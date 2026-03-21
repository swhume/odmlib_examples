import csv
import os


class ProgrammingCode:
    HEADERS = ["Result", "Context", "Document", "Code"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "programmingcode.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for display in self.mdv.ResultDisplay:
                for result in display.AnalysisResult:
                    leaf_id = ""
                    if result.ProgrammingCode.DocumentRef:
                        leaf_id = result.ProgrammingCode.DocumentRef[0].leafID
                    writer.writerow([result.OID, result.ProgrammingCode.Context, leaf_id, result.ProgrammingCode.Code._content])
