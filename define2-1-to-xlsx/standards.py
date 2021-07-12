import csv
import os


class Standards:
    HEADERS = ["OID", "Name", "Type", "Publishing Set", "Version", "Status", "Comment"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "standards.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for std in self.mdv.Standards.Standard:
                pset = ""
                status = ""
                comment = ""
                if std.PublishingSet:
                    pset = std.PublishingSet
                if std.Status:
                    status = std.Status
                if std.CommentOID:
                    comment = std.CommentOID
                writer.writerow([std.OID, std.Name, std.Type, pset, std.Version, status, comment])
