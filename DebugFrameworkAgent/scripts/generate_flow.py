#!/usr/bin/env python3
"""
generate_flow.py — Generate automation flow files from an experiments JSON.

Usage examples:
    python generate_flow.py --experiments ./exp.json --out ./flow_output/
    python generate_flow.py --experiments exps.json --unit-ip 192.168.0.2 --unit-com 11
    python generate_flow.py --help
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _core import flow_builder, exporter


_DEFAULT_NODE_TYPES = {
    "boot": flow_builder.NODE_BOOT,
    "test": flow_builder.NODE_TEST,
    "gate": flow_builder.NODE_GATE,
}


def parse_args():
    p = argparse.ArgumentParser(
        description="Generate TestStructure.json, TestFlows.json, unit_config.ini, positions.json.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--experiments", metavar="FILE", required=True,
                   help="Path to experiments JSON (list of experiment dicts).")
    p.add_argument("--out", metavar="DIR", default="./flow_output",
                   help="Output directory (default: ./flow_output).")
    p.add_argument("--unit-ip",  metavar="IP",   help="DUT IP address for unit_config.ini.")
    p.add_argument("--unit-com", metavar="PORT", type=int, help="DUT COM port.")
    p.add_argument("--unit-product", metavar="PROD", help="Product name (GNR/CWF/DMR).")
    p.add_argument("--no-boot-node", action="store_true",
                   help="Skip the auto-prepended Boot node.")
    return p.parse_args()


def main():
    args = parse_args()

    exp_file = pathlib.Path(args.experiments)
    if not exp_file.exists():
        print(f"File not found: {exp_file}")
        sys.exit(1)

    with open(exp_file, encoding="utf-8") as fh:
        experiments_raw = json.load(fh)

    if isinstance(experiments_raw, dict):
        experiments_raw = [experiments_raw]

    # Build nodes list: one node per experiment + optional Boot + EndPass/EndFail
    nodes: list[dict] = []

    if not args.no_boot_node:
        nodes.append({"name": "Boot", "type": flow_builder.NODE_BOOT})

    for i, exp in enumerate(experiments_raw):
        tname = exp.get("Test Name") or f"Test_{i+1}"
        nodes.append({"name": tname, "type": flow_builder.NODE_TEST})

    nodes.append({"name": "End_PASS", "type": flow_builder.NODE_END_PASS})
    nodes.append({"name": "End_FAIL", "type": flow_builder.NODE_END_FAIL})

    # Wire last Test node to both End nodes
    if len(nodes) >= 3:
        last_test_idx = next(
            (len(nodes) - 3 - i for i, n in enumerate(reversed(nodes[:-2]))
             if n["type"] == flow_builder.NODE_TEST),
            None,
        )
        if last_test_idx is not None:
            nodes[last_test_idx]["on_pass"] = "End_PASS"
            nodes[last_test_idx]["on_fail"] = "End_FAIL"

    # Build experiment bindings: each test node gets one experiment
    exp_bindings: dict[str, list[dict]] = {}
    test_nodes = [n for n in nodes if n["type"] == flow_builder.NODE_TEST]
    for nd, exp in zip(test_nodes, experiments_raw):
        exp_bindings[nd["name"]] = [exp]

    unit_config = {
        "ip_address": args.unit_ip,
        "com_port":   args.unit_com,
        "product":    args.unit_product,
    }

    artefacts = flow_builder.build_all(nodes, exp_bindings, unit_config)

    written = exporter.write_flow_files(
        structure=artefacts["structure"],
        flows=artefacts["flows"],
        ini_text=artefacts["ini"],
        positions=artefacts["positions"],
        out_dir=pathlib.Path(args.out),
    )

    print(f"Flow files written to: {pathlib.Path(args.out).resolve()}")
    for label, path in written.items():
        print(f"  {label:<12} {path.name}")


if __name__ == "__main__":
    main()
