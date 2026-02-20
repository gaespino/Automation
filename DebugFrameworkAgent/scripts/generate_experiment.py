#!/usr/bin/env python3
"""
generate_experiment.py — Generate a new experiment from a preset or blank template.

Usage examples:
    python generate_experiment.py --product GNR --preset gnr_baseline --out ./exp.json
    python generate_experiment.py --product CWF --mode mesh --name "CWF Mesh Run"
    python generate_experiment.py --product DMR --preset dmr_dragon_base_h --set Loops=10
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
        description="Generate a new experiment JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--product", choices=["GNR", "CWF", "DMR"], required=True,
                   help="Target product.")
    p.add_argument("--preset", metavar="KEY",
                   help="Optional preset key to start from.")
    p.add_argument("--mode", default="mesh",
                   choices=["mesh", "slice", "boot", "linux"],
                   help="Test mode for blank experiments (default: mesh).")
    p.add_argument("--name", metavar="NAME",
                   help="Test name for the generated experiment.")
    p.add_argument("--out", metavar="PATH", default=".",
                   help="Output directory or .json file path.")
    p.add_argument("--set", metavar="KEY=VALUE", nargs="*",
                   help="Additional field overrides, e.g. --set Loops=10.")
    p.add_argument("--presets-file", metavar="PATH",
                   help="Override default experiment_presets.json location.")
    p.add_argument("--no-validate", action="store_true",
                   help="Skip validation before export.")
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
            continue
        k, _, v = item.partition("=")
        if v.lower() == "true":   v = True
        elif v.lower() == "false": v = False
        else:
            try:   v = int(v)
            except ValueError:
                try: v = float(v)
                except ValueError: pass
        result[k.strip()] = v
    return result


def main():
    args = parse_args()
    overrides = _parse_overrides(args.set)
    if args.name:
        overrides["Test Name"] = args.name

    if args.preset:
        custom_path = pathlib.Path(args.presets_file) if args.presets_file else None
        data = preset_loader.load_all(custom_path)
        try:
            preset = preset_loader.get_preset(data, args.preset, product=args.product)
        except KeyError as exc:
            print(f"Error: {exc}")
            sys.exit(1)
        exp = experiment_builder.apply_preset(preset, overrides)
    else:
        exp = experiment_builder.new_blank(args.product, args.mode)
        for k, v in overrides.items():
            exp[k] = v

    if not args.no_validate:
        ok, errors, warnings = experiment_builder.validate(exp)
        for w in warnings:
            print(f"Warning: {w}")
        if not ok:
            print("Validation failed — experiment NOT exported:")
            for e in errors:
                print(f"  ERROR: {e}")
            sys.exit(1)
        validation_result = (ok, errors, warnings)
    else:
        validation_result = None

    out = pathlib.Path(args.out)
    if out.suffix.lower() == ".json":
        out_path = exporter.write_experiment_json(exp, out.parent, out.stem)
    else:
        out_path = exporter.write_experiment_json(exp, out)

    print(f"Generated: {out_path}")

    if not args.no_report:
        product = args.product
        report_dir = out_path.parent
        try:
            written = exporter.write_report(
                exp,
                report_dir,
                name=out_path.stem,
                formats=tuple(args.report_format),
                validation_result=validation_result,
                product=product,
            )
            for fmt, rpath in written.items():
                print(f"Report ({fmt.upper()}): {rpath}")
        except ImportError as exc:
            print(f"Note: {exc}")


if __name__ == "__main__":
    main()
