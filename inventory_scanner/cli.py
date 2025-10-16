"""Command line interface for the Tesla inventory scanner."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

from .config import InventoryConfig
from .runner import run_forever, run_once


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Monitor Tesla's used Model S inventory")
    parser.add_argument("--zip", dest="zip_code", default="94506", help="ZIP code used for inventory search")
    parser.add_argument("--min-year", type=int, default=2023, help="Minimum model year to include")
    parser.add_argument("--max-mileage", type=int, default=50_000, help="Maximum mileage to include")
    parser.add_argument("--allow-repaired", action="store_true", help="Include vehicles with repair history")
    parser.add_argument("--interval", type=int, default=None, help="Polling interval in seconds for continuous mode")
    parser.add_argument("--result-count", type=int, default=50, help="Number of results to request per poll")
    parser.add_argument("--storage-path", type=Path, default=Path("data/known_inventory.json"), help="Where to persist known inventory")
    parser.add_argument("--graph-path", type=Path, default=Path("artifacts/price_vs_mileage.png"), help="Where to write the generated graph")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    parser.add_argument("--cookie", default=None, help="Optional Cookie header captured from a browser session")
    parser.add_argument(
        "--header",
        dest="headers",
        action="append",
        default=[],
        metavar="KEY:VALUE",
        help="Extra HTTP header(s) to forward to Tesla (may be specified multiple times)",
    )
    parser.add_argument("--continuous", action="store_true", help="Run continuously using the provided interval")
    return parser


def create_config(args: argparse.Namespace, extra_headers: dict[str, str]) -> InventoryConfig:
    config = InventoryConfig(
        zip_code=args.zip_code,
        min_year=args.min_year,
        max_mileage=args.max_mileage,
        allow_repaired=args.allow_repaired,
        poll_interval=args.interval if args.continuous else None,
        result_count=args.result_count,
        storage_path=args.storage_path,
        graph_path=args.graph_path,
        cookie_header=args.cookie,
        extra_headers=extra_headers,
    )
    return config


def parse_headers(pairs: Iterable[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for item in pairs:
        if ":" not in item:
            raise argparse.ArgumentTypeError(
                f"Invalid header format '{item}'. Expected KEY:VALUE."
            )
        key, value = item.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise argparse.ArgumentTypeError(
                f"Invalid header format '{item}'. Header name cannot be empty."
            )
        headers[key] = value
    return headers


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main(argv: Iterable[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    configure_logging(args.log_level)
    try:
        extra_headers = parse_headers(args.headers)
    except argparse.ArgumentTypeError as error:
        parser.error(str(error))
    config = create_config(args, extra_headers)

    if args.continuous:
        if args.interval is None:
            parser.error("--continuous requires --interval to be specified")
        run_forever(config)
    else:
        new_listings = run_once(config)
        if new_listings:
            logging.getLogger(__name__).info("Detected %s new vehicles", len(new_listings))
        else:
            logging.getLogger(__name__).info("No new vehicles detected on this run")


if __name__ == "__main__":
    main()
