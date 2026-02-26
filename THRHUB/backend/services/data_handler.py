"""
Data Handler Service
=====================
Low-level JSON read/write for THRHUB data storage.
Mirrors the Portfolio DataHandler but adapted for REST API use.
"""
import json
import os
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import DATA_PATH

logger = logging.getLogger(__name__)


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _read_json(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: Any):
    _ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


class DataHandler:
    """Handles JSON file storage for units and tool sessions."""

    def __init__(self, data_root: str = DATA_PATH):
        self.data_root = data_root
        _ensure_dir(data_root)

    # ── Generic session store ─────────────────────────────────────────────────

    def list_sessions(self, category: str) -> List[Dict]:
        """Return metadata for all sessions in a category."""
        category_dir = os.path.join(self.data_root, category)
        if not os.path.isdir(category_dir):
            return []
        sessions = []
        for fname in sorted(os.listdir(category_dir)):
            if fname.endswith(".json"):
                path = os.path.join(category_dir, fname)
                try:
                    data = _read_json(path)
                    sessions.append({
                        "id": fname.replace(".json", ""),
                        "name": data.get("name", fname),
                        "created_at": data.get("created_at", ""),
                        "updated_at": data.get("updated_at", ""),
                    })
                except Exception:
                    pass
        return sessions

    def save_session(self, category: str, name: str, payload: Any) -> str:
        """Persist a named session. Returns the generated session ID."""
        session_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()
        doc = {
            "id": session_id,
            "name": name,
            "created_at": now,
            "updated_at": now,
            "data": payload,
        }
        path = os.path.join(self.data_root, category, f"{session_id}.json")
        _write_json(path, doc)
        return session_id

    def load_session(self, category: str, session_id: str) -> Optional[Dict]:
        """Load a session by ID. Returns None if not found."""
        path = os.path.join(self.data_root, category, f"{session_id}.json")
        if not os.path.exists(path):
            return None
        return _read_json(path)

    # ── Unit store ────────────────────────────────────────────────────────────

    def list_units(self, product: Optional[str] = None) -> List[Dict]:
        """Return metadata for all units, optionally filtered by product."""
        units_dir = os.path.join(self.data_root, "units")
        if not os.path.isdir(units_dir):
            return []
        result = []
        for fname in sorted(os.listdir(units_dir)):
            if fname.endswith(".json"):
                path = os.path.join(units_dir, fname)
                try:
                    data = _read_json(path)
                    if product and data.get("product", "").upper() != product.upper():
                        continue
                    result.append(data)
                except Exception:
                    pass
        return result

    def get_unit(self, unit_id: str) -> Optional[Dict]:
        """Return a single unit doc."""
        path = os.path.join(self.data_root, "units", f"{unit_id}.json")
        if not os.path.exists(path):
            return None
        return _read_json(path)

    def save_unit(self, unit: Dict) -> Dict:
        """Persist a unit dict. Returns the saved doc."""
        unit_id = unit.get("id") or str(uuid.uuid4())[:12]
        unit["id"] = unit_id
        unit.setdefault("created_at", datetime.utcnow().isoformat())
        unit["updated_at"] = datetime.utcnow().isoformat()
        path = os.path.join(self.data_root, "units", f"{unit_id}.json")
        _write_json(path, unit)
        return unit
