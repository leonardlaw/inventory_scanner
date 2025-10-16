"""Client for the public Tesla inventory API."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

import requests

from .config import InventoryConfig
from .models import Vehicle

LOGGER = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.tesla.com/inventory/used/ms",
    "Origin": "https://www.tesla.com",
    "Accept-Language": "en-US,en;q=0.9",
}


class TeslaAPIError(RuntimeError):
    """Raised when the Tesla inventory API cannot be queried successfully."""


class TeslaAPIAccessDenied(TeslaAPIError):
    """Raised when Tesla's bot protections block the request."""

    def __init__(self, response: requests.Response):
        reference = response.headers.get("x-reference-error")
        message = (
            "Tesla inventory API returned 403 Access Denied. "
            "Tesla's Akamai protection typically requires forwarding the "
            "browser cookies and headers from an authenticated session."
        )
        if reference:
            message = f"{message} Reference {reference}."
        super().__init__(message)
        self.status_code = response.status_code
        self.reference = reference
        self.body_snippet = response.text[:200]


def build_query(config: InventoryConfig, model: str) -> Dict[str, Any]:
    """Create the payload used when hitting the Tesla inventory endpoint."""

    return {
        "query": {
            "model": model,
            "condition": "used",
            "arrangeby": "Relevance",
            "order": "asc",
            "market": config.market,
            "zip": config.zip_code,
            "range": "0",
            "super_region": config.super_region,
            "language": config.language,
            "paymenttype": config.payment_type,
        },
        "offset": 0,
        "count": config.result_count,
        "outsideOffset": 0,
        "outsideSearch": False,
    }


def fetch_inventory(config: InventoryConfig) -> List[Vehicle]:
    """Fetch and normalize inventory entries from Tesla's API."""

    session = build_session(config)

    results: List[Vehicle] = []
    for model in config.desired_models:
        query = build_query(config, model)
        LOGGER.info("Requesting inventory for %s", model)
        response = session.get(
            config.query_url,
            params={"query": json.dumps(query)},
            timeout=30,
        )
        if response.status_code == 403:
            raise TeslaAPIAccessDenied(response)
        if response.status_code != 200:
            raise TeslaAPIError(
                f"Tesla inventory API returned {response.status_code}: {response.text[:200]}"
            )
        payload = response.json()
        records = payload.get("results") or []
        LOGGER.info("Received %s records for %s", len(records), model)
        for raw_vehicle in records:
            vehicle = normalize_vehicle(raw_vehicle, config)
            if vehicle:
                results.append(vehicle)
    return results


def build_session(config: InventoryConfig) -> requests.Session:
    session = requests.Session()
    headers = {**DEFAULT_HEADERS, "Referer": config.referer_url}
    if config.cookie_header:
        headers["Cookie"] = config.cookie_header
    if config.extra_headers:
        headers.update(config.extra_headers)
    session.headers.update(headers)
    return session


def normalize_vehicle(raw_vehicle: Dict[str, Any], config: InventoryConfig) -> Vehicle | None:
    """Convert Tesla's payload into a :class:`Vehicle` instance."""

    vin = raw_vehicle.get("VIN") or raw_vehicle.get("vin")
    if not vin:
        LOGGER.debug("Skipping entry without VIN: %s", raw_vehicle)
        return None

    year = safe_int(raw_vehicle.get("Year") or raw_vehicle.get("year"))
    price = safe_int(
        raw_vehicle.get("Price")
        or raw_vehicle.get("price")
        or raw_vehicle.get("Prc")
        or raw_vehicle.get("price")
    )
    mileage = safe_float(
        raw_vehicle.get("Odometer")
        or raw_vehicle.get("odometer")
        or raw_vehicle.get("Miles")
        or raw_vehicle.get("miles")
    )

    damage_history = extract_damage_history(raw_vehicle)
    trim = raw_vehicle.get("TrimName") or raw_vehicle.get("Trim") or ""
    exterior_color = raw_vehicle.get("ExteriorColor") or raw_vehicle.get("exterior_color") or ""
    interior_color = raw_vehicle.get("InteriorColor") or raw_vehicle.get("interior_color") or ""
    city = raw_vehicle.get("City") or raw_vehicle.get("city") or ""
    state = raw_vehicle.get("State") or raw_vehicle.get("state") or ""

    source_url = build_listing_url(raw_vehicle)

    if year is None or price is None or mileage is None:
        LOGGER.debug("Skipping %s due to missing numeric data", vin)
        return None

    return Vehicle(
        vin=vin,
        year=year,
        price=price,
        mileage=mileage,
        damage_history=damage_history,
        trim=trim,
        exterior_color=exterior_color,
        interior_color=interior_color,
        city=city,
        state=state,
        source_url=source_url,
        raw=raw_vehicle,
    )


def extract_damage_history(raw_vehicle: Dict[str, Any]) -> str:
    history = raw_vehicle.get("VehicleHistory") or raw_vehicle.get("vehicle_history")
    if isinstance(history, list):
        return ", ".join(str(item) for item in history if item)
    if isinstance(history, dict):
        text = history.get("value") or history.get("text")
        if text:
            return str(text)
    return str(history or "")


def build_listing_url(raw_vehicle: Dict[str, Any]) -> str:
    url = (
        raw_vehicle.get("InventoryUrl")
        or raw_vehicle.get("inventory_url")
        or raw_vehicle.get("Url")
        or raw_vehicle.get("url")
    )
    if url:
        return str(url)
    vin = raw_vehicle.get("VIN") or raw_vehicle.get("vin") or ""
    return f"https://www.tesla.com/inventory/used/ms?vin={vin}" if vin else ""


def safe_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
