import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_element as OE
import odmlib.typed as T
import odmlib.ns_registry as NS


NS.NamespaceRegistry(prefix="mdr", uri="http://www.cdisc.org/ns/library-xml/v1.0")

# TODO TranslatedText element content is required as part of ODM, but Library publishes empty TranslatedText
# class TranslatedText(ODM.TranslatedText):
#     lang = ODM.TranslatedText.lang
#     _content = ODM.TranslatedText._content


class TranslatedText(OE.ODMElement):
    lang = T.String(namespace="xml")
    _content = T.String(required=False)


class Alias(ODM.Alias):
    Context = ODM.Alias.Context
    Name = ODM.Alias.Name


class StudyDescription(ODM.StudyDescription):
    _content = ODM.StudyDescription._content


class ProtocolName(ODM.ProtocolName):
    _content = ODM.ProtocolName._content


class StudyName(ODM.StudyName):
    _content = ODM.StudyName._content


class GlobalVariables(ODM.GlobalVariables):
    StudyName = ODM.GlobalVariables.StudyName
    StudyDescription = ODM.GlobalVariables.StudyDescription
    ProtocolName = ODM.GlobalVariables.ProtocolName


class Description(ODM.Description):
    TranslatedText = ODM.Description.TranslatedText


class ItemRef(ODM.ItemRef):
    ItemOID = ODM.ItemRef.ItemOID
    OrderNumber = ODM.ItemRef.OrderNumber
    Mandatory = ODM.ItemRef.Mandatory
    KeySequence = ODM.ItemRef.KeySequence
    MethodOID = ODM.ItemRef.MethodOID
    Role = ODM.ItemRef.Role
    RoleCodeListOID = ODM.ItemRef.RoleCodeListOID


class Class(OE.ODMElement):
    namespace = "mdr"
    Name = T.Name(required=True)


class ItemGroupDef(ODM.ItemGroupDef):
    OID = ODM.ItemGroupDef.OID
    Name = ODM.ItemGroupDef.Name
    Repeating = ODM.ItemGroupDef.Repeating
    IsReferenceData = ODM.ItemGroupDef.IsReferenceData
    SASDatasetName = ODM.ItemGroupDef.SASDatasetName
    Domain = ODM.ItemGroupDef.Domain
    Purpose = ODM.ItemGroupDef.Purpose
    Description = ODM.ItemGroupDef.Description
    ItemRef = ODM.ItemGroupDef.ItemRef
    Alias = ODM.ItemGroupDef.Alias
    Class = T.ODMObject(element_class=Class, namespace="mdr")

    def __len__(self):
        return len(self.ItemRef)

    def __getitem__(self, position):
        return self.ItemRef[position]

    def __iter__(self):
        return iter(self.ItemRef)


class CheckValue(ODM.CheckValue):
    _content = T.String(required=False)


class FormalExpression(ODM.FormalExpression):
    Context = ODM.FormalExpression.Context
    _content = ODM.FormalExpression._content


class RangeCheck(ODM.RangeCheck):
    Comparator = ODM.RangeCheck.Comparator
    SoftHard = ODM.RangeCheck.SoftHard
    CheckValue = T.ODMListObject(element_class=CheckValue)


class CodeListRef(ODM.CodeListRef):
    CodeListOID = ODM.CodeListRef.CodeListOID


class AltCodeListRef(OE.ODMElement):
    namespace = "mdr"
    CodeListOID = T.OIDRef(required=True)


class Prompt(OE.ODMElement):
    namespace = "mdr"
    TranslatedText = ODM.Description.TranslatedText


class CRFCompletionInstructions(OE.ODMElement):
    namespace = "mdr"
    TranslatedText = ODM.Description.TranslatedText


class ImplementationNotes(OE.ODMElement):
    namespace = "mdr"
    TranslatedText = ODM.Description.TranslatedText


class MappingInstructions(OE.ODMElement):
    namespace = "mdr"
    TranslatedText = ODM.Description.TranslatedText


class Definition(OE.ODMElement):
    namespace = "mdr"
    TranslatedText = ODM.Description.TranslatedText


class Question(ODM.Question):
    Question = ODM.Question


class ItemDef(ODM.ItemDef):
    OID = ODM.ItemDef.OID
    Name = ODM.ItemDef.Name
    DataType = ODM.ItemDef.DataType
    Length = ODM.ItemDef.Length
    SignificantDigits = ODM.ItemDef.SignificantDigits
    SASFieldName = ODM.ItemDef.SASFieldName
    Core = T.ExtendedValidValues(valid_values=["HR", "R/C", "O"], namespace="mdr")
    SubmissionDataType = T.ExtendedValidValues(required=True, valid_values=["Char", "Num"], namespace="mdr")
    VariableSet = T.String(namespace="mdr")
    DescribedValueDomain = T.String(namespace="mdr")
    Description = ODM.ItemDef.Description
    Question = ODM.ItemDef.Question
    CodeListRef = ODM.ItemDef.CodeListRef
    Alias = T.ODMListObject(element_class=Alias)
    AltCodeListRef = T.ODMListObject(element_class=AltCodeListRef, namespace="mdr")
    Prompt = T.ODMObject(element_class=Prompt, namespace="mdr")
    CRFCompletionInstructions = T.ODMObject(element_class=CRFCompletionInstructions, namespace="mdr")
    ImplementationNotes = T.ODMObject(element_class=ImplementationNotes, namespace="mdr")
    MappingInstructions = T.ODMObject(element_class=MappingInstructions, namespace="mdr")
    Definition = T.ODMObject(element_class=Definition, namespace="mdr")


class Decode(ODM.Decode):
    TranslatedText = ODM.Decode.TranslatedText


class CodeListItem(ODM.CodeListItem):
    CodedValue = ODM.CodeListItem.CodedValue
    Rank = ODM.CodeListItem.Rank
    OrderNumber = ODM.CodeListItem.OrderNumber
    Description = ODM.CodeList.Description
    Decode = ODM.CodeListItem.Decode
    Alias = ODM.CodeListItem.Alias


class EnumeratedItem(ODM.EnumeratedItem):
    CodedValue = ODM.EnumeratedItem.CodedValue
    Rank = ODM.EnumeratedItem.Rank
    OrderNumber = ODM.EnumeratedItem.OrderNumber
    Description = ODM.CodeList.Description
    Alias = ODM.EnumeratedItem.Alias


class ExternalCodeList(ODM.ExternalCodeList):
    Dictionary = ODM.ExternalCodeList.Dictionary
    Version = ODM.ExternalCodeList.Version
    ref = ODM.ExternalCodeList.ref
    href = ODM.ExternalCodeList.href


class CodeList(ODM.CodeList):
    OID = ODM.CodeList.OID
    Name = ODM.CodeList.Name
    DataType = ODM.CodeList.DataType
    SASFormatName = ODM.CodeList.SASFormatName
    Description = ODM.CodeList.Description
    CodeListItem = ODM.CodeList.CodeListItem
    EnumeratedItem = ODM.CodeList.EnumeratedItem
    ExternalCodeList = ODM.CodeList.ExternalCodeList
    Alias = ODM.CodeList.Alias


class MethodDef(ODM.MethodDef):
    OID = ODM.MethodDef.OID
    Name = ODM.MethodDef.Name
    Type = ODM.MethodDef.Type
    Description = ODM.MethodDef.Description
    FormalExpression = ODM.MethodDef.FormalExpression


class MetaDataVersion(ODM.MetaDataVersion):
    OID = ODM.MetaDataVersion.OID
    Name = ODM.MetaDataVersion.Name
    Description = ODM.MetaDataVersion.Description
    DatePublished = T.DateString(required=True, namespace="mdr")
    Status = T.ExtendedValidValues(valid_values=["Final", "Provisional", "Draft"], namespace="mdr")
    ItemGroupDef = ODM.MetaDataVersion.ItemGroupDef
    ItemDef = ODM.MetaDataVersion.ItemDef
    CodeList = ODM.MetaDataVersion.CodeList
    MethodDef = ODM.MetaDataVersion.MethodDef


class Study(ODM.Study):
    OID = ODM.Study.OID
    GlobalVariables = ODM.Study.GlobalVariables
    MetaDataVersion = T.ODMObject(required=True, element_class=MetaDataVersion)


class ODM(ODM.ODM):
    FileType = ODM.ODM.FileType
    FileOID = ODM.ODM.FileOID
    CreationDateTime = ODM.ODM.CreationDateTime
    AsOfDateTime = ODM.ODM.AsOfDateTime
    ODMVersion = ODM.ODM.ODMVersion
    Originator = ODM.ODM.Originator
    SourceSystem = ODM.ODM.SourceSystem
    SourceSystemVersion = ODM.ODM.SourceSystemVersion
    Granularity = T.ExtendedValidValues(valid_values=["Metadata"])
    schemaLocation = ODM.ODM.schemaLocation
    LibraryXMLVersion = T.ExtendedValidValues(required=True, valid_values=["1.0.0"], namespace="mdr")
    ID = ODM.ODM.ID
    Study = ODM.ODM.Study
