#!/usr/bin/env python3
"""
mcp_server.py — Local MCP server exposing Debug Framework tools to GitHub Copilot Agent Mode.

Phase 2 optional — requires: pip install "mcp[cli]>=1.0"

Run via VS Code task or:
    python mcp_server.py

Then add to .vscode/mcp.json
"""
from __future__ import annotations
import json
import pathlib
import sys

# Guard: graceful failure if mcp is not installed
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _core import preset_loader, experiment_builder, exporter, flow_builder

# --------------------------------------------------------------------------
# Tool registry
# --------------------------------------------------------------------------

def _load_data():
    return preset_loader.load_all()


def tool_list_presets(product: str = "all", category: str = "all") -> str:
    """List available presets, optionally filtered by product and category."""
    data = _load_data()
    presets = preset_loader.filter_by_product(data, product=product, category=category)
    rows = [
        {"key": p["_key"], "product": p["_product"], "category": p["_category"],
         "description": p.get("description", "")}
        for p in presets
    ]
    return json.dumps(rows, indent=2)


def tool_get_preset(key: str, product: str | None = None) -> str:
    """Return the full preset dict for a given key."""
    data = _load_data()
    try:
        preset = preset_loader.get_preset(data, key, product=product)
        return json.dumps(preset, indent=2)
    except KeyError as exc:
        return json.dumps({"error": str(exc)})


def tool_generate_experiment(
    product:    str,
    mode:       str = "mesh",
    preset_key: str | None = None,
    test_name:  str | None = None,
    overrides:  dict | None = None,
) -> str:
    """
    Generate an experiment dict.
    If preset_key is provided, start from that preset; otherwise blank.
    Returns validated experiment JSON string.
    """
    if preset_key:
        data = _load_data()
        try:
            preset = preset_loader.get_preset(data, preset_key, product=product)
        except KeyError as exc:
            return json.dumps({"error": str(exc)})
        exp = experiment_builder.apply_preset(preset, overrides or {})
    else:
        exp = experiment_builder.new_blank(product, mode)
        for k, v in (overrides or {}).items():
            exp[k] = v

    if test_name:
        exp["Test Name"] = test_name

    ok, errors, warnings = experiment_builder.validate(exp)
    return json.dumps({
        "experiment": exp,
        "valid":     ok,
        "errors":    errors,
        "warnings":  warnings,
    }, indent=2)


def tool_validate_experiment(experiment: dict) -> str:
    """Validate a single experiment dict and return errors/warnings."""
    ok, errors, warnings = experiment_builder.validate(experiment)
    return json.dumps({"valid": ok, "errors": errors, "warnings": warnings}, indent=2)


def tool_get_product_defaults(product: str) -> str:
    """Return the product-specific field defaults for a product."""
    try:
        return json.dumps(experiment_builder.get_product_defaults(product), indent=2)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})


# --------------------------------------------------------------------------
# MCP server bootstrap
# --------------------------------------------------------------------------

def _run_server():
    server = Server("debug-framework-agent")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="list_presets",
                description="List available experiment presets.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "product":  {"type": "string", "enum": ["GNR", "CWF", "DMR", "all"]},
                        "category": {"type": "string"},
                    },
                },
            ),
            types.Tool(
                name="get_preset",
                description="Get a single preset by key.",
                inputSchema={
                    "type": "object",
                    "required": ["key"],
                    "properties": {
                        "key":     {"type": "string"},
                        "product": {"type": "string"},
                    },
                },
            ),
            types.Tool(
                name="generate_experiment",
                description="Generate a new experiment from a preset or blank template.",
                inputSchema={
                    "type": "object",
                    "required": ["product"],
                    "properties": {
                        "product":    {"type": "string"},
                        "mode":       {"type": "string"},
                        "preset_key": {"type": "string"},
                        "test_name":  {"type": "string"},
                        "overrides":  {"type": "object"},
                    },
                },
            ),
            types.Tool(
                name="validate_experiment",
                description="Validate an experiment dict.",
                inputSchema={
                    "type": "object",
                    "required": ["experiment"],
                    "properties": {"experiment": {"type": "object"}},
                },
            ),
            types.Tool(
                name="get_product_defaults",
                description="Get product-specific field defaults.",
                inputSchema={
                    "type": "object",
                    "required": ["product"],
                    "properties": {"product": {"type": "string"}},
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name == "list_presets":
            result = tool_list_presets(**arguments)
        elif name == "get_preset":
            result = tool_get_preset(**arguments)
        elif name == "generate_experiment":
            result = tool_generate_experiment(**arguments)
        elif name == "validate_experiment":
            result = tool_validate_experiment(**arguments)
        elif name == "get_product_defaults":
            result = tool_get_product_defaults(**arguments)
        else:
            result = json.dumps({"error": f"Unknown tool: {name}"})
        return [types.TextContent(type="text", text=result)]

    import asyncio
    asyncio.run(stdio_server(server))


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

if __name__ == "__main__":
    if not MCP_AVAILABLE:
        print(
            "ERROR: mcp package not installed.\n"
            "Install it with:  pip install \"mcp[cli]>=1.0\"\n"
            "See DebugFrameworkAgent/docs/SETUP.md for details.",
            file=sys.stderr,
        )
        sys.exit(1)
    _run_server()
