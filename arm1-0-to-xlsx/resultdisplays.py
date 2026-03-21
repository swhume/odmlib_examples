import csv
import os

# TODO: Can have multiple PDFPageRefs according to the model, but only see one so far
class ResultDisplays:
    HEADERS = ["OID", "Name", "Description", "Document", "Pages", "Title"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "resultdisplays.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for ig in self.mdv.AnalysisResultDisplays:
                leafId = ""
                pages = ""
                title = ""
                if len(ig.DocumentRef) > 0:
                    leafId = ig.DocumentRef[0].leafID
                    pages = ig.DocumentRef[0].PDFPageRef[0].PageRefs
                    title = ig.DocumentRef[0].PDFPageRef[0].Title

                writer.writerow([ig.OID, ig.Name, ig.Description.TranslatedText[0]._content, leafId,
                                 pages, title])
