"""Integration test: verify gendefine produces functionally equivalent output to xlsx2define2-1."""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config_loader import MappingConfig
from spreadsheet_reader import SpreadsheetReader
from intermediate_builder import IntermediateBuilder
from define_builder import DefineBuilder
from oid_generator import OIDGenerator
from value_transformer import ValueTransformer


# Paths relative to the gendefine/ directory
GENDEFINE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(GENDEFINE_DIR, "data")
MAPPINGS_DIR = os.path.join(GENDEFINE_DIR, "mappings")
REFERENCE_XML = os.path.join(GENDEFINE_DIR, "..", "xlsx2define2-1", "data", "odmlib-roundtrip-define.xml")
INPUT_XLSX = os.path.join(DATA_DIR, "odmlib-define-metadata.xlsx")


def _count_elements(path):
    """Parse XML and return dict of tag -> count."""
    tree = ET.parse(path)
    counts = {}
    for elem in tree.getroot().iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        counts[tag] = counts.get(tag, 0) + 1
    return counts


def _get_oids(path, element_name, attr="OID"):
    """Extract OID values for a given element type."""
    tree = ET.parse(path)
    oids = set()
    for elem in tree.getroot().iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == element_name and attr in elem.attrib:
            oids.add(elem.attrib[attr])
    return oids


def _flatten_elements(path):
    """Return list of (tag, attribs, text) for all elements (excluding ODM root)."""
    tree = ET.parse(path)
    result = []
    for elem in tree.getroot().iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "ODM":
            continue  # Skip root (timestamps differ)
        result.append((tag, dict(sorted(elem.attrib.items())), (elem.text or "").strip()))
    return result


@pytest.fixture(scope="module")
def generated_xml():
    """Run the full gendefine pipeline and return path to generated XML."""
    if not os.path.exists(INPUT_XLSX):
        pytest.skip("Test data not available: odmlib-define-metadata.xlsx")
    if not os.path.exists(REFERENCE_XML):
        pytest.skip("Reference XML not available: odmlib-roundtrip-define.xml")

    mapping_path = os.path.join(MAPPINGS_DIR, "odmlib-format.json")
    config = MappingConfig(mapping_path)

    reader = SpreadsheetReader(config)
    raw_data = reader.read_workbook(INPUT_XLSX)

    oid_gen = OIDGenerator()
    transformer = ValueTransformer(config.value_transforms, config.defaults)
    builder = IntermediateBuilder(config, oid_gen, transformer)
    intermediate = builder.build(raw_data)

    lang = config.global_settings.get("language", "en")
    define_builder = DefineBuilder(intermediate, lang)
    odm = define_builder.build()

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        output_path = f.name
    odm.write_xml(output_path)
    yield output_path
    os.unlink(output_path)


class TestElementCounts:
    def test_all_element_counts_match(self, generated_xml):
        ref_counts = _count_elements(REFERENCE_XML)
        gen_counts = _count_elements(generated_xml)
        for tag in ref_counts:
            assert gen_counts.get(tag, 0) == ref_counts[tag], \
                f"{tag}: expected {ref_counts[tag]}, got {gen_counts.get(tag, 0)}"


class TestOIDValues:
    @pytest.mark.parametrize("element", [
        "ItemGroupDef", "ItemDef", "CodeList", "MethodDef",
        "CommentDef", "WhereClauseDef", "ValueListDef",
    ])
    def test_oid_values_match(self, generated_xml, element):
        ref_oids = _get_oids(REFERENCE_XML, element)
        gen_oids = _get_oids(generated_xml, element)
        assert ref_oids == gen_oids, f"{element} OID mismatch"


class TestAttributeValues:
    def test_all_elements_match(self, generated_xml):
        ref_flat = _flatten_elements(REFERENCE_XML)
        gen_flat = _flatten_elements(generated_xml)
        assert len(ref_flat) == len(gen_flat), \
            f"Element count mismatch: ref={len(ref_flat)} gen={len(gen_flat)}"
        for i, (rf, gf) in enumerate(zip(ref_flat, gen_flat)):
            rtag, rattrs, rtext = rf
            gtag, gattrs, gtext = gf
            assert rtag == gtag, f"Element {i}: tag mismatch ref={rtag} gen={gtag}"
            assert rattrs == gattrs, f"Element {i} ({rtag}): attr mismatch"
            assert rtext == gtext, f"Element {i} ({rtag}): text mismatch ref={rtext!r} gen={gtext!r}"
