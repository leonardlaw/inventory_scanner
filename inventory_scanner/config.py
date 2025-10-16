"""Configuration models for the Tesla inventory scanner."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional


@dataclass(slots=True)
class InventoryConfig:
    """Runtime configuration for scanning Tesla's used inventory."""

    zip_code: str = "94506"
    min_year: int = 2023
    max_mileage: int = 50_000
    allow_repaired: bool = False
    poll_interval: Optional[int] = None
    result_count: int = 50
    storage_path: Path = Path("data/known_inventory.json")
    graph_path: Path = Path("artifacts/price_vs_mileage.png")
    query_url: str = "https://www.tesla.com/inventory/api/v1/inventory-results"
    referer_url: str = "https://www.tesla.com/inventory/used/ms"
    cookie_header: str | None = None
    extra_headers: dict[str, str] = field(default_factory=dict)
    market: str = "US"
    payment_type: str = "cash"
    super_region: str = "north america"
    language: str = "en"

    desired_models: Iterable[str] = field(default_factory=lambda: ("ms",))

    def ensure_paths(self) -> None:
        """Ensure that storage and artifact directories exist."""

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)
