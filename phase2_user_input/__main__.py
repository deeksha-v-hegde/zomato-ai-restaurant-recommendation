"""CLI entrypoint for Phase 2 user input."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from phase2_user_input.exceptions import DuplicateSubmitError, PreferenceValidationError
from phase2_user_input.form import collect_preferences
from phase2_user_input.pipeline import run_phase2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Phase 2: Collect and validate restaurant recommendation preferences."
    )
    parser.add_argument("--location", help="Location preference")
    parser.add_argument("--budget", help="Budget band: low | medium | high")
    parser.add_argument("--cuisine", help="Cuisine (comma-separated allowed)")
    parser.add_argument("--min-rating", help="Minimum rating 0-5")
    parser.add_argument("--additional", help="Optional free-text preferences")
    parser.add_argument(
        "--cuisine-match-mode",
        choices=["or", "and"],
        default=None,
        help="How multiple cuisines are matched (default: or)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for preferences interactively",
    )
    parser.add_argument(
        "--skip-catalog-check",
        action="store_true",
        help="Skip Phase 1 catalog existence warnings",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print validated preferences as JSON",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    provided = any([args.location, args.budget, args.cuisine, args.min_rating, args.additional])
    if not args.interactive and not provided:
        args.interactive = True

    try:
        if args.interactive:
            result = run_phase2(
                interactive=True,
                check_catalog=not args.skip_catalog_check,
                source="interactive",
            )
        else:
            raw = collect_preferences(
                location=args.location,
                budget=args.budget,
                cuisine=args.cuisine,
                min_rating=args.min_rating,
                additional_preferences=args.additional,
                cuisine_match_mode=args.cuisine_match_mode,
            )
            result = run_phase2(
                raw,
                check_catalog=not args.skip_catalog_check,
                source="args",
            )
    except PreferenceValidationError as exc:
        logging.error("Phase 2 validation failed:")
        for err in exc.errors:
            logging.error("  - %s", err)
        return 1
    except DuplicateSubmitError as exc:
        logging.error("%s", exc)
        return 1

    prefs = result.preferences
    if args.json:
        print(json.dumps(prefs.to_dict(), ensure_ascii=False, indent=2))
        return 0

    print("\nPhase 2 complete — Validated Preference Object")
    print(f"  source              : {result.source}")
    print(f"  location            : {prefs.location} (key={prefs.location_key})")
    print(f"  budget              : {prefs.budget}")
    print(f"  cuisines            : {prefs.cuisines} (match={prefs.cuisine_match_mode})")
    print(f"  min_rating          : {prefs.min_rating}")
    print(f"  additional          : {prefs.additional_preferences or '(none)'}")
    print(f"  additional_truncated: {prefs.additional_preferences_truncated}")
    if prefs.warnings:
        print("  warnings:")
        for warning in prefs.warnings:
            print(f"    - {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
