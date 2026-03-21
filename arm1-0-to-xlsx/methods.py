import csv
import os


class Methods:
    HEADERS = ["OID", "Name", "Type", "Description", "Expression Context", "Expression Code", "Document", "Pages"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "methods.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for md in self.mdv.MethodDef:
                context = ""
                code = ""
                if md.FormalExpression:
                    context = md.FormalExpression[0].Context
                    code = md.FormalExpression[0]._content
                leaf_id = ""
                page_refs = ""
                if md.DocumentRef:
                    leaf_id = md.DocumentRef[0].leafID
                    page_refs = md.DocumentRef[0].PDFPageRef[0].PageRefs
                description = " ".join(md.Description.TranslatedText[0]._content.split())
                writer.writerow([md.OID, md.Name, md.Type, description, context, code,
                                 leaf_id, page_refs])
