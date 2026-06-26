"""
acme_odm_1_0 -- a minimal local ODM 1.3.2 extension model.

This package shows how to build your own odmlib extension model. It adds a single vendor
attribute, ``acme:Label``, to ``ItemDef`` in a custom namespace.

Two rules make a local model work with the odmlib loaders:

1. Register every custom namespace at import time with ``NamespaceRegistry``.
2. The loader instantiates each element by class name and only recurses into the child
   descriptors found in that class's OWN ``__dict__``. So every element that appears in your
   documents needs a class here, and each class must re-declare (by referencing the base class)
   the child elements and attributes it should carry. New extension attributes are added with
   ``T.<type>(namespace="<prefix>")``.

Because of rule 2 this model only covers the small slice of ODM used by ``data/acme-odm.xml``
(ODM > Study > GlobalVariables / MetaDataVersion > ItemDef > Description > TranslatedText). A
real extension would re-declare the full tree (see the vendor models in the odmlib_snippets repo).
"""
import odmlib.odm_1_3_2.model as ODM
import odmlib.typed as T
import odmlib.ns_registry as NS

# 1. register the custom namespace (prefix -> URI) at import time
NS.NamespaceRegistry(prefix="acme", uri="http://www.acme.com/ns/odm-ext/v1.0")


class TranslatedText(ODM.TranslatedText):
    lang = ODM.TranslatedText.lang
    _content = ODM.TranslatedText._content


class Description(ODM.Description):
    TranslatedText = ODM.Description.TranslatedText


class ItemDef(ODM.ItemDef):
    OID = ODM.ItemDef.OID
    Name = ODM.ItemDef.Name
    DataType = ODM.ItemDef.DataType
    # the custom extension attribute, in the "acme" namespace
    Label = T.String(namespace="acme")
    Description = ODM.ItemDef.Description


class MetaDataVersion(ODM.MetaDataVersion):
    OID = ODM.MetaDataVersion.OID
    Name = ODM.MetaDataVersion.Name
    ItemDef = ODM.MetaDataVersion.ItemDef


class StudyName(ODM.StudyName):
    _content = ODM.StudyName._content


class StudyDescription(ODM.StudyDescription):
    _content = ODM.StudyDescription._content


class ProtocolName(ODM.ProtocolName):
    _content = ODM.ProtocolName._content


class GlobalVariables(ODM.GlobalVariables):
    StudyName = ODM.GlobalVariables.StudyName
    StudyDescription = ODM.GlobalVariables.StudyDescription
    ProtocolName = ODM.GlobalVariables.ProtocolName


class Study(ODM.Study):
    OID = ODM.Study.OID
    GlobalVariables = ODM.Study.GlobalVariables
    MetaDataVersion = ODM.Study.MetaDataVersion


class ODM(ODM.ODM):
    FileOID = ODM.ODM.FileOID
    CreationDateTime = ODM.ODM.CreationDateTime
    AsOfDateTime = ODM.ODM.AsOfDateTime
    ODMVersion = ODM.ODM.ODMVersion
    FileType = ODM.ODM.FileType
    Granularity = ODM.ODM.Granularity
    Originator = ODM.ODM.Originator
    SourceSystem = ODM.ODM.SourceSystem
    Study = ODM.ODM.Study
