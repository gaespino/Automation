#!/usr/bin/env python3
"""
apply_preset.py — Apply an experiment preset, prompt for required fields, and export.

Usage examples:
    python apply_preset.py --preset gnr_baseline --name "My Test"
    python apply_preset.py --preset gnr_baseline --name "Boot Run" --out ./output/
    python apply_preset.py --preset dmr_dragon_base_h --product DMR --out ./dmr_exp.json
    python apply_preset.py --list   (print all available keys and exit)
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _core import preset_loader, experiment_builder, exporter


def parse_args():
    p = argparse.ArgumentParser(
        description="Apply an experiment preset and export to JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--preset", metavar="KEY",
                   help="Preset key to apply (e.g. gnr_baseline).")
    p.add_argument("--product", choices=["GNR", "CWF", "DMR"],
                   help="Product context for product-specific preset lookup.")
    p.add_argument("--name", metavar="NAME",
                   help="Override 'Test Name' in the output experiment.")
    p.add_argument("--out", metavar="PATH", default=".",
                   help="Output directory or file path (default: current dir).")
    p.add_argument("--set", metavar="KEY=VALUE", nargs="*",
                   help="Additional field overrides, e.g. --set Loops=10 Reset=False")
    p.add_argument("--list", action="store_true", dest="list_only",
                   help="List all preset keys and exit.")
    p.add_argument("--presets-file", metavar="PATH",
                   help="Override default experiment_presets.json location.")
    p.add_argument("--no-report", action="store_true",
                   help="Skip report generation after export.")
    p.add_argument("--report-format", metavar="FMT", nargs="+",
                   choices=["md", "html", "pdf"], default=["md", "html"],
                   help="Report formats to generate (default: md html).")
    return p.parse_args()


def _parse_overrides(raw: list[str] | None) -> dict:
    if not raw:
        return {}
    result = {}
    for item in raw:
        if "=" not in item:
            print(f"Warning: skipping override '{item}' (no '=' found)")
            continue
        k, _, v = item.partition("=")
        # Best-effort type coercion
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass
        result[k.strip()] = v
    return result


def main():
    args = parse_args()

    custom_path = pathlib.Path(args.presets_file) if args.presets_file else None
    data = preset_loader.load_all(custom_path)

    if args.list_only:
        presets = preset_loader.filter_by_product(data, product=args.product or "all")
        for pr in presets:
            print(f"{pr['_key']:<40}  {pr.get('description', '')}")
        return

    if not args.preset:
        print("Error: --preset KEY is required. Use --list to see available keys.")
        sys.exit(1)

    try:
        preset = preset_loader.get_preset(data, args.preset, product=args.product)
    except KeyError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    overrides = _parse_overrides(args.set)
    if args.name:
        overrides["Test Name"] = args.name

    exp = experiment_builder.apply_preset(preset, overrides)

    # Validate before export
    ok, errors, warnings = experiment_builder.validate(exp)
    for w in warnings:
        print(f"Warning: {w}")
    if not ok:
        print("Validation errors (experiment NOT exported):")
        for e in errors:
            print(f"  ERROR: {e}")
        sys.exit(1)

    out = pathlib.Path(args.out)
    if out.suffix.lower() == ".json":
        out_path = exporter.write_experiment_json(exp, out.parent, out.stem)
    else:
        out_path = exporter.write_experiment_json(exp, out)

    print(f"Exported: {out_path}")

    if not args.no_report:
        product = args.product
        report_dir = out_path.parent
        try:
            written = exporter.write_report(
                exp,
                report_dir,
                name=out_path.stem,
                formats=tuple(args.report_format),
                validation_result=(ok, errors, warnings),
                product=product,
            )
            for fmt, rpath in written.items():
                print(f"Report ({fmt.upper()}): {rpath}")
        except ImportError as exc:
            print(f"Note: {exc}")


if __name__ == "__main__":
    main()
