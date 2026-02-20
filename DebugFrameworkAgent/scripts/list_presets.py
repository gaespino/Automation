#!/usr/bin/env python3
"""
list_presets.py — List available experiment presets.

Usage examples:
    python list_presets.py
    python list_presets.py --product GNR
    python list_presets.py --product CWF --category content
    python list_presets.py --product DMR --json
"""
from __future__ import annotations
import argparse
import json
import sys
import pathlib

# Allow running directly OR as part of the package
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _core import preset_loader


def parse_args():
    p = argparse.ArgumentParser(
        description="List available experiment presets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--product",  choices=["GNR", "CWF", "DMR"],
                   help="Filter by product (default: show common + all products).")
    p.add_argument("--category", default="all",
                   help="Filter by category (boot, content, test, fuse, common). Default: all.")
    p.add_argument("--json", action="store_true", dest="as_json",
                   help="Output as JSON array.")
    p.add_argument("--presets-file", metavar="PATH",
                   help="Override default experiment_presets.json location.")
    return p.parse_args()


def main():
    args = parse_args()

    custom_path = pathlib.Path(args.presets_file) if args.presets_file else None
    data = preset_loader.load_all(custom_path)

    presets = preset_loader.filter_by_product(
        data,
        product=args.product or "all",
        category=args.category,
    )

    if args.as_json:
        print(json.dumps(presets, indent=2))
        return

    if not presets:
        print("No presets found for the given filters.")
        return

    # Group by category for pretty output
    by_cat: dict[str, list] = {}
    for pr in presets:
        cat = pr.get("_category", "unknown")
        by_cat.setdefault(cat, []).append(pr)

    for cat, items in by_cat.items():
        print(f"\n[{cat.upper()}]  ({len(items)} preset{'s' if len(items) != 1 else ''})")
        for pr in items:
            key  = pr.get("_key", "?")
            desc = pr.get("description", "")
            prod = pr.get("_product", "common")
            flag = f"[{prod}]" if prod != "common" else "[all]"
            print(f"  {flag}  {key:<40}  {desc}")

    print(f"\nTotal: {len(presets)} presets")


if __name__ == "__main__":
    main()
