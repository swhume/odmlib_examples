import csv
import os


class AnalysisResults:
    HEADERS = ["OID", "ParameterOID", "Description", "Reason", "Purpose", "DisplayOID", "Documentation", "Document",
               "Pages", "Title", "DatasetComment"]

    def __init__(self, odmlib_display, data_path):
        self.mdv = odmlib_display
        self.path = data_path
        self.file_name = os.path.join(self.path, "analysisresults.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for display in self.mdv.ResultDisplay:
                for ig in display.AnalysisResult:
                    poid=""
                    leafId = ""
                    pages = ""
                    title = ""
                    if ig.ParameterOID:
                        poid=ig.ParameterOID
                    if len(ig.Documentation.DocumentRef) > 0:
                        leafId = ig.Documentation.DocumentRef[0].leafID
                        pages = ig.Documentation.DocumentRef[0].PDFPageRef[0].PageRefs
                        title = ig.Documentation.DocumentRef[0].PDFPageRef[0].Title
                    writer.writerow([ig.OID, poid, ig.Description.TranslatedText[0]._content,
                        ig.AnalysisReason, ig.AnalysisPurpose, display.OID,
                        ig.Documentation.Description.TranslatedText[0]._content, leafId,
                        pages,
                        title, ig.AnalysisDatasets.CommentOID])
