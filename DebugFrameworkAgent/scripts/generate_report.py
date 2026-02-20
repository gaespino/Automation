#!/usr/bin/env python3
"""
generate_report.py — Generate a human-readable Markdown / HTML / PDF report
from an existing experiment JSON or TPL file.

Usage:
    python generate_report.py experiment.json
    python generate_report.py experiments.tpl
    python generate_report.py experiment.json --format md
    python generate_report.py experiment.json --format html
    python generate_report.py experiment.json --format pdf         # requires fpdf2
    python generate_report.py experiment.json --format md html pdf
    python generate_report.py experiment.json --out ./reports/
    python generate_report.py experiment.json --product GNR

Accepted input formats:
  .json — single experiment dict, list of dicts, or outer dict-of-dicts
  .tpl  — tab-separated PPV template (header row + one or more data rows)

The .tpl format is equivalent to the .json format for report purposes.
If a .tpl is provided, reports are generated from the template values.

Reports are written alongside the input file unless --out is specified.
Filenames:  <stem>_report.md  /  <stem>_report.html  /  <stem>_report.pdf
"""
from __future__ import annotations
import argparse
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
    p.add_argument("experiment", metavar="EXPERIMENT_FILE",
                   help="Path to the experiment file (.json or .tpl).")
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

    # Load experiments from .json or .tpl — normalises all formats into a list
    try:
        experiments = experiment_builder.load_batch_from_file(exp_path)
    except FileNotFoundError:
        print(f"Error: file not found: {exp_path}")
        sys.exit(1)
    except ValueError as exc:
        print(f"Error: could not load experiment file: {exc}")
        sys.exit(1)

    # Determine output directory
    out_dir = pathlib.Path(args.out).resolve() if args.out else exp_path.parent

    is_batch = len(experiments) != 1

    product = args.product or (experiments[0].get("Product Chop") if experiments else None)

    # Optionally validate
    validation_result = None
    if args.validate:
        if is_batch:
            all_ok, all_errors, all_warnings, disabled = experiment_builder.validate_batch(
                experiments, product=product
            )
            status = "PASS" if all_ok else "FAIL"
            print(f"Validation: {status} ({len(all_errors)} errors, {len(all_warnings)} warnings)")
            if disabled:
                print(f"  Disabled experiments (skipped): {', '.join(disabled)}")
            # Surface individual issues
            for i, exp in enumerate(experiments):
                ok, errs, warns = experiment_builder.validate(exp, product=product)
                label = exp.get("Test Name", f"exp[{i}]")
                for e in errs:
                    print(f"  ERR  [{label}] {e}")
                for w in warns:
                    if not w.startswith("EXPERIMENT_DISABLED:"):
                        print(f"  WARN [{label}] {w}")
            # Provide a combined tuple for the report banner
            validation_result = (all_ok, all_errors, all_warnings)
        else:
            ok, errors, warnings = experiment_builder.validate(experiments[0])
            validation_result = (ok, errors, warnings)
            status = "PASS" if ok else "FAIL"
            print(f"Validation: {status} ({len(errors)} errors, {len(warnings)} warnings)")

    # Generate reports
    try:
        if is_batch:
            written = exporter.write_batch_report(
                experiments,
                out_dir,
                name=exp_path.stem,
                formats=tuple(f for f in args.formats if f != "pdf"),
                product=product,
                batch_name=exp_path.stem,
            )
        else:
            written = exporter.write_report(
                experiments[0],
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
