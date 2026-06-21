import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from oid_generator import OIDGenerator


class TestOIDGenerate:
    """Tests for pattern-based OID generation."""

    @pytest.fixture
    def gen(self):
        return OIDGenerator()

    def test_basic_pattern_substitution(self, gen):
        oid = gen.generate("IT.{Dataset}.{Variable}", {"Dataset": "DM", "Variable": "STUDYID"})
        assert oid == "IT.DM.STUDYID"

    def test_single_placeholder(self, gen):
        oid = gen.generate("IG.{Dataset}", {"Dataset": "AE"})
        assert oid == "IG.AE"

    def test_oids_are_uppercased(self, gen):
        oid = gen.generate("IT.{Dataset}.{Variable}", {"Dataset": "dm", "Variable": "studyid"})
        assert oid == "IT.DM.STUDYID"

    def test_mixed_case_pattern_uppercased(self, gen):
        oid = gen.generate("ig.{Dataset}", {"Dataset": "DM"})
        assert oid == "IG.DM"

    def test_deterministic_same_input_same_output(self):
        """Two separate generators with same input produce same OID string."""
        gen1 = OIDGenerator()
        gen2 = OIDGenerator()
        oid1 = gen1.generate("IT.{Dataset}.{Variable}", {"Dataset": "DM", "Variable": "AGE"})
        oid2 = gen2.generate("IT.{Dataset}.{Variable}", {"Dataset": "DM", "Variable": "AGE"})
        assert oid1 == oid2

    def test_duplicate_oid_raises_value_error(self, gen):
        gen.generate("IG.{Dataset}", {"Dataset": "DM"})
        with pytest.raises(ValueError, match="Duplicate OID"):
            gen.generate("IG.{Dataset}", {"Dataset": "DM"})

    def test_missing_placeholder_raises_key_error(self, gen):
        with pytest.raises(KeyError, match="Variable"):
            gen.generate("IT.{Dataset}.{Variable}", {"Dataset": "DM"})

    def test_extra_values_ignored(self, gen):
        oid = gen.generate("IG.{Dataset}", {"Dataset": "DM", "Extra": "ignored"})
        assert oid == "IG.DM"

    def test_numeric_value_converted_to_string(self, gen):
        oid = gen.generate("STD.{index}", {"index": 1})
        assert oid == "STD.1"

    def test_multiple_oids_tracked(self, gen):
        gen.generate("IG.{Dataset}", {"Dataset": "DM"})
        gen.generate("IG.{Dataset}", {"Dataset": "AE"})
        gen.generate("IG.{Dataset}", {"Dataset": "VS"})
        assert gen.exists("IG.DM")
        assert gen.exists("IG.AE")
        assert gen.exists("IG.VS")


class TestOIDRegister:
    """Tests for registering column-sourced OIDs."""

    @pytest.fixture
    def gen(self):
        return OIDGenerator()

    def test_register_oid(self, gen):
        gen.register("IG.DM")
        assert gen.exists("IG.DM")

    def test_register_uppercases(self, gen):
        gen.register("ig.dm")
        assert gen.exists("IG.DM")

    def test_register_duplicate_raises_value_error(self, gen):
        gen.register("IG.DM")
        with pytest.raises(ValueError, match="Duplicate OID"):
            gen.register("IG.DM")

    def test_register_conflicts_with_generated(self, gen):
        gen.generate("IG.{Dataset}", {"Dataset": "DM"})
        with pytest.raises(ValueError, match="Duplicate OID"):
            gen.register("IG.DM")

    def test_generate_conflicts_with_registered(self, gen):
        gen.register("IG.DM")
        with pytest.raises(ValueError, match="Duplicate OID"):
            gen.generate("IG.{Dataset}", {"Dataset": "DM"})


class TestOIDExists:
    """Tests for the exists() check."""

    @pytest.fixture
    def gen(self):
        return OIDGenerator()

    def test_exists_false_initially(self, gen):
        assert gen.exists("IG.DM") is False

    def test_exists_case_insensitive(self, gen):
        gen.register("IG.DM")
        assert gen.exists("ig.dm") is True
        assert gen.exists("IG.DM") is True


class TestOIDReset:
    """Tests for resetting the OID registry."""

    def test_reset_clears_all(self):
        gen = OIDGenerator()
        gen.generate("IG.{Dataset}", {"Dataset": "DM"})
        gen.register("IT.DM.STUDYID")
        gen.reset()
        assert gen.exists("IG.DM") is False
        assert gen.exists("IT.DM.STUDYID") is False

    def test_generate_after_reset_succeeds(self):
        gen = OIDGenerator()
        gen.generate("IG.{Dataset}", {"Dataset": "DM"})
        gen.reset()
        oid = gen.generate("IG.{Dataset}", {"Dataset": "DM"})
        assert oid == "IG.DM"
