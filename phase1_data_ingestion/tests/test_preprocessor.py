"""Lightweight unit checks for Phase 1 preprocessing helpers."""

from __future__ import annotations

import unittest

import pandas as pd

from phase1_data_ingestion.exceptions import SchemaValidationError
from phase1_data_ingestion.loader import validate_schema
from phase1_data_ingestion.preprocessor import (
    budget_band_from_cost,
    deduplicate_records,
    normalize_location,
    parse_cost,
    parse_rating,
    preprocess,
    split_cuisines,
)


class PreprocessorTests(unittest.TestCase):
    def test_parse_rating_valid(self) -> None:
        rating, valid = parse_rating("4.1/5")
        self.assertEqual(rating, 4.1)
        self.assertTrue(valid)

    def test_parse_rating_new(self) -> None:
        rating, valid = parse_rating("NEW")
        self.assertIsNone(rating)
        self.assertFalse(valid)

    def test_parse_rating_out_of_range(self) -> None:
        rating, valid = parse_rating("6/5")
        self.assertIsNone(rating)
        self.assertFalse(valid)

    def test_parse_cost(self) -> None:
        self.assertEqual(parse_cost("1,200"), 1200)
        self.assertEqual(parse_cost("₹800"), 800)
        self.assertIsNone(parse_cost(""))

    def test_budget_bands(self) -> None:
        self.assertEqual(budget_band_from_cost(250), "low")
        self.assertEqual(budget_band_from_cost(500), "medium")
        self.assertEqual(budget_band_from_cost(1200), "high")

    def test_split_cuisines(self) -> None:
        self.assertEqual(split_cuisines("Italian, Chinese, italian"), ["Italian", "Chinese"])

    def test_normalize_location_alias(self) -> None:
        display, key = normalize_location(" Bengaluru ")
        self.assertEqual(key, "bangalore")
        self.assertIsNotNone(display)

    def test_schema_validation(self) -> None:
        with self.assertRaises(SchemaValidationError):
            validate_schema(["name", "location"])

    def test_preprocess_drops_blank_names_and_dedupes(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "name": "Cafe A",
                    "location": "BTM",
                    "cuisines": "Cafe",
                    "approx_cost(for two people)": "300",
                    "rate": "4.0/5",
                    "votes": 10,
                },
                {
                    "name": "Cafe A",
                    "location": "BTM",
                    "cuisines": "Cafe",
                    "approx_cost(for two people)": "300",
                    "rate": "4.2/5",
                    "votes": 50,
                },
                {
                    "name": None,
                    "location": "HSR",
                    "cuisines": "North Indian",
                    "approx_cost(for two people)": "400",
                    "rate": "3.9/5",
                    "votes": 5,
                },
            ]
        )
        records = preprocess(frame)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].votes, 50)
        self.assertEqual(records[0].rating, 4.2)


class DedupTests(unittest.TestCase):
    def test_deduplicate_prefers_higher_votes(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "name": "X",
                    "location": "Indiranagar",
                    "cuisines": "Italian",
                    "approx_cost(for two people)": "700",
                    "rate": "4.0/5",
                    "votes": 1,
                },
                {
                    "name": "X",
                    "location": "Indiranagar",
                    "cuisines": "Italian",
                    "approx_cost(for two people)": "700",
                    "rate": "3.5/5",
                    "votes": 100,
                },
            ]
        )
        records = preprocess(frame)
        self.assertEqual(len(deduplicate_records(records)), 1)
        self.assertEqual(records[0].votes, 100)


if __name__ == "__main__":
    unittest.main()
