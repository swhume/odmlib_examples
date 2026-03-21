import csv
import os


class Datasets:
    HEADERS = ["OID", "Dataset", "Description", "Class", "Structure", "Purpose", "Repeating", "Reference Data", "Comment",
               "IsNonStandard", "StandardOID", "HasNoData", "Document"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "datasets.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for ig in self.mdv.ItemGroupDef:
                print(ig.Class.Name)
                writer.writerow([ig.OID, ig.Name, ig.Description.TranslatedText[0]._content, ig.Class.Name, ig.Structure, ig.Purpose,
                                 ig.Repeating, ig.IsReferenceData, ig.CommentOID, ig.IsNonStandard, ig.StandardOID,
                                 ig.HasNoData, ig.leaf.ID])
