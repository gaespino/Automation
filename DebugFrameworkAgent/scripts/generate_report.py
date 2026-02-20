#!/usr/bin/env python3
"""
generate_report.py — Generate a human-readable Markdown / HTML / PDF report
from an existing experiment JSON file.

Usage:
    python generate_report.py experiment.json
    python generate_report.py experiment.json --format md
    python generate_report.py experiment.json --format html
    python generate_report.py experiment.json --format pdf         # requires fpdf2
    python generate_report.py experiment.json --format md html pdf
    python generate_report.py experiment.json --out ./reports/
    python generate_report.py experiment.json --product GNR

Reports are written alongside the input file unless --out is specified.
Filenames:  <stem>_report.md  /  <stem>_report.html  /  <stem>_report.pdf
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _core import exporter, experiment_builder


def parse_args():
    p = argparse.ArgumentParser(
        description="Generate a report for an existing experiment JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("experiment", metavar="EXPERIMENT_JSON",
                   help="Path to the experiment .json file.")
    p.add_argument("--format", metavar="FMT", nargs="+",
                   choices=["md", "html", "pdf"], default=["md", "html"],
                   dest="formats",
                   help="Output format(s). Choices: md html pdf. Default: md html.")
    p.add_argument("--out", metavar="DIR",
                   help="Output directory (default: same folder as input file).")
    p.add_argument("--product", metavar="PRODUCT",
                   help="Product label to show in the report (e.g. GNR, CWF, DMR).")
    p.add_argument("--validate", action="store_true",
                   help="Run experiment validation and include results in report.")
    return p.parse_args()


def main():
    args = parse_args()

    exp_path = pathlib.Path(args.experiment).resolve()
    if not exp_path.exists():
        print(f"Error: file not found: {exp_path}")
        sys.exit(1)

    try:
        with open(exp_path, encoding="utf-8") as fh:
            experiment = json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"Error: could not parse JSON: {exc}")
        sys.exit(1)

    if not isinstance(experiment, dict):
        print("Error: experiment file must contain a JSON object (dict), not a list.")
        sys.exit(1)

    # Determine output directory
    out_dir = pathlib.Path(args.out).resolve() if args.out else exp_path.parent

    # Optionally validate
    validation_result = None
    if args.validate:
        ok, errors, warnings = experiment_builder.validate(experiment)
        validation_result = (ok, errors, warnings)
        status = "PASS" if ok else "FAIL"
        print(f"Validation: {status} ({len(errors)} errors, {len(warnings)} warnings)")

    product = args.product or experiment.get("Product Chop")

    # Generate reports
    try:
        written = exporter.write_report(
            experiment,
            out_dir,
            name=exp_path.stem,
            formats=tuple(args.formats),
            validation_result=validation_result,
            product=product,
        )
    except ImportError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    for fmt, path in written.items():
        print(f"[{fmt.upper()}] {path}")

    print("Done.")


if __name__ == "__main__":
    main()
