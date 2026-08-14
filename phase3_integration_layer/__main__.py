"""CLI entrypoint for Phase 3 integration layer."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from phase2_user_input.exceptions import PreferenceValidationError
from phase2_user_input.form import collect_preferences
from phase2_user_input.pipeline import run_phase2

from phase3_integration_layer.pipeline import run_phase3


def _safe_print(text: str) -> None:
    """Print text without failing on Windows consoles that lack UTF-8."""
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(text.encode(encoding, errors="replace").decode(encoding))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Phase 3: Filter restaurants and build the LLM prompt."
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
        help="Prompt for Phase 2 preferences interactively",
    )
    parser.add_argument(
        "--skip-catalog-check",
        action="store_true",
        help="Skip Phase 1 catalog existence warnings during validation",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=None,
        help="Override shortlist cap (default from config)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print Phase 3 result as JSON",
    )
    parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="Print the assembled LLM prompt",
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
            phase2 = run_phase2(
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
            phase2 = run_phase2(
                raw,
                check_catalog=not args.skip_catalog_check,
                source="args",
            )
    except PreferenceValidationError as exc:
        logging.error("Phase 2 validation failed:")
        for err in exc.errors:
            logging.error("  - %s", err)
        return 1

    kwargs: dict[str, int] = {}
    if args.max_candidates is not None:
        kwargs["max_candidates"] = args.max_candidates

    try:
        result = run_phase3(phase2.preferences, **kwargs)
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        return 1

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0

    diag = result.diagnostics
    _safe_print("\nPhase 3 complete - Integration Layer")
    print(f"  skip_llm           : {result.skip_llm}")
    print(f"  candidates         : {len(result.candidates)}")
    print(f"  filter pipeline    : total={diag.total_records} -> location={diag.after_location} "
          f"-> budget={diag.after_budget} -> cuisine={diag.after_cuisine} "
          f"-> rating={diag.after_rating} -> shortlist={diag.shortlist_count}")
    print(f"  shortlist_capped   : {diag.capped}")
    print(f"  strict_rating_drop : {diag.strict_rating_removed_all}")

    if result.no_match_message:
        print(f"  message            : {result.no_match_message}")
    if result.refine_hints:
        print("  refine hints:")
        for hint in result.refine_hints:
            print(f"    - {hint}")

    if result.prompt:
        print(f"  prompt_chars       : {len(result.prompt.full_text)}")
        print(f"  prompt_truncated   : {result.prompt.truncated}")
        if args.show_prompt:
            print("\n--- LLM Prompt ---")
            print(result.prompt.full_text)
    elif not result.skip_llm:
        print("  prompt             : (none)")

    if result.candidates and not args.show_prompt:
        print(f"\nTop candidates ({min(5, len(result.candidates))}):")
        for candidate in result.candidates[:5]:
            _safe_print(
                f"  - {candidate.name} | {candidate.location} | "
                f"{candidate.cuisines} | rating={candidate.rating} | cost={candidate.cost}"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
