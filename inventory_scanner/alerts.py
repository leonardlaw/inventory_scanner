"""Alerting helpers."""

from __future__ import annotations

from typing import Iterable, List

from .models import Vehicle


def format_vehicle(vehicle: Vehicle) -> str:
    return (
        f"{vehicle.year} {vehicle.trim or 'Model S'} - ${vehicle.price:,} "
        f"({vehicle.mileage:,.0f} miles)\n"
        f"VIN: {vehicle.vin}\n"
        f"History: {vehicle.damage_history or 'Clean'}\n"
        f"Location: {vehicle.city}, {vehicle.state}\n"
        f"Listing: {vehicle.source_url}"
    )


def render_alert(new_vehicles: Iterable[Vehicle]) -> str:
    vehicles: List[Vehicle] = list(new_vehicles)
    if not vehicles:
        return "No new matching vehicles found."
    lines = ["New Tesla Model S listings detected:"]
    for vehicle in vehicles:
        lines.append("".join(("- ", format_vehicle(vehicle))))
    return "\n\n".join(lines)


def print_alert(new_vehicles: Iterable[Vehicle]) -> None:
    message = render_alert(new_vehicles)
    print(message)
