import csv
from odmlib.ct_1_1_1 import model as CT
import datetime


class CT2ODM:
    def __init__(self, csv_file, odm_file, standard, package_date):
        self.csv_file = csv_file
        self.odm_file = odm_file
        self.standard = standard
        self.pkg_date = package_date

    def create(self):
        odm = self._create_odm()
        odm.Study.append(self._create_study())
        odm.Study[0].MetaDataVersion.append(self._create_mdv())
        with open(self.csv_file, "r") as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter='\t')
            line_count = 0
            cl_dict = {}
            cl_c_code = ""
            cl = None
            for row in csv_reader:
                if row["Code"] and row["Codelist Extensible (Yes/No)"] and not row["Codelist Code"]:
                    if cl_dict and cl_c_code != row["Code"]:
                        self._complete_codelist(odm, cl, cl_dict)
                    # assumes Codelist comes before associated terms
                    cl, cl_dict = self._create_codelist(row)
                    cl_c_code = row["Code"]
                else:
                    cl.EnumeratedItem.append(self._create_enumerated_item(row))
                line_count += 1
            self._complete_codelist(odm, cl, cl_dict)
            print(f'Processed {line_count} lines.')
            odm.write_xml(self.odm_file)

    def _create_enumerated_item(self, row):
        ei = CT.EnumeratedItem(CodedValue=row["CDISC Submission Value"], ExtCodeID=row["Code"])
        if row["CDISC Synonym(s)"]:
            for synonym in self._get_synonyms(row["CDISC Synonym(s)"]):
                ei.CDISCSynonym.append(CT.CDISCSynonym(_content=synonym))
        ei.CDISCDefinition = CT.CDISCDefinition(_content=row["CDISC Definition"])
        ei.PreferredTerm = CT.PreferredTerm(_content=row["NCI Preferred Term"])
        return ei

    def _complete_codelist(self, odm, cl, cl_dict):
        self._update_codelist(cl, cl_dict)
        odm.Study[0].MetaDataVersion[0].CodeList.append(cl)

    def _update_codelist(self, cl, cl_dict):
        cl.CDISCSubmissionValue = CT.CDISCSubmissionValue(_content=cl_dict["sub_val"])
        cl.CDISCSynonym = CT.CDISCSynonym(_content=cl_dict["synonyms"])
        cl.PreferredTerm = CT.PreferredTerm(_content=cl_dict["preferred_term"])

    def _create_codelist(self, row):
        cl = CT.CodeList(
            OID="CL." + row["Code"] + "." + row["CDISC Submission Value"],
            Name=row["CDISC Synonym(s)"],
            DataType="text",
            ExtCodeID=row["Code"],
            CodeListExtensible=row["Codelist Extensible (Yes/No)"]
        )
        cl.Description = CT.Description()
        cl.Description.TranslatedText.append(CT.TranslatedText(_content=row["CDISC Definition"], lang="en"))
        cl_dict = {
            "sub_val": row["CDISC Submission Value"],
            "synonyms": row["CDISC Synonym(s)"],
            "preferred_term": row["NCI Preferred Term"]
        }
        return cl, cl_dict

    def _get_synonyms(self, synonyms_string):
        synonyms = []
        for synonym in synonyms_string.split(";"):
            synonyms.append(synonym.strip())
        return synonyms

    def _create_odm(self):
        odm = CT.ODM(
            FileOID="CDISC_CT." + self.standard + "." + self.pkg_date,
            AsOfDateTime=self.pkg_date + "T00:00:00",
            CreationDateTime=self._set_datetime(),
            ODMVersion="1.3.2",
            FileType="Snapshot",
            Granularity="Metadata",
            Originator="Sam Hume",
            SourceSystem="NCI Thesaurus",
            SourceSystemVersion=self.pkg_date
        )
        return odm

    def _create_study(self):
        """
        create the study ODMLIB object from the Study worksheet and return it
        :param rows: dictionary created from the rows in the study worksheet
        :return: odmlib Study object
        """
        study = CT.Study(OID="CDISC_CT." + self.standard + "." + self.pkg_date)
        gv = CT.GlobalVariables()
        gv.StudyName = CT.StudyName(_content="CDISC " + self.standard + " Controlled Terminology")
        gv.StudyDescription = CT.StudyDescription(_content="CDISC " + self.standard + " Controlled Terminology, " + self.pkg_date)
        gv.ProtocolName = CT.ProtocolName(_content="CDISC " + self.standard + " Controlled Terminology")
        study.GlobalVariables = gv
        return study


    def _create_mdv(self):
        """
        create the MetaDataVersion ODMLIB object and return it
        :return: odmlib MetaDataVersion object
        """
        mdv = CT.MetaDataVersion(
            OID="CDISC_CT_MetaDataVersion." + self.standard + "." + self.pkg_date,
            Name="CDISC " + self.standard + " Controlled Terminology",
            Description="CDISC " + self.standard + " Controlled Terminology, " + self.pkg_date,
        )
        return mdv

    def _set_datetime(self):
        """return the current datetime in ISO 8601 format"""
        return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()


if __name__ == '__main__':
    ct2odm = CT2ODM(csv_file="./data/sdtm-ct.txt", odm_file="./data/sdtm-ct.xml", standard="SDTM", package_date="2021-06-25")
    ct2odm.create()
