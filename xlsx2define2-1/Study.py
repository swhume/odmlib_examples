from odmlib.define_2_1 import model as DEFINE
import define_object


class Study(define_object.DefineObject):
    """ create a Define-XML v2.1 Study element object and initialize the MetaDataVersion object """
    def __init__(self):
        super().__init__()

    def create_define_objects(self, sheet, objects, lang, acrf):
        """
        parse each row in the Excel sheet and create ODMLIB objects to return in the objects dictionary
        :param sheet: xlrd Excel sheet object
        :param objects: dictionary of ODMLIB objects updated by this method
        :param lang: xml:lang setting for TranslatedText
        """
        self.lang = lang
        self.acrf = acrf
        self.sheet = sheet
        rows = {}
        for row in sheet.iter_rows(min_row=1, min_col=1, max_col=2, values_only=True):
            row_content = self._load_row(row)
            rows.update(row_content)
        self.lang = rows["Language"]
        self.acrf = rows["Annotated CRF"]
        objects["Study"] = self._create_study_object(rows)
        objects["MetaDataVersion"] = self._create_metadataversion_object(rows)

    def _create_study_object(self, rows):
        """
        create the study ODMLIB object from the Study worksheet and return it
        :param rows: dictionary created from the rows in the study worksheet
        :return: odmlib Study object
        """
        study_oid = self.generate_oid(['ODM', rows["StudyName"]])
        study = DEFINE.Study(OID=study_oid)
        gv = DEFINE.GlobalVariables()
        gv.StudyName = DEFINE.StudyName(_content=rows["StudyName"])
        gv.StudyDescription = DEFINE.StudyDescription(_content=rows["StudyDescription"])
        gv.ProtocolName = DEFINE.ProtocolName(_content=rows["ProtocolName"])
        study.GlobalVariables = gv
        return study

    def _create_metadataversion_object(self, rows):
        """
        create the MetaDataVersion ODMLIB object from the Study worksheet and return it
        :param rows: dictionary created from the rows in the study worksheet
        :return: odmlib MetaDataVersion object
        """
        mdv_oid = self.generate_oid(["MDV", rows["StudyName"]])
        mdv = DEFINE.MetaDataVersion(OID=mdv_oid, Name="MDV " + rows["StudyName"], Description="Data Definitions for "
                                     + rows["StudyName"], DefineVersion="2.1.0")
        return mdv

    def _load_row(self, row_values):
        """
        load the Study worksheet row and return a dictionary
        :param row_idx: index indicating the row to load
        :return: dictionary with the row attribute as key and value as dictionary value
        """
        row = {}
        row[row_values[0]] = row_values[1]
        return row
