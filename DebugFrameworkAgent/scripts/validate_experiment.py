#!/usr/bin/env python3
"""
validate_experiment.py — Validate an experiment JSON or TPL file against framework rules.

Usage examples:
    python validate_experiment.py experiment.json
    python validate_experiment.py experiment.tpl
    python validate_experiment.py ./output/my_test.json
    python validate_experiment.py --json experiment.json

Accepted formats:
  .json — single experiment dict, list of dicts, or outer dict-of-dicts
  .tpl  — tab-separated PPV template (header row + one or more data rows)
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _core import experiment_builder


def parse_args():
    p = argparse.ArgumentParser(
        description="Validate an experiment JSON file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("file", metavar="FILE",
                   help="Path to experiment file (.json or .tpl).")
    p.add_argument("--json", action="store_true", dest="as_json",
                   help="Output results as JSON.")
    return p.parse_args()


def validate_one(exp: dict, idx: int | None = None) -> dict:
    label = exp.get("Test Name") or (f"Experiment[{idx}]" if idx is not None else "Experiment")
    ok, errors, warnings = experiment_builder.validate(exp)
    return {"name": label, "valid": ok, "errors": errors, "warnings": warnings}


def main():
    args = parse_args()
    path = pathlib.Path(args.file)

    # load_batch_from_file handles .json (all three structures) and .tpl transparently
    try:
        experiments = experiment_builder.load_batch_from_file(path)
    except FileNotFoundError:
        print(f"File not found: {path}")
        sys.exit(1)
    except ValueError as exc:
        print(f"Error loading file: {exc}")
        sys.exit(1)
    results = [validate_one(exp, i) for i, exp in enumerate(experiments)]

    if args.as_json:
        print(json.dumps(results, indent=2))
        sys.exit(0 if all(r["valid"] for r in results) else 1)

    all_ok = True
    for r in results:
        status = "PASS" if r["valid"] else "FAIL"
        print(f"\n[{status}] {r['name']}")
        for w in r["warnings"]:
            print(f"  WARN  {w}")
        for e in r["errors"]:
            print(f"  ERR   {e}")
            all_ok = False
        if r["valid"] and not r["warnings"]:
            print("  OK    No issues found.")

    total = len(results)
    passed = sum(1 for r in results if r["valid"])
    print(f"\nResult: {passed}/{total} experiments valid.")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
