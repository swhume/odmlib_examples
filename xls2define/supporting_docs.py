from odmlib.define_2_0 import model as DEFINE


class SupportingDocuments:

    @staticmethod
    def create_annotatedcrf():
        acrf = DEFINE.AnnotatedCRF()
        dr = DEFINE.DocumentRef(leafID='LF.blankcrf')
        acrf.DocumentRef = dr
        return acrf

    @staticmethod
    def create_supplementaldoc():
        sdoc = DEFINE.SupplementalDoc()
        dr1 = DEFINE.DocumentRef(leafID='LF.ReviewersGuide')
        sdoc.DocumentRef.append(dr1)
        dr2 = DEFINE.DocumentRef(leafID='LF.ComplexAlgorithms')
        sdoc.DocumentRef.append(dr2)
        return sdoc
