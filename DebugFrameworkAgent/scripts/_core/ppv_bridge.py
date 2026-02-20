"""
ppv_bridge.py — Optional read-only bridge to PPV's live field configurations.

When PPV is found on the host machine the bridge reads its JSON config files
so that enum values (Test Mode, Test Type, Content, Voltage Type, etc.) are
always in sync with the installed PPV version.

When PPV is NOT found the bridge degrades gracefully: every call returns
`None` or a sensible fallback, so DebugFrameworkAgent continues working in
standalone mode without any errors.

Discovery order:
  1. PPV_ROOT environment variable (highest priority — user override)
  2. Explicit `override` argument passed to `discover_ppv()`
  3. Paths relative to this file's location (works when the two repos sit
     side-by-side under the same parent, regardless of where the user cloned)
  4. Common absolute candidates (last resort safety net)

A PPV root is only accepted when it contains at least one
`configs/*ControlPanelConfig.json` file.
"""

from __future__ import annotations

import copy
import glob
import json
import os
import pathlib
from typing import Any

# ---------------------------------------------------------------------------
# Discovery candidates
# ---------------------------------------------------------------------------

_RELATIVE_CANDIDATES: list[pathlib.Path] = [
    # If _core/ is at  <root>/DebugFrameworkAgent/scripts/_core/
    # then PPV might be at <root>/PPV/
    pathlib.Path(__file__).parents[3] / "PPV",
    pathlib.Path(__file__).parents[4] / "PPV",
]

_ABSOLUTE_CANDIDATES: list[pathlib.Path] = [
    pathlib.Path("C:/Git/Automation/PPV"),
    pathlib.Path("D:/Git/Automation/PPV"),
    pathlib.Path("E:/Git/Automation/PPV"),
    pathlib.Path.home() / "Git/Automation/PPV",
    pathlib.Path.home() / "source/repos/Automation/PPV",
]

# Config file pattern that confirms a root is a genuine PPV install
_CONFIG_GLOB = "configs/*ControlPanelConfig.json"


def _is_valid_ppv_root(root: pathlib.Path) -> bool:
    """Return True when *root* looks like an actual PPV installation."""
    if not root.is_dir():
        return False
    return bool(glob.glob(str(root / _CONFIG_GLOB)))


def discover_ppv(override: pathlib.Path | str | None = None) -> pathlib.Path | None:
    """
    Search for a PPV installation and return its root Path, or None.

    Priority:
      PPV_ROOT env var → override argument → relative candidates → absolute candidates
    """
    # 1. Environment variable (highest priority)
    env_val = os.environ.get("PPV_ROOT")
    if env_val:
        p = pathlib.Path(env_val)
        if _is_valid_ppv_root(p):
            return p.resolve()

    # 2. Explicit argument
    if override is not None:
        p = pathlib.Path(override)
        if _is_valid_ppv_root(p):
            return p.resolve()

    # 3. Relative candidates (repo-layout-aware)
    for candidate in _RELATIVE_CANDIDATES:
        if _is_valid_ppv_root(candidate):
            return candidate.resolve()

    # 4. Common absolute paths
    for candidate in _ABSOLUTE_CANDIDATES:
        if _is_valid_ppv_root(candidate):
            return candidate.resolve()

    return None


# ---------------------------------------------------------------------------
# Bridge class
# ---------------------------------------------------------------------------

class PPVBridge:
    """
    Read-only bridge to a PPV installation.

    All public methods are safe to call even when PPV is not available —
    they return None / the supplied fallback instead of raising.
    """

    def __init__(self, ppv_root: pathlib.Path | str | None = None) -> None:
        """
        Initialise the bridge.

        Args:
            ppv_root: Explicit PPV root.  When None, auto-discovery is used.
        """
        if ppv_root is not None:
            root = pathlib.Path(ppv_root)
            self._root: pathlib.Path | None = root.resolve() if _is_valid_ppv_root(root) else None
        else:
            self._root = discover_ppv()

        self._config_cache: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_available(self) -> bool:
        """True when a valid PPV installation was found."""
        return self._root is not None

    @property
    def root(self) -> pathlib.Path | None:
        """Resolved PPV root path, or None."""
        return self._root

    @property
    def status_line(self) -> str:
        """One-line status string suitable for printing at tool startup."""
        if self._root:
            return f"PPV detected at: {self._root}"
        return "PPV not found — running in standalone mode."

    # ------------------------------------------------------------------
    # Config loading
    # ------------------------------------------------------------------

    def load_live_field_config(
        self,
        product: str,
        fallback: Any = None,
    ) -> dict[str, Any] | None:
        """
        Load the ControlPanelConfig JSON for *product* (GNR / CWF / DMR).

        Returns the parsed dict, or *fallback* (default None) if unavailable.
        Results are cached per product.
        """
        if not self.is_available:
            return fallback

        product = product.upper()
        if product in self._config_cache:
            return copy.deepcopy(self._config_cache[product])

        # Try exact match first, then prefix match
        config_dir = self._root / "configs"
        patterns   = [
            config_dir / f"{product}ControlPanelConfig.json",
        ]
        # Glob for anything that starts with the product name
        glob_matches = sorted(config_dir.glob(f"{product}*ControlPanelConfig.json"))
        for gm in glob_matches:
            if gm not in patterns:
                patterns.append(gm)

        for p in patterns:
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    self._config_cache[product] = data
                    return copy.deepcopy(data)
                except (json.JSONDecodeError, OSError):
                    pass

        return fallback

    # ------------------------------------------------------------------
    # Enum helpers
    # ------------------------------------------------------------------

    def sync_enums(self, product: str) -> dict[str, list[str]] | None:
        """
        Return a dict mapping enum key → valid values list for *product*.

        Keys returned (when present in the config):
          TEST_MODES, TEST_TYPES, CONTENT_OPTIONS,
          VOLTAGE_TYPES, TYPES, DOMAINS

        Returns None when PPV is unavailable or the config cannot be parsed.
        """
        cfg = self.load_live_field_config(product)
        if cfg is None:
            return None

        result: dict[str, list[str]] = {}
        # Common PPV config shapes — adapt as the PPV schema evolves
        key_map = {
            "testModes":      "TEST_MODES",
            "testTypes":      "TEST_TYPES",
            "contentOptions": "CONTENT_OPTIONS",
            "voltageTypes":   "VOLTAGE_TYPES",
            "sweepTypes":     "TYPES",
            "domains":        "DOMAINS",
            # Flat list variants
            "TEST_MODES":      "TEST_MODES",
            "TEST_TYPES":      "TEST_TYPES",
            "CONTENT_OPTIONS": "CONTENT_OPTIONS",
            "VOLTAGE_TYPES":   "VOLTAGE_TYPES",
            "TYPES":           "TYPES",
            "DOMAINS":         "DOMAINS",
        }
        for src_key, dst_key in key_map.items():
            val = cfg.get(src_key)
            if isinstance(val, list):
                result[dst_key] = [str(v) for v in val]

        return result if result else None

    def get_valid_enum(
        self,
        product:  str,
        enum_key: str,
        fallback: list[str] | None = None,
    ) -> list[str] | None:
        """
        Return the valid values list for one enum key, or *fallback*.

        Example: get_valid_enum("GNR", "TEST_MODES")
        """
        enums = self.sync_enums(product)
        if enums is None:
            return fallback
        return enums.get(enum_key, fallback)

    # ------------------------------------------------------------------
    # Field enable / configs
    # ------------------------------------------------------------------

    def get_field_enable_config(
        self,
        product:  str,
        fallback: Any = None,
    ) -> dict[str, bool] | None:
        """
        Return the field-enable flags dict from the PPV config, or *fallback*.

        Maps field name → enabled (bool).
        """
        cfg = self.load_live_field_config(product)
        if cfg is None:
            return fallback
        enables = cfg.get("fieldEnableConfig") or cfg.get("field_enable_config")
        if isinstance(enables, dict):
            return copy.deepcopy(enables)
        return fallback

    def get_field_configs(
        self,
        product:  str,
        fallback: Any = None,
    ) -> list[dict] | None:
        """
        Return the full field-config list from the PPV config, or *fallback*.

        Each entry typically contains: name, label, type, options, enabled, …
        """
        cfg = self.load_live_field_config(product)
        if cfg is None:
            return fallback
        fields = cfg.get("fieldConfigs") or cfg.get("fields") or cfg.get("field_configs")
        if isinstance(fields, list):
            return copy.deepcopy(fields)
        return fallback

    # ------------------------------------------------------------------
    # Experiment loading
    # ------------------------------------------------------------------

    def load_ppv_experiment(self, file_path: pathlib.Path | str) -> dict[str, Any]:
        """
        Read a PPV-style experiment JSON file and return it as a plain dict.

        Raises FileNotFoundError / ValueError on problems (same contract as
        experiment_builder.load_from_file).
        """
        p = pathlib.Path(file_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"PPV experiment file not found: {p}")
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in '{p}': {exc}") from exc
        if isinstance(raw, list):
            if not raw:
                raise ValueError(f"'{p}' contains an empty list.")
            raw = raw[0]
        if not isinstance(raw, dict):
            raise ValueError(f"'{p}' does not contain a valid experiment dict.")
        return copy.deepcopy(raw)

    # ------------------------------------------------------------------
    # Output path suggestion
    # ------------------------------------------------------------------

    def get_output_path(
        self,
        unit_id:       str | None = None,
        fallback_base: pathlib.Path | str | None = None,
    ) -> pathlib.Path:
        """
        Suggest an output directory for experiment artefacts.

        When PPV is available:  <ppv_root>/output/<unit_id>/
        Otherwise:              <fallback_base>/output/<unit_id>/

        Falls back to DebugFrameworkAgent/output/ when nothing else is known.
        """
        if fallback_base is None:
            # DebugFrameworkAgent/output/ relative to this file's location
            fallback_base = pathlib.Path(__file__).parents[2] / "output"

        base: pathlib.Path
        if self.is_available:
            base = self._root / "output"
        else:
            base = pathlib.Path(fallback_base)

        if unit_id:
            return (base / unit_id).resolve()
        return base.resolve()

    # ------------------------------------------------------------------
    # Enum validation
    # ------------------------------------------------------------------

    def validate_enum_value(
        self,
        product:          str,
        enum_key:         str,
        value:            str | None,
        bundled_fallback: list[str] | None = None,
    ) -> tuple[bool, str | None]:
        """
        Check whether *value* is a member of the live enum list for *enum_key*.

        Args:
            product:          GNR / CWF / DMR.
            enum_key:         One of TEST_MODES, TEST_TYPES, CONTENT_OPTIONS,
                              VOLTAGE_TYPES, TYPES, DOMAINS.
            value:            The value to check.
            bundled_fallback: Fallback list used when PPV is unavailable.

        Returns:
            (is_valid, error_message)
            is_valid=True means the value is acceptable (or no list available).
            error_message is None when is_valid=True.
        """
        if value is None or value == "":
            return True, None  # Empty / None is a "not set" state, not an enum error

        valid_list = self.get_valid_enum(product, enum_key, fallback=bundled_fallback)
        if valid_list is None:
            # No list available — can't validate, accept the value
            return True, None

        if value in valid_list:
            return True, None

        return False, (
            f"'{value}' is not a valid {enum_key} for {product}. "
            f"Expected one of: {', '.join(valid_list)}"
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_bridge_instance: PPVBridge | None = None


def get_bridge(ppv_root: pathlib.Path | str | None = None) -> PPVBridge:
    """
    Return the module-level PPVBridge singleton.

    The first call creates the instance (optionally with an explicit root).
    Subsequent calls return the cached instance regardless of arguments.
    Call `reset_bridge()` to force re-discovery.
    """
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = PPVBridge(ppv_root)
    return _bridge_instance


def reset_bridge() -> None:
    """Discard the cached bridge instance (mainly useful in tests)."""
    global _bridge_instance
    _bridge_instance = None
