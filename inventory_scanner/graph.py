"""Graph generation utilities."""

from __future__ import annotations

from pathlib import Path

from .models import Vehicle


def plot_price_vs_mileage(vehicles: list[Vehicle], output_path: Path) -> None:
    import matplotlib.pyplot as plt

    if not vehicles:
        raise ValueError("No vehicles supplied for graph generation")

    mileages = [vehicle.mileage for vehicle in vehicles]
    prices = [vehicle.price for vehicle in vehicles]
    labels = [vehicle.vin for vehicle in vehicles]

    plt.figure(figsize=(10, 6))
    plt.scatter(mileages, prices, c="#cc0000", alpha=0.7)
    plt.title("Tesla Model S Price vs Mileage")
    plt.xlabel("Mileage (miles)")
    plt.ylabel("Price (USD)")
    plt.grid(True, linestyle="--", alpha=0.3)

    for mileage, price, label in zip(mileages, prices, labels):
        plt.annotate(
            label,
            (mileage, price),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=8,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
