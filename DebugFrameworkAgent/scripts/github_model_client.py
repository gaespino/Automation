#!/usr/bin/env python3
"""
github_model_client.py — GitHub Models API client for DebugFrameworkAgent.

Sends requests to the GitHub Models inference endpoint using stdlib only
(urllib + json) — no external packages required.

Usage examples:
    # Ask a one-shot question
    python github_model_client.py --message "What Test Mode should I use for a mesh run?"

    # Use an agent file for system context
    python github_model_client.py --agent experiment \\
        --message "Generate a GNR Dragon experiment with 100 loops"

    # Translate plain English to field overrides
    python github_model_client.py --translate \\
        --product GNR \\
        --message "dragon content with ULX Path set to FS1 and 50 loops"

    # List available models
    python github_model_client.py --list-models

Environment:
    GITHUB_TOKEN   — Personal Access Token or Actions GITHUB_TOKEN (required)
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_MODELS_URL = "https://models.inference.ai.azure.com/chat/completions"
GITHUB_MODELS_LIST_URL = "https://models.inference.ai.azure.com/models"
DEFAULT_MODEL = "gpt-4o-mini"

_SCRIPTS_DIR = pathlib.Path(__file__).parent
_AGENT_ROOT  = _SCRIPTS_DIR.parent  # DebugFrameworkAgent/

# ---------------------------------------------------------------------------
# Helper: file loaders
# ---------------------------------------------------------------------------

def load_agent_file(name: str) -> str:
    """
    Load an .agent.md file by short name (e.g. "experiment" or "orchestrator").

    Searches DebugFrameworkAgent/agents/<name>.agent.md
    Returns the file text, or empty string if not found.
    """
    candidates = [
        _AGENT_ROOT / "agents" / f"{name}.agent.md",
        _AGENT_ROOT / "agents" / f"{name}.md",
    ]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")
    return ""


def load_skill_file(name: str) -> str:
    """
    Load a .skill.md file by short name (e.g. "experiment_constraints").

    Searches DebugFrameworkAgent/skills/<name>.skill.md
    Returns the file text, or empty string if not found.
    """
    candidates = [
        _AGENT_ROOT / "skills" / f"{name}.skill.md",
        _AGENT_ROOT / "skills" / f"{name}.md",
    ]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")
    return ""


def load_prompt_file(name: str) -> str:
    """
    Load a .prompt.md file by short name (e.g. "content_dragon").

    Searches DebugFrameworkAgent/prompts/<name>.prompt.md
    Returns the file text, or empty string if not found.
    """
    candidates = [
        _AGENT_ROOT / "prompts" / f"{name}.prompt.md",
        _AGENT_ROOT / "prompts" / f"{name}.md",
    ]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")
    return ""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class GitHubModelClient:
    """
    Minimal GitHub Models API client — stdlib only.

    Args:
        token:   GitHub PAT / Actions token. Defaults to GITHUB_TOKEN env var.
        model:   Model ID string (default: gpt-4o-mini).
        timeout: HTTP timeout in seconds (default: 60).
    """

    def __init__(
        self,
        token:   str | None = None,
        model:   str = DEFAULT_MODEL,
        timeout: int = 60,
    ) -> None:
        self.token   = token or os.environ.get("GITHUB_TOKEN", "")
        self.model   = model
        self.timeout = timeout

        if not self.token:
            raise ValueError(
                "GITHUB_TOKEN is not set. "
                "Export the variable or pass token= explicitly."
            )

    # ------------------------------------------------------------------
    # Core request
    # ------------------------------------------------------------------

    def _post(self, url: str, payload: dict) -> dict:
        """POST *payload* as JSON, return parsed response dict."""
        body = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type":  "application/json",
                "Accept":        "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GitHub Models API error {exc.code}: {body_text}"
            ) from exc

    def _get(self, url: str) -> Any:
        """GET *url*, return parsed response."""
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept":        "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GitHub Models API error {exc.code}: {body_text}"
            ) from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ask(
        self,
        user_message:  str,
        system_prompt: str | None = None,
        history:       list[dict] | None = None,
        temperature:   float = 0.2,
        max_tokens:    int   = 2048,
    ) -> str:
        """
        Send a chat completion request and return the assistant reply as a string.

        Args:
            user_message:  The user turn text.
            system_prompt: Optional system prompt prepended to the conversation.
            history:       Optional list of prior {role, content} messages.
            temperature:   Sampling temperature (default 0.2 for determinism).
            max_tokens:    Maximum tokens in the response.

        Returns:
            The assistant's text reply.
        """
        messages: list[dict] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        payload = {
            "model":       self.model,
            "messages":    messages,
            "temperature": temperature,
            "max_tokens":  max_tokens,
        }

        data = self._post(GITHUB_MODELS_URL, payload)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected response structure: {data}") from exc

    def ask_with_agent_context(
        self,
        user_message: str,
        agent:        str = "experiment",
        extra_skills: list[str] | None = None,
        **kwargs,
    ) -> str:
        """
        Ask a question with the agent's .md files loaded as system context.

        The system prompt is built from:
          1. The agent file  (agents/<agent>.agent.md)
          2. Any extra skill files  (skills/<name>.skill.md for each name in extra_skills)

        Args:
            user_message: The user question / request.
            agent:        Short agent name (default "experiment").
            extra_skills: List of skill short names to include (e.g. ["experiment_constraints"]).
            **kwargs:     Forwarded to :meth:`ask` (temperature, max_tokens, history).

        Returns:
            The assistant's text reply.
        """
        parts: list[str] = []

        agent_text = load_agent_file(agent)
        if agent_text:
            parts.append(f"## Agent: {agent}\n\n{agent_text}")

        for skill_name in (extra_skills or []):
            skill_text = load_skill_file(skill_name)
            if skill_text:
                parts.append(f"## Skill: {skill_name}\n\n{skill_text}")

        system_prompt = "\n\n---\n\n".join(parts) if parts else None

        return self.ask(user_message, system_prompt=system_prompt, **kwargs)

    def translate_to_overrides(
        self,
        user_description: str,
        product:          str = "GNR",
    ) -> dict[str, Any]:
        """
        Convert a plain-English experiment description into a field-override dict.

        The model is asked to return valid JSON representing {field: value} pairs
        that can be passed directly to experiment_builder.update_fields().

        Args:
            user_description: Natural-language description of the desired changes.
            product:          Target product (GNR / CWF / DMR).

        Returns:
            Dict of {field_name: value} ready for update_fields().
            Returns an empty dict if the model returns no parseable JSON.
        """
        system = (
            "You are a Debug Framework experiment configuration assistant.\n"
            f"The target product is {product}.\n"
            "The user will describe what they want in plain English.\n"
            "You must respond with ONLY a valid JSON object mapping experiment field "
            "names (exactly as they appear in the experiment schema) to their new values.\n"
            "Do NOT include any explanation, markdown fences, or extra text — just the JSON.\n\n"
            "Common field names: Test Name, Test Mode, Test Type, Content, Loops, "
            "Dragon ULX Path, Dragon Content Path, Dragon Content Line, "
            "Linux Path, Voltage Type, IA Voltage Bump, CFC Voltage Bump, "
            "Start, End, Steps, Domain, Type, TTL Folder, IP Address, Check Core."
        )

        raw = self.ask(user_description, system_prompt=system, temperature=0.1)

        # Strip optional markdown code fences if the model wrapped them
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw   = "\n".join(
                ln for ln in lines if not ln.startswith("```")
            ).strip()

        try:
            result = json.loads(raw)
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, ValueError):
            pass

        return {}

    # ------------------------------------------------------------------
    # Model listing
    # ------------------------------------------------------------------

    def list_models(self) -> list[dict]:
        """
        Return a list of available model dicts from the GitHub Models catalog.

        Each entry typically contains: id, name, description, publisher, …
        """
        data = self._get(GITHUB_MODELS_LIST_URL)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("models", data.get("data", []))
        return []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(
        description="Query GitHub Models on behalf of DebugFrameworkAgent.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--message", "-m", metavar="TEXT",
                   help="User message to send to the model.")
    p.add_argument("--agent", metavar="NAME", default="experiment",
                   help="Agent file to load as system context (default: experiment).")
    p.add_argument("--skill", metavar="NAME", nargs="*",
                   help="Additional skill file(s) to include in system context.")
    p.add_argument("--prompt-file", metavar="NAME",
                   help="Load a prompt file and use it as the system prompt.")
    p.add_argument("--translate", action="store_true",
                   help="Translate --message to a field-override JSON dict.")
    p.add_argument("--product", default="GNR", choices=["GNR", "CWF", "DMR"],
                   help="Product context for --translate (default: GNR).")
    p.add_argument("--model", default=DEFAULT_MODEL,
                   help=f"Model to use (default: {DEFAULT_MODEL}).")
    p.add_argument("--list-models", action="store_true",
                   help="Print available GitHub Models and exit.")
    p.add_argument("--temperature", type=float, default=0.2,
                   help="Sampling temperature (default: 0.2).")
    p.add_argument("--max-tokens", type=int, default=2048,
                   help="Maximum tokens in the reply (default: 2048).")
    return p.parse_args()


def main():
    args = _parse_args()

    try:
        client = GitHubModelClient(model=args.model)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.list_models:
        models = client.list_models()
        if not models:
            print("No models returned.")
        for m in models:
            mid  = m.get("id") or m.get("name", "?")
            desc = m.get("description") or m.get("summary", "")
            print(f"  {mid:<40} {desc[:60]}")
        return

    if not args.message:
        print("Error: --message is required (unless using --list-models).", file=sys.stderr)
        sys.exit(1)

    if args.translate:
        result = client.translate_to_overrides(args.message, product=args.product)
        print(json.dumps(result, indent=2))
        return

    if args.prompt_file:
        sys_prompt = load_prompt_file(args.prompt_file)
        reply = client.ask(
            args.message,
            system_prompt=sys_prompt or None,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
    else:
        reply = client.ask_with_agent_context(
            args.message,
            agent=args.agent,
            extra_skills=args.skill,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )

    print(reply)


if __name__ == "__main__":
    main()
