import csv
import os


class Comments:
    HEADERS = ["OID", "Description", "Document", "Pages"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "comments.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for com in self.mdv.CommentDef:
                leaf_id = ""
                page_refs = ""
                if com.DocumentRef:
                    leaf_id = com.DocumentRef[0].leafID
                    if com.DocumentRef[0].PDFPageRef:
                        page_refs = com.DocumentRef[0].PDFPageRef[0].PageRefs
                comment = " ".join(com.Description.TranslatedText[0]._content.split())
                writer.writerow([com.OID, comment, leaf_id, page_refs])
