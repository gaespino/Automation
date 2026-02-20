"""
preset_loader.py — Load, filter, and merge experiment presets.

All paths are resolved relative to this file's own location so the package
can be dropped anywhere without editing paths.
No external dependencies.
"""

from __future__ import annotations
import json
import pathlib
from typing import Any

# --------------------------------------------------------------------------
# Locate defaults dir relative to *this file's* location:
# scripts/_core/preset_loader.py  →  ../../defaults/
# --------------------------------------------------------------------------
_DEFAULTS_DIR        = pathlib.Path(__file__).parent.parent.parent / "defaults"
_PRESETS_DIR         = _DEFAULTS_DIR / "presets"          # split-file directory (current)
_DEFAULT_PRESETS_PATH = _DEFAULTS_DIR / "experiment_presets.json"  # legacy single-file

VALID_PRODUCTS   = ("GNR", "CWF", "DMR")
VALID_CATEGORIES = ("common", "boot", "content", "fuse", "all")

# Keys inside a product section
_CATEGORY_MAP = {
    "boot":    "boot_cases",
    "content": "content_cases",
    "fuse":    "fuse_collection",
}

_REQUIRED_PRESET_KEYS = {"label", "description", "products", "ask_user", "experiment"}


# --------------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------------

def _load_raw(path: pathlib.Path | str) -> dict:
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Presets file not found: {p}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in presets file {p}: {exc}") from exc


def _load_split_dir(directory: pathlib.Path) -> dict:
    """
    Load presets from a split-file directory containing:
        common.json, GNR.json, CWF.json, DMR.json

    Merges them into the canonical dict shape:
        {_meta, common, GNR, CWF, DMR}
    which is identical to what the old monolithic file produced.
    """
    result: dict = {}

    common_path = directory / "common.json"
    if not common_path.exists():
        raise FileNotFoundError(
            f"Split presets directory is missing common.json: {directory}"
        )
    common_data = _load_raw(common_path)
    result["_meta"]  = common_data.get("_meta", {})
    result["common"] = common_data.get("common", {})

    for prod in VALID_PRODUCTS:
        prod_path = directory / f"{prod}.json"
        if not prod_path.exists():
            raise FileNotFoundError(
                f"Split presets directory is missing {prod}.json: {directory}"
            )
        prod_data = _load_raw(prod_path)
        result[prod] = prod_data.get(prod, {})

    return result


def _iter_category(data: dict, product: str, category_key: str):
    """Yield (key, preset_dict) for a product category section."""
    prod_data = data.get(product, {})
    section   = prod_data.get(category_key, {})
    yield from section.items()


def _validate_preset_schema(key: str, preset: Any) -> list[str]:
    errors = []
    if not isinstance(preset, dict):
        return [f"  [{key}] preset is not a dict"]
    missing = _REQUIRED_PRESET_KEYS - preset.keys()
    if missing:
        errors.append(f"  [{key}] missing keys: {sorted(missing)}")
    return errors


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def load_all(path: pathlib.Path | str | None = None) -> dict:
    """
    Load and return the full presets data as a merged dict.

    Returns the canonical structure: {_meta, common, GNR, CWF, DMR}.
    Raises FileNotFoundError or ValueError on bad input.

    Resolution order when *path* is omitted:
        1. defaults/presets/  directory (split-file layout — current default)
        2. defaults/experiment_presets.json  (legacy single file — fallback)

    When *path* is given:
        - Directory  → load as split-file layout
        - File path  → load as legacy single JSON
    """
    if path is None:
        if _PRESETS_DIR.exists():
            return _load_split_dir(_PRESETS_DIR)
        return _load_raw(_DEFAULT_PRESETS_PATH)   # legacy fallback

    p = pathlib.Path(path)
    if p.is_dir():
        return _load_split_dir(p)
    return _load_raw(p)   # single-file (keeps test_load_nonexistent_file_raises working)


def get_meta(data: dict) -> dict:
    """Return the _meta block."""
    return data.get("_meta", {})


def filter_by_product(
    data: dict,
    product: str,
    category: str = "all",
) -> list[dict]:
    """
    Return a flat list of preset records matching product + category.

    Each record is enriched with:
        _key      — the dict key
        _product  — which section it came from ("common" or product code)
        _category — "common" | "boot" | "content" | "fuse"

    Args:
        data:     Full presets dict (from load_all).
        product:  GNR | CWF | DMR  (case-insensitive).
        category: all | common | boot | content | fuse.
    """
    product  = product.upper()
    category = category.lower()

    # "all" product means iterate over every product + common
    if product == "ALL":
        results = []
        for prod in VALID_PRODUCTS:
            results.extend(filter_by_product(data, prod, category))
        # deduplicate common presets (they appear once per product)
        seen = set()
        deduped = []
        for item in results:
            k = (item["_key"], item["_product"])
            if k not in seen:
                seen.add(k)
                deduped.append(item)
        return deduped

    if product not in VALID_PRODUCTS:
        raise ValueError(f"Unknown product '{product}'. Must be one of {VALID_PRODUCTS}.")
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Unknown category '{category}'. Must be one of {VALID_CATEGORIES}.")

    results = []

    # ── Common presets ───────────────────────────────────────────────────
    if category in ("all", "common"):
        for key, preset in data.get("common", {}).items():
            prods = preset.get("products", [])
            if product in prods:
                results.append({**preset, "_key": key, "_product": "common", "_category": "common"})

    # ── Product-specific sections ─────────────────────────────────────────
    if category == "all":
        cats_to_include = list(_CATEGORY_MAP.keys())
    elif category != "common":
        cats_to_include = [category]
    else:
        cats_to_include = []

    for cat_name in cats_to_include:
        cat_key = _CATEGORY_MAP[cat_name]
        for key, preset in _iter_category(data, product, cat_key):
            results.append({**preset, "_key": key, "_product": product, "_category": cat_name})

    return results


def get_categories(data: dict, product: str) -> dict[str, list[dict]]:
    """
    Return an ordered dict of categories → preset list for the given product.
    Keys: "common", "boot", "content", "fuse" (only those with items).
    """
    product = product.upper()
    out = {}

    common = filter_by_product(data, product, "common")
    if common:
        out["common"] = common

    for cat_name in ("boot", "content", "fuse"):
        cat_key = _CATEGORY_MAP[cat_name]
        items = []
        for key, preset in _iter_category(data, product, cat_key):
            items.append({**preset, "_key": key, "_product": product, "_category": cat_name})
        if items:
            out[cat_name] = items

    return out


def get_preset(data: dict, key: str, product: str | None = None) -> dict:
    """
    Retrieve a single preset by its key.

    Searches common first, then all product sections if product is given, else all three.
    Raises KeyError if not found.
    """
    # Custom (injected via merge_custom)
    if key in data.get("_custom", {}):
        return data["_custom"][key]

    # Common
    if key in data.get("common", {}):
        return data["common"][key]

    products = [product.upper()] if product else list(VALID_PRODUCTS)
    for prod in products:
        for cat_key in _CATEGORY_MAP.values():
            section = data.get(prod, {}).get(cat_key, {})
            if key in section:
                return section[key]

    raise KeyError(f"Preset key '{key}' not found.")


def merge_custom(data: dict, custom_path: pathlib.Path | str) -> dict:
    """
    Load a user-provided custom preset JSON and merge it session-locally.

    The custom file can be:
    - A flat dict of preset_key → preset_dict   (simple format)
    - A full presets JSON with common/product structure

    Returns a *new* data dict (original is not mutated).
    Custom presets are injected under data["_custom"] and tagged with
    _product="custom", _category="custom" when iterated.

    Raises ValueError with a descriptive message if the file fails schema checks.
    """
    import copy
    raw = _load_raw(custom_path)

    # Detect format: if has "common" or product keys → full format, else flat
    is_full_format = bool(
        raw.get("common") or any(p in raw for p in VALID_PRODUCTS)
    )

    custom_presets: dict[str, dict] = {}

    if is_full_format:
        for key, preset in raw.get("common", {}).items():
            custom_presets[key] = preset
        for prod in VALID_PRODUCTS:
            for cat_key in _CATEGORY_MAP.values():
                for key, preset in raw.get(prod, {}).get(cat_key, {}).items():
                    custom_presets[key] = preset
    else:
        # Flat format
        custom_presets = {k: v for k, v in raw.items() if not k.startswith("_")}

    # Validate each custom preset — only require 'experiment' key (relax full schema)
    errors = []
    for key, preset in custom_presets.items():
        if not isinstance(preset, dict):
            errors.append(f"  [{key}] preset is not a dict")
        elif "experiment" not in preset:
            errors.append(f"  [{key}] missing required key: 'experiment'")
    if errors:
        raise ValueError(
            f"Custom preset file {custom_path} has schema errors:\n" + "\n".join(errors)
        )

    merged = copy.deepcopy(data)
    merged["_custom"] = custom_presets
    return merged


def iter_custom(data: dict):
    """Yield (key, preset) from the custom section if it exists."""
    for key, preset in data.get("_custom", {}).items():
        yield key, {**preset, "_key": key, "_product": "custom", "_category": "custom"}


def validate_schema(data: dict) -> tuple[bool, list[str]]:
    """
    Validate the full presets dict structure.
    Returns (is_valid, errors).
    Used by tests and the MCP validate tool.
    """
    errors = []

    if "common" not in data:
        errors.append("Missing top-level 'common' key.")

    for prod in VALID_PRODUCTS:
        if prod not in data:
            errors.append(f"Missing top-level '{prod}' key.")
            continue
        for sub in ("boot_cases", "content_cases", "fuse_collection"):
            if sub not in data[prod]:
                errors.append(f"Missing '{prod}.{sub}' key.")

    # Spot-check a few presets
    for key, preset in data.get("common", {}).items():
        errors.extend(_validate_preset_schema(key, preset))

    return len(errors) == 0, errors
