"""Domain models for Tesla inventory entries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(slots=True)
class Vehicle:
    """Normalized representation of a Tesla vehicle listing."""

    vin: str
    year: int
    price: int
    mileage: float
    damage_history: str
    trim: str
    exterior_color: str
    interior_color: str
    city: str
    state: str
    source_url: str
    raw: Dict[str, Any]

    @property
    def is_clean_history(self) -> bool:
        history = (self.damage_history or "").lower()
        return "repair" not in history and "accident" not in history

    def to_summary(self) -> Dict[str, Any]:
        return {
            "vin": self.vin,
            "year": self.year,
            "price": self.price,
            "mileage": self.mileage,
            "damage_history": self.damage_history,
            "trim": self.trim,
            "exterior_color": self.exterior_color,
            "interior_color": self.interior_color,
            "city": self.city,
            "state": self.state,
            "source_url": self.source_url,
        }
