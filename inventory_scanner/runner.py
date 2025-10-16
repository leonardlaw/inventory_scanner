"""High-level orchestration for scanning Tesla inventory."""

from __future__ import annotations

import logging
import time
from typing import Iterable, List

from .alerts import print_alert
from .config import InventoryConfig
from .graph import plot_price_vs_mileage
from .models import Vehicle
from .storage import InventoryStore
from .tesla_client import TeslaAPIError, fetch_inventory

LOGGER = logging.getLogger(__name__)


def filter_inventory(vehicles: Iterable[Vehicle], config: InventoryConfig) -> List[Vehicle]:
    filtered: List[Vehicle] = []
    for vehicle in vehicles:
        if vehicle.year < config.min_year:
            continue
        if vehicle.mileage is None or vehicle.mileage > config.max_mileage:
            continue
        if not config.allow_repaired and not vehicle.is_clean_history:
            continue
        filtered.append(vehicle)
    return filtered


def run_once(config: InventoryConfig) -> List[Vehicle]:
    config.ensure_paths()
    store = InventoryStore(config.storage_path)

    try:
        inventory = fetch_inventory(config)
    except TeslaAPIError as error:
        LOGGER.error("Failed to query Tesla inventory: %s", error)
        raise

    matching = filter_inventory(inventory, config)
    new_listings = store.diff_new(matching)

    if matching:
        store.save(matching)
        try:
            plot_price_vs_mileage(matching, config.graph_path)
        except ValueError:
            LOGGER.info("Skipped graph generation due to missing data")
    else:
        LOGGER.info("No vehicles met the filter criteria")

    if new_listings:
        print_alert(new_listings)
    else:
        LOGGER.info("No new inventory items detected")

    return new_listings


def run_forever(config: InventoryConfig) -> None:
    if config.poll_interval is None:
        raise ValueError("poll_interval must be set for continuous monitoring")

    LOGGER.info("Starting continuous monitoring loop (interval=%ss)", config.poll_interval)
    while True:
        try:
            run_once(config)
        except TeslaAPIError:
            LOGGER.warning("Retrying after API failure in %s seconds", config.poll_interval)
        time.sleep(config.poll_interval)
