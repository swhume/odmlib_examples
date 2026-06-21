import csv
import os

class CodeLists:
    HEADERS = ["OID", "Name", "NCI Codelist Code", "Data Type", "Order", "Term", "NCI Term Code", "Decoded Value",
               "Comment", "IsNonStandard", "StandardOID", "Term Date Published", "Term Status",
               "Term Ext Code ID", "Term Submission Value", "Term Synonym", "Term Definition", "Term Preferred Term", "CL Extensible", "CL Date Published", "CL Status",
               "CL Ext Code ID", "CL Submission Value", "CL Synonym", "CL Definition", "CL Preferred Term"]

    def __init__(self, odmlib_mdv, data_path):
        self.mdv = odmlib_mdv
        self.path = data_path
        self.file_name = os.path.join(self.path, "codelists.csv")

    def extract(self):
        with open(self.file_name, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(self.HEADERS)
            for cl in self.mdv.CodeList:
                if cl.EnumeratedItem:
                    self._write_enumerated_item_row(cl, writer)
                elif cl.CodeListItem:
                    self._write_code_list_item_row(cl, writer)

    def _write_enumerated_item_row(self, cl, writer):
        attr = self._conditional_codelist_content(cl)
        for ei in cl.EnumeratedItem:
            order_number = ei.OrderNumber if ei.OrderNumber else ""
            ei_c_code = ei.Alias[0].Name if ei.Alias else ""
            date_published = ei.DatePublished if ei.DatePublished else ""
            status = ei.Status if ei.Status else ""
            ext_code_id = ei.ExtCodeID if ei.ExtCodeID else ""
            submission_value = ei.SubmissionValue if ei.SubmissionValue else ""
            synonym = ei.Synonym.TranslatedText._content if ei.Synonym is not None else ""
            definition = ei.Definition.TranslatedText._content if ei.Definition is not None else ""
            preferred_term = ei.PreferredTerm.TranslatedText._content if ei.PreferredTerm is not None else ""
            writer.writerow([cl.OID, cl.Name, attr["cl_c_code"], cl.DataType, order_number, ei.CodedValue, ei_c_code, "",
                             attr["comment_oid"], attr["is_non_std"], attr["standard_oid"],
                             date_published, status, ext_code_id, submission_value, synonym, definition, preferred_term, attr["CodeListExtensible"],
                             attr["DatePublished"], attr["Status"], attr["ExtCodeID"], attr["SubmissionValue"], attr["Synonym"],
                             attr["Definition"], attr["PreferredTerm"]])

    def _write_code_list_item_row(self, cl, writer):
        attr = self._conditional_codelist_content(cl)
        for cli in cl.CodeListItem:
            order_number = ""
            if cli.OrderNumber:
                order_number = cli.OrderNumber
            cli_c_code = ""
            if cli.Alias:
                cli_c_code = cli.Alias[0].Name
            decode = cli.Decode.TranslatedText[0]._content
            writer.writerow([cl.OID, cl.Name, attr["cl_c_code"], cl.DataType, order_number, cli.CodedValue, cli_c_code,
                             decode, attr["comment_oid"], attr["is_non_std"], attr["standard_oid"], attr["CodeListExtensible"],
                             attr["DatePublished"], attr["Status"], attr["ExtCodeID"], attr["SubmissionValue"], attr["Synonym"],
                             attr["Definition"], attr["PreferredTerm"]])

    def _conditional_codelist_content(self ,cl):
        attr = {}
        attr["cl_c_code"] = cl.Alias[0].Name if cl.Alias else ""
        attr["comment_oid"] = cl.CommentOID if cl.CommentOID else ""
        attr["is_non_std"] = cl.IsNonStandard if cl.IsNonStandard else ""
        attr["standard_oid"] = cl.StandardOID if cl.StandardOID else ""
        attr["CodeListExtensible"] = cl.CodeListExtensible if cl.CodeListExtensible else ""
        attr["DatePublished"] = cl.DatePublished if cl.DatePublished else ""
        attr["Status"] = cl.Status if cl.Status else ""
        attr["ExtCodeID"] = cl.ExtCodeID if cl.ExtCodeID else ""
        attr["SubmissionValue"] = cl.SubmissionValue if cl.SubmissionValue else ""
        attr["Synonym"] = cl.Synonym.TranslatedText._content if cl.Synonym is not None else ""
        attr["Definition"] = cl.Definition.TranslatedText._content if cl.Definition is not None else ""
        attr["PreferredTerm"] = cl.PreferredTerm.TranslatedText._content if cl.PreferredTerm is not None else ""
        return attr
