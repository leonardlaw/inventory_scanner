"""Local persistence helpers for inventory snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List

from .models import Vehicle


class InventoryStore:
    """Persist known inventory items to disk so new listings can be detected."""

    def __init__(self, path: Path):
        self.path = path

    def load(self) -> Dict[str, Dict]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as handle:
            try:
                payload = json.load(handle)
            except json.JSONDecodeError:
                return {}
        if not isinstance(payload, dict):
            return {}
        return payload

    def save(self, vehicles: Iterable[Vehicle]) -> None:
        payload = {vehicle.vin: vehicle.to_summary() for vehicle in vehicles}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def diff_new(self, vehicles: Iterable[Vehicle]) -> List[Vehicle]:
        known = self.load()
        new_items: List[Vehicle] = []
        for vehicle in vehicles:
            if vehicle.vin not in known:
                new_items.append(vehicle)
        return new_items
