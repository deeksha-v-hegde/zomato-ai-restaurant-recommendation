"""CLI entrypoint for Phase 4 recommendation engine (Groq)."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from phase2_user_input.exceptions import PreferenceValidationError
from phase2_user_input.form import collect_preferences
from phase2_user_input.pipeline import run_phase2
from phase3_integration_layer.pipeline import run_phase3

from phase4_recommendation_engine.config import DEFAULT_GROQ_MODEL, GROQ_API_KEY_ENV
from phase4_recommendation_engine.exceptions import GroqConfigurationError, RecommendationEngineError
from phase4_recommendation_engine.pipeline import run_phase4


def _safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(text.encode(encoding, errors="replace").decode(encoding))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Phase 4: Rank restaurants with Groq LLM explanations."
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
        "--model",
        default=DEFAULT_GROQ_MODEL,
        help=f"Groq model id (default: {DEFAULT_GROQ_MODEL})",
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Do not use deterministic fallback if Groq fails",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print Phase 4 result as JSON",
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

    try:
        phase3 = run_phase3(phase2.preferences)
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        return 1

    if phase3.skip_llm:
        _safe_print("\nPhase 4 skipped - no matching candidates from Phase 3.")
        if phase3.no_match_message:
            _safe_print(f"  message: {phase3.no_match_message}")
        for hint in phase3.refine_hints:
            _safe_print(f"  hint: {hint}")
        return 0

    from phase4_recommendation_engine.groq_client import GroqLLMClient

    try:
        client = GroqLLMClient(model=args.model)
        result = run_phase4(
            phase3,
            phase2.preferences,
            client=client,
            allow_fallback=not args.no_fallback,
        )
    except GroqConfigurationError as exc:
        logging.error("%s", exc)
        logging.error("Set %s before running Phase 4.", GROQ_API_KEY_ENV)
        return 1
    except RecommendationEngineError as exc:
        logging.error("Phase 4 failed: %s", exc)
        return 1

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0

    _safe_print("\nPhase 4 complete - Recommendation Engine (Groq)")
    _safe_print(f"  model          : {result.llm_model or args.model}")
    _safe_print(f"  used_fallback  : {result.used_fallback}")
    _safe_print(f"  recommendations: {len(result.recommendations)}")
    if result.fallback_reason:
        _safe_print(f"  fallback_reason: {result.fallback_reason}")
    if result.summary:
        _safe_print(f"  summary        : {result.summary}")
    if result.warnings:
        _safe_print("  warnings:")
        for warning in result.warnings:
            _safe_print(f"    - {warning}")

    for item in result.recommendations:
        _safe_print(
            f"\n  #{item.rank} {item.name} ({item.source})"
        )
        _safe_print(
            f"     {item.cuisines} | rating={item.rating} | cost={item.cost} | "
            f"budget={item.budget_band}"
        )
        _safe_print(f"     {item.explanation}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
