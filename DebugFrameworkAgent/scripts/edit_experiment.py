#!/usr/bin/env python3
"""
edit_experiment.py — Load an existing experiment JSON and apply field changes.

Usage examples:
    python edit_experiment.py --file ./output/MyUnit/MyExp.json --set Loops=20
    python edit_experiment.py --file ./output/MyUnit/MyExp.json --set Loops=20 "TTL Folder=S:\\GNR\\RVP\\TTLs"
    python edit_experiment.py --file ./output/MyUnit/MyExp.json --set Voltage_IA=0.05 --out ./output/MyUnit/MyExp_v2.json
    python edit_experiment.py --file ./output/MyUnit/MyExp.json --show
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _core import experiment_builder, exporter


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Load an existing experiment JSON and apply field overrides.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--file", metavar="PATH", required=True,
                   help="Path to the existing experiment JSON file.")
    p.add_argument("--set", metavar="KEY=VALUE", nargs="*",
                   help="Field overrides to apply, e.g. --set Loops=20 'TTL Folder=S:\\RVP\\TTLs'")
    p.add_argument("--out", metavar="PATH",
                   help="Output path for the updated JSON (default: overwrite input file).")
    p.add_argument("--show", action="store_true",
                   help="Print the current field values and exit without saving.")
    p.add_argument("--report", action="store_true",
                   help="Also regenerate the Markdown + HTML report alongside the JSON.")
    p.add_argument("--product", default=None,
                   help="Product hint for validation (GNR / CWF / DMR).")
    return p.parse_args()


def _parse_overrides(raw: list[str] | None) -> dict:
    if not raw:
        return {}
    result: dict = {}
    for item in raw:
        if "=" not in item:
            print(f"Warning: ignoring override '{item}' — expected KEY=VALUE format.", file=sys.stderr)
            continue
        key, _, val = item.partition("=")
        # Try to coerce to int / float / bool before falling back to string
        for cast in (int, float):
            try:
                val = cast(val)
                break
            except ValueError:
                pass
        if isinstance(val, str):
            if val.lower() == "true":
                val = True
            elif val.lower() == "false":
                val = False
            elif val.lower() in ("null", "none", ""):
                val = None
        result[key.strip()] = val
    return result


def main() -> None:
    args = parse_args()

    # --- Load ----------------------------------------------------------
    try:
        exp = experiment_builder.load_from_file(args.file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    # --- Show ----------------------------------------------------------
    if args.show:
        print(json.dumps(exp, indent=2, ensure_ascii=False))
        return

    # --- Apply overrides -----------------------------------------------
    changes = _parse_overrides(args.set)
    if changes:
        exp = experiment_builder.update_fields(exp, changes)
        print(f"Applied {len(changes)} change(s): {', '.join(changes.keys())}")
    else:
        print("No --set overrides provided — nothing to change.", file=sys.stderr)
        sys.exit(0)

    # --- Validate -------------------------------------------------------
    ok, errors, warnings = experiment_builder.validate(exp, product=args.product)
    for e in errors:
        print(f"  ERROR:   {e}", file=sys.stderr)
    for w in warnings:
        print(f"  Warning: {w}")
    if not ok:
        print("Validation failed — fix errors before saving.", file=sys.stderr)
        sys.exit(1)

    # --- Save -----------------------------------------------------------
    out_path = pathlib.Path(args.out).resolve() if args.out else pathlib.Path(args.file).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(exp, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {out_path}")

    # --- Optional report regeneration -----------------------------------
    if args.report:
        written = exporter.write_report(exp, out_path.parent, name=out_path.stem, product=args.product)
        for fmt, rp in written.items():
            print(f"Report ({fmt}): {rp}")


if __name__ == "__main__":
    main()
