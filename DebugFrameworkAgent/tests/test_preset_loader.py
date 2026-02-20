"""
test_preset_loader.py — Tests for scripts/_core/preset_loader.py

Run with:
    pytest DebugFrameworkAgent/tests/test_preset_loader.py -v
"""

import json
import pathlib
import copy
import pytest
import sys

# Add scripts dir to path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from _core import preset_loader


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def presets_data():
    return preset_loader.load_all()


@pytest.fixture()
def minimal_custom_presets(tmp_path):
    """A valid minimal custom presets file."""
    data = {
        "version": "2.0",
        "common": {
            "custom_test": {
                "description": "Custom test preset",
                "ask_user": [],
                "experiment": {"Test Name": "CustomTest", "Loops": 5},
            }
        }
    }
    p = tmp_path / "custom.json"
    p.write_text(json.dumps(data))
    return p


# ---------------------------------------------------------------------------
# load_all
# ---------------------------------------------------------------------------

class TestLoadAll:
    def test_returns_dict(self, presets_data):
        assert isinstance(presets_data, dict)

    def test_has_version(self, presets_data):
        assert presets_data.get("_meta", {}).get("version") == "2.0"

    def test_has_common_section(self, presets_data):
        assert "common" in presets_data

    def test_has_product_sections(self, presets_data):
        for product in ("GNR", "CWF", "DMR"):
            assert product in presets_data, f"Missing product section: {product}"

    def test_common_has_presets(self, presets_data):
        assert len(presets_data["common"]) > 0

    def test_load_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            preset_loader.load_all(pathlib.Path("/nonexistent/path/presets.json"))


# ---------------------------------------------------------------------------
# filter_by_product
# ---------------------------------------------------------------------------

class TestFilterByProduct:
    def test_filter_gnr_returns_list(self, presets_data):
        result = preset_loader.filter_by_product(presets_data, "GNR")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_filter_all_returns_all_products(self, presets_data):
        # "all" product sentinel returns union across all 3 products
        all_results = preset_loader.filter_by_product(presets_data, "ALL")
        gnr_results = preset_loader.filter_by_product(presets_data, "GNR")
        assert len(all_results) >= len(gnr_results)

    def test_each_result_has_meta_keys(self, presets_data):
        results = preset_loader.filter_by_product(presets_data, "GNR")
        for item in results:
            assert "_key" in item
            assert "_product" in item
            assert "_category" in item

    def test_filter_by_category(self, presets_data):
        content = preset_loader.filter_by_product(presets_data, "GNR", category="content")
        for item in content:
            assert item["_category"] == "content"

    def test_common_presets_present_in_all_products(self, presets_data):
        gnr = {p["_key"] for p in preset_loader.filter_by_product(presets_data, "GNR")}
        cwf = {p["_key"] for p in preset_loader.filter_by_product(presets_data, "CWF")}
        dmr = {p["_key"] for p in preset_loader.filter_by_product(presets_data, "DMR")}
        common_keys = set(presets_data.get("common", {}).keys())
        for k in common_keys:
            assert k in gnr, f"Common preset '{k}' missing from GNR filter"
            assert k in cwf, f"Common preset '{k}' missing from CWF filter"
            assert k in dmr, f"Common preset '{k}' missing from DMR filter"


# ---------------------------------------------------------------------------
# get_preset
# ---------------------------------------------------------------------------

class TestGetPreset:
    def test_get_common_preset(self, presets_data):
        common_keys = list(presets_data.get("common", {}).keys())
        assert common_keys, "No common presets found"
        preset = preset_loader.get_preset(presets_data, common_keys[0])
        assert isinstance(preset, dict)

    def test_get_gnr_specific_preset(self, presets_data):
        gnr_presets = presets_data.get("GNR", {})
        if not gnr_presets:
            pytest.skip("No GNR-specific presets in file")
        key = next(iter(gnr_presets))
        # Access from any of the sub-categories
        for subcat in gnr_presets.values():
            if isinstance(subcat, dict) and key not in subcat:
                pass
        # Just verify get_preset doesn't crash with a product hint
        # Use a real key from flattened listing
        results = preset_loader.filter_by_product(presets_data, "GNR")
        if not results:
            pytest.skip("No GNR presets")
        key = results[0]["_key"]
        preset = preset_loader.get_preset(presets_data, key, product="GNR")
        assert isinstance(preset, dict)

    def test_get_nonexistent_preset_raises(self, presets_data):
        with pytest.raises(KeyError):
            preset_loader.get_preset(presets_data, "does_not_exist_xyz")

    def test_preset_has_experiment_key(self, presets_data):
        common_keys = list(presets_data.get("common", {}).keys())
        assert common_keys
        preset = preset_loader.get_preset(presets_data, common_keys[0])
        assert "experiment" in preset


# ---------------------------------------------------------------------------
# validate_schema
# ---------------------------------------------------------------------------

class TestValidateSchema:
    def test_valid_schema_passes(self, presets_data):
        ok, errors = preset_loader.validate_schema(presets_data)
        assert ok, f"Schema errors: {errors}"

    def test_empty_dict_fails(self):
        ok, errors = preset_loader.validate_schema({})
        assert not ok
        assert len(errors) > 0

    def test_missing_version_fails(self, presets_data):
        bad = copy.deepcopy(presets_data)
        # Remove _meta to simulate a corrupted / minimal file
        bad.pop("_meta", None)
        bad.pop("common", None)
        ok, errors = preset_loader.validate_schema(bad)
        assert not ok


# ---------------------------------------------------------------------------
# merge_custom
# ---------------------------------------------------------------------------

class TestMergeCustom:
    def test_merge_adds_custom_key(self, presets_data, minimal_custom_presets):
        merged = preset_loader.merge_custom(presets_data, minimal_custom_presets)
        assert "_custom" in merged

    def test_original_not_mutated(self, presets_data, minimal_custom_presets):
        _ = preset_loader.merge_custom(presets_data, minimal_custom_presets)
        assert "_custom" not in presets_data

    def test_custom_preset_accessible(self, presets_data, minimal_custom_presets):
        merged = preset_loader.merge_custom(presets_data, minimal_custom_presets)
        preset = preset_loader.get_preset(merged, "custom_test")
        assert preset["experiment"]["Loops"] == 5
