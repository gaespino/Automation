"""
Unit Service
=============
Business logic for unit lifecycle management and dashboard statistics.
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.data_handler import DataHandler

logger = logging.getLogger(__name__)


class UnitService:
    """Manages units: create, update, list, and derive statistics."""

    def __init__(self):
        self._dh = DataHandler()

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        """Return dashboard summary statistics."""
        all_units = self._dh.list_units()
        total = len(all_units)
        by_product: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        failing: List[Dict] = []

        for u in all_units:
            prod = u.get("product", "UNKNOWN")
            by_product[prod] = by_product.get(prod, 0) + 1
            status = u.get("status", "unknown").lower()
            by_status[status] = by_status.get(status, 0) + 1
            if status in ("fail", "failing", "reject"):
                failing.append({
                    "id": u.get("id"),
                    "vid": u.get("vid", ""),
                    "product": prod,
                    "status": status,
                    "fail_reason": u.get("fail_reason", ""),
                    "bucket": u.get("bucket", ""),
                    "updated_at": u.get("updated_at", ""),
                })

        return {
            "total_units": total,
            "by_product": by_product,
            "by_status": by_status,
            "failing_count": len(failing),
            "failing_units": failing,
        }

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def list_units(self, product: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        units = self._dh.list_units(product=product)
        if status:
            units = [u for u in units if u.get("status", "").lower() == status.lower()]
        return units

    def get_unit(self, unit_id: str) -> Optional[Dict]:
        return self._dh.get_unit(unit_id)

    def create_unit(self, data: Dict) -> Dict:
        """Validate and create a unit."""
        if not data.get("vid"):
            raise ValueError("'vid' (Visual ID) is required to create a unit.")
        data.setdefault("product", "GNR")
        data.setdefault("status", "active")
        data.setdefault("experiments", [])
        return self._dh.save_unit(data)

    def update_unit(self, unit_id: str, data: Dict) -> Optional[Dict]:
        existing = self._dh.get_unit(unit_id)
        if existing is None:
            return None
        existing.update(data)
        existing["id"] = unit_id  # prevent overwrite
        return self._dh.save_unit(existing)

    def get_experiments(self, unit_id: str) -> List[Dict]:
        unit = self._dh.get_unit(unit_id)
        if unit is None:
            return []
        return unit.get("experiments", [])
