"""CLI entrypoint for Phase 1 data ingestion."""

from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter

from phase1_data_ingestion.exceptions import DataIngestionError
from phase1_data_ingestion.pipeline import run_phase1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Phase 1: Load, clean, and store the Zomato Hugging Face dataset."
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Ignore cache and reload from Hugging Face.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Do not read from cache (still writes cache after processing).",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=5,
        help="Print N sample clean restaurants (default: 5).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        result = run_phase1(
            use_cache=not args.no_cache,
            force_refresh=args.force_refresh,
        )
    except DataIngestionError as exc:
        logging.error("Phase 1 failed: %s", exc)
        return 1

    bands = Counter(r.budget_band or "unknown" for r in result.records)
    valid_ratings = sum(1 for r in result.records if r.rating_valid_for_filter)

    print("\nPhase 1 complete")
    print(f"  from_cache : {result.from_cache}")
    print(f"  raw_rows   : {result.raw_rows}")
    print(f"  clean_rows : {result.clean_rows}")
    print(f"  valid_rating_rows : {valid_ratings}")
    print(f"  budget_bands : {dict(bands)}")
    print(f"  store_json : {result.store_paths['json']}")
    print(f"  store_csv  : {result.store_paths['csv']}")

    sample_n = max(0, args.sample)
    if sample_n:
        print(f"\nSample restaurants ({min(sample_n, len(result.records))}):")
        for restaurant in result.records[:sample_n]:
            print(
                f"  - {restaurant.name} | {restaurant.location} | "
                f"{restaurant.cuisine_text or 'N/A'} | "
                f"rating={restaurant.rating} | cost={restaurant.cost} | "
                f"budget={restaurant.budget_band}"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
