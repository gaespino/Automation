"""
flow_builder.py — Build automation flow structures for PPV/automation export.

Generates the four file formats used by the automation framework:
  - TestStructure.json    (node/connection graph)
  - TestFlows.json        (per-node experiment bindings)
  - unit_config.ini       (DUT connection settings)
  - positions.json        (optional layout hints)

See automation_flow_designer.skill.md for full format specs.
No external dependencies.
"""

from __future__ import annotations
import copy
import json
from typing import Any

# --------------------------------------------------------------------------
# Node type constants
# --------------------------------------------------------------------------
NODE_BOOT      = "Boot"
NODE_TEST      = "Test"
NODE_GATE      = "Gate"
NODE_END_PASS  = "EndPass"
NODE_END_FAIL  = "EndFail"
NODE_END_ABORT = "EndAbort"

TERMINAL_NODES = {NODE_END_PASS, NODE_END_FAIL, NODE_END_ABORT}

# --------------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------------

def _node_id(idx: int) -> str:
    return f"node_{idx:03d}"


def _connection(src: str, dst: str, label: str = "PASS") -> dict:
    return {"from": src, "to": dst, "on": label}


def _test_node(node_id: str, name: str, node_type: str = NODE_TEST) -> dict:
    return {
        "id":    node_id,
        "name":  name,
        "type":  node_type,
    }


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def build_structure(nodes: list[dict]) -> dict:
    """
    Build a TestStructure object from a list of node descriptors.

    Each node dict should have at minimum:
      - name (str): human-readable label
      - type (str): Boot | Test | Gate | EndPass | EndFail | EndAbort
      - on_pass (str, optional): name of destination node on PASS
      - on_fail (str, optional): name of destination node on FAIL

    A default linear chain is generated when on_pass/on_fail are omitted.

    Returns a dict suitable for JSON serialisation as TestStructure.json.
    """
    if not nodes:
        return {"nodes": [], "connections": []}

    built_nodes:    list[dict] = []
    connections:    list[dict] = []
    name_to_id:     dict[str, str] = {}

    for i, nd in enumerate(nodes):
        nid  = _node_id(i)
        name = nd.get("name", f"Node_{i}")
        ntype = nd.get("type", NODE_TEST)
        built_nodes.append(_test_node(nid, name, ntype))
        name_to_id[name] = nid

    for i, nd in enumerate(nodes):
        src_id = _node_id(i)
        ntype  = nd.get("type", NODE_TEST)

        if ntype in TERMINAL_NODES:
            continue

        # Explicit wiring
        if "on_pass" in nd:
            dst = name_to_id.get(nd["on_pass"])
            if dst:
                connections.append(_connection(src_id, dst, "PASS"))
        elif i + 1 < len(nodes):
            connections.append(_connection(src_id, _node_id(i + 1), "PASS"))

        if "on_fail" in nd:
            dst = name_to_id.get(nd["on_fail"])
            if dst:
                connections.append(_connection(src_id, dst, "FAIL"))

    return {"nodes": built_nodes, "connections": connections}


def build_flows(
    nodes: list[dict],
    experiments: dict[str, list[dict]],
) -> dict:
    """
    Build a TestFlows binding object.

    Args:
        nodes:       Same list used for build_structure.
        experiments: Mapping of node_name → [experiment_dict, ...].
                     Experiments are taken verbatim; no deep validation.

    Returns a dict where each key is the node id and value is payload:
        {"node_id": {"experiments": [...], "mode": "sequential"}}
    """
    name_to_id = {nd.get("name", f"Node_{i}"): _node_id(i) for i, nd in enumerate(nodes)}

    result: dict[str, Any] = {}
    for node_name, exps in experiments.items():
        nid = name_to_id.get(node_name)
        if nid is None:
            continue
        result[nid] = {
            "node":        node_name,
            "experiments": list(exps),
            "mode":        "sequential",
        }
    return result


def build_ini(unit_config: dict) -> str:
    """
    Build a unit_config.ini string from a config dict.

    Expected keys (all optional — omitted keys use blank defaults):
        com_port, ip_address, socket_type, product, lot, wafer, xy,
        dut_type, setup_name, operator

    Returns a multi-line INI string (no file I/O).
    """
    sections: list[str] = []

    def _add_section(header: str, pairs: list[tuple[str, Any]]) -> None:
        lines = [f"[{header}]"]
        for key, val in pairs:
            if val is not None:
                lines.append(f"{key} = {val}")
        sections.append("\n".join(lines))

    _add_section("Connection", [
        ("COMPort",    unit_config.get("com_port")),
        ("IPAddress",  unit_config.get("ip_address")),
        ("SocketType", unit_config.get("socket_type")),
    ])

    _add_section("DUT", [
        ("Product",   unit_config.get("product")),
        ("Lot",       unit_config.get("lot")),
        ("Wafer",     unit_config.get("wafer")),
        ("XY",        unit_config.get("xy")),
        ("DUTType",   unit_config.get("dut_type", "Unknown")),
    ])

    _add_section("Setup", [
        ("SetupName", unit_config.get("setup_name")),
        ("Operator",  unit_config.get("operator")),
    ])

    return "\n\n".join(sections) + "\n"


def build_positions(nodes: list[dict], default_x_step: int = 200) -> dict:
    """
    Build an optional positions/layout dict for UI rendering.

    Generates a simple left-to-right layout unless x/y are provided
    in each node descriptor.

    Returns a dict keyed by node_id → {"x": int, "y": int}.
    """
    result: dict[str, dict] = {}
    for i, nd in enumerate(nodes):
        nid = _node_id(i)
        result[nid] = {
            "x": nd.get("x", i * default_x_step),
            "y": nd.get("y", 0),
        }
    return result


def build_all(
    nodes: list[dict],
    experiments: dict[str, list[dict]],
    unit_config: dict | None = None,
) -> dict[str, Any]:
    """
    Convenience wrapper — build all four artefacts in one call.

    Returns:
        {
          "structure":  <TestStructure dict>,
          "flows":      <TestFlows dict>,
          "ini":        <unit_config.ini string>,
          "positions":  <positions dict>,
        }
    """
    return {
        "structure": build_structure(nodes),
        "flows":     build_flows(nodes, experiments),
        "ini":       build_ini(unit_config or {}),
        "positions": build_positions(nodes),
    }
