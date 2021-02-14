import odmlib.odm_loader as OL
import odmlib.loader as LD
import os

# An odmlib example application

SOURCE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash-odm-source.xml')
TARGET = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash-odm-target.xml')


class MergeODM:
    def __init__(self, source_file, target_file, form_oid):
        """ simple merge application that generates a target ODM file with a CRF moved from a source ODM file """
        self.source_file = source_file
        self.target_file = target_file
        self.form_oid = form_oid

    def merge(self):
        source_loader = LD.ODMLoader(OL.XMLODMLoader())
        source_loader.open_odm_document(self.source_file)
        source_mdv = source_loader.MetaDataVersion()
        target_loader = LD.ODMLoader(OL.XMLODMLoader())
        target_loader.open_odm_document(self.target_file)
        target_root = target_loader.root()
        self._merge_form_def(source_mdv, target_root.Study[0].MetaDataVersion[0])
        self._write_target_odm(target_root)

    def _merge_form_def(self, source_mdv, target_mdv):
        vs_form = source_mdv.find("FormDef", "OID", self.form_oid)
        if self._element_does_not_exist(target_mdv, vs_form.OID, "FormDef"):
            target_mdv.FormDef.append(vs_form)
            self._merge_item_group_def(source_mdv, target_mdv, vs_form)

    def _merge_item_group_def(self, source_mdv, target_mdv, form):
        for igr in form.ItemGroupRef:
            igd = source_mdv.find("ItemGroupDef", "OID", igr.ItemGroupOID)
            if self._element_does_not_exist(target_mdv, igd.OID, "ItemGroupDef"):
                target_mdv.ItemGroupDef.append(igd)
                self._merge_items(source_mdv, target_mdv, igd)

    def _merge_items(self, source_mdv, target_mdv, igd):
        for itr in igd.ItemRef:
            item = source_mdv.find("ItemDef", "OID", itr.ItemOID)
            if self._element_does_not_exist(target_mdv, item.OID, "ItemDef"):
                target_mdv.ItemDef.append(item)
                self._merge_method(source_mdv, target_mdv, itr)
                self._merge_codelist(source_mdv, target_mdv, item)

    def _merge_method(self, source_mdv, target_mdv, itr):
        if itr.MethodOID:
            method = source_mdv.find("MethodDef", "OID", itr.MethodOID)
            if self._element_does_not_exist(target_mdv, method.OID, "MethodDef"):
                target_mdv.MethodDef.append(method)

    def _merge_codelist(self, source_mdv, target_mdv, item):
        if item.CodeListRef:
            codelist = source_mdv.find("CodeList", "OID", item.CodeListRef.CodeListOID)
            if self._element_does_not_exist(target_mdv, codelist.OID, "CodeList"):
                target_mdv.CodeList.append(codelist)

    def _write_target_odm(self, target_root):
        target_root.write_xml(self.target_file)

    def _element_does_not_exist(self, mdv, oid, element_type):
        if mdv.find(element_type, "OID", oid):
            return False
        else:
            return True


def main():
    """ main driver method that merges a CRF in the source ODM file into a target ODM file """
    m = MergeODM(SOURCE, TARGET, "ODM.F.VS")
    m.merge()


if __name__ == "__main__":
    main()
