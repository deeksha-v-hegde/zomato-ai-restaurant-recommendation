"""Unit tests for Phase 3 filtering and prompt assembly."""

from __future__ import annotations

import unittest

from phase1_data_ingestion.models import RestaurantRecord
from phase2_user_input.models import ValidatedPreferences

from phase3_integration_layer.filter import (
    build_refine_hints,
    filter_and_shortlist,
    filter_by_cuisine,
    filter_by_location,
    filter_by_rating,
)
from phase3_integration_layer.models import FilterDiagnostics
from phase3_integration_layer.prompt_builder import build_llm_prompt


def _record(
    *,
    name: str,
    location_key: str = "btm",
    location: str = "BTM",
    cuisines: list[str] | None = None,
    budget_band: str | None = "medium",
    cost: int | None = 500,
    rating: float | None = 4.2,
    rating_valid: bool = True,
    votes: int | None = 100,
) -> RestaurantRecord:
    cuisines = cuisines or ["Italian"]
    return RestaurantRecord(
        name=name,
        location=location,
        location_key=location_key,
        cuisines=cuisines,
        cuisine_text=", ".join(cuisines),
        cost=cost,
        budget_band=budget_band,
        rating=rating,
        rating_valid_for_filter=rating_valid,
        votes=votes,
    )


def _preferences(**overrides: object) -> ValidatedPreferences:
    base = {
        "location": "BTM",
        "location_key": "btm",
        "budget": "medium",
        "cuisines": ["Italian"],
        "cuisine_text": "Italian",
        "cuisine_match_mode": "or",
        "min_rating": 4.0,
    }
    base.update(overrides)
    return ValidatedPreferences(**base)  # type: ignore[arg-type]


class FilterTests(unittest.TestCase):
    def test_location_filter(self) -> None:
        records = [
            _record(name="A", location_key="btm"),
            _record(name="B", location_key="hsr", location="HSR"),
        ]
        matched = filter_by_location(records, _preferences())
        self.assertEqual([r.name for r in matched], ["A"])

    def test_cuisine_or_mode(self) -> None:
        records = [
            _record(name="Italian Place", cuisines=["Italian"]),
            _record(name="Chinese Place", cuisines=["Chinese"]),
            _record(name="Mixed", cuisines=["Italian", "Chinese"]),
        ]
        prefs = _preferences(cuisines=["Italian", "Chinese"], cuisine_text="Italian, Chinese")
        matched = filter_by_cuisine(records, prefs)
        self.assertEqual(len(matched), 3)

    def test_cuisine_and_mode(self) -> None:
        records = [
            _record(name="Italian Only", cuisines=["Italian"]),
            _record(name="Both", cuisines=["Italian", "Chinese"]),
        ]
        prefs = _preferences(
            cuisines=["Italian", "Chinese"],
            cuisine_text="Italian, Chinese",
            cuisine_match_mode="and",
        )
        matched = filter_by_cuisine(records, prefs)
        self.assertEqual([r.name for r in matched], ["Both"])

    def test_rating_filter(self) -> None:
        records = [
            _record(name="High", rating=4.5),
            _record(name="Low", rating=3.5),
            _record(name="Unknown", rating=None, rating_valid=False),
        ]
        matched = filter_by_rating(records, _preferences(min_rating=4.0))
        self.assertEqual([r.name for r in matched], ["High"])

    def test_zero_candidates_returns_hints(self) -> None:
        records = [_record(name="Only", location_key="hsr", location="HSR")]
        candidates, diagnostics, hints = filter_and_shortlist(records, _preferences())
        self.assertEqual(candidates, [])
        self.assertEqual(diagnostics.after_location, 0)
        self.assertTrue(hints)
        self.assertIn("No restaurants found", hints[0])

    def test_strict_rating_hint(self) -> None:
        records = [_record(name="Low Rated", rating=3.8)]
        candidates, diagnostics, hints = filter_and_shortlist(records, _preferences(min_rating=4.5))
        self.assertEqual(candidates, [])
        self.assertTrue(diagnostics.strict_rating_removed_all)
        self.assertTrue(any("rating" in hint.lower() for hint in hints))

    def test_shortlist_cap_and_deterministic_order(self) -> None:
        records = [
            _record(name="B", rating=4.5, votes=10),
            _record(name="A", rating=4.5, votes=20),
            _record(name="C", rating=4.0, votes=100),
        ]
        candidates, diagnostics, _ = filter_and_shortlist(
            records,
            _preferences(min_rating=3.5),
            max_candidates=2,
        )
        self.assertEqual(len(candidates), 2)
        self.assertTrue(diagnostics.capped)
        self.assertEqual(candidates[0].name, "A")
        self.assertEqual(candidates[1].name, "B")


class PromptBuilderTests(unittest.TestCase):
    def test_prompt_contains_schema_and_candidates(self) -> None:
        records = [_record(name="Test Cafe")]
        candidates, _, _ = filter_and_shortlist(records, _preferences(min_rating=3.0))
        prompt = build_llm_prompt(_preferences(min_rating=3.0), candidates)
        self.assertIn("Candidate restaurants", prompt.user_message)
        self.assertIn("recommendations", prompt.user_message)
        self.assertIn(candidates[0].candidate_id, prompt.user_message)
        self.assertEqual(len(prompt.candidate_ids), 1)

    def test_single_candidate_still_builds_prompt(self) -> None:
        records = [_record(name="Solo")]
        candidates, _, _ = filter_and_shortlist(records, _preferences(min_rating=3.0))
        prompt = build_llm_prompt(_preferences(min_rating=3.0), candidates)
        self.assertIn("Solo", prompt.full_text)


class RefineHintTests(unittest.TestCase):
    def test_budget_hint(self) -> None:
        diagnostics = FilterDiagnostics(
            total_records=10,
            after_location=5,
            after_budget=0,
            after_cuisine=0,
            before_rating=0,
            after_rating=0,
            shortlist_count=0,
        )
        hints = build_refine_hints(_preferences(), diagnostics)
        self.assertTrue(any("budget" in hint.lower() for hint in hints))


if __name__ == "__main__":
    unittest.main()
