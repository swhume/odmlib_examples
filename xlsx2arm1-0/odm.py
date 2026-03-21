from odmlib.arm_1_0 import model as DEFINE
import datetime


class ODM:
    def __init__(self):
        self.attrs = self._set_attributes()

    def create_define_objects(self):
        odm = DEFINE.ODM(**self.attrs)
        return odm

    def _set_attributes(self):
        return {"FileOID": "ODM.DEFINE21.TEST.001", "AsOfDateTime": self._set_datetime(),
                 "CreationDateTime": self._set_datetime(), "ODMVersion": "1.3.2", "FileType": "Snapshot",
                 "Originator": "Michael Kilhullen", "SourceSystem": "odmlib", "SourceSystemVersion": "0.2", "Context": "Other"}

    def _set_datetime(self):
        """return the current datetime in ISO 8601 format"""
        return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
