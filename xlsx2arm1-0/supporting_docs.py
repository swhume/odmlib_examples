from odmlib.arm_1_0 import model as DEFINE


class SupportingDocuments:

    @staticmethod
    def create_annotatedcrf(annotated_crf):
        acrf = DEFINE.AnnotatedCRF()
        dr = DEFINE.DocumentRef(leafID=annotated_crf)
        acrf.DocumentRef = dr
        return acrf

    @staticmethod
    def create_supplementaldoc(annotated_crf, leaf_objects):
        sdoc = DEFINE.SupplementalDoc() if leaf_objects else None
        for lo in leaf_objects:
            if leaf_objects and lo.ID != annotated_crf:
                dr = DEFINE.DocumentRef(leafID=lo.ID)
                sdoc.DocumentRef.append(dr)
        return sdoc
