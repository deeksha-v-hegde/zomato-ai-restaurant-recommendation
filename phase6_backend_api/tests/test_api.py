"""Unit tests for Phase 6 backend API."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from phase4_recommendation_engine.models import Phase4Result, Recommendation
from phase6_backend_api.app.dependencies import AppState, init_app_state, set_app_state
from phase6_backend_api.app.main import create_app
from phase1_data_ingestion.store import load_clean_store
from phase1_data_ingestion.config import CLEAN_STORE_PATH


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = load_clean_store(CLEAN_STORE_PATH)

    def setUp(self) -> None:
        state = AppState(
            records=self.records,
            store_loaded=True,
            groq_configured=True,
            store_path=CLEAN_STORE_PATH,
        )
        set_app_state(state)
        self.client = TestClient(create_app())

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_root(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("frontend_dev_url", payload)
        self.assertIn("docs_url", payload)

    def test_ready_when_store_loaded(self) -> None:
        response = self.client.get("/ready")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["store_loaded"])
        self.assertGreater(payload["restaurant_count"], 0)

    def test_catalog_locations(self) -> None:
        response = self.client.get("/catalog/locations")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreater(payload["count"], 0)
        self.assertIn("Bellandur", payload["items"])

    def test_catalog_cuisines(self) -> None:
        response = self.client.get("/catalog/cuisines")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreater(payload["count"], 0)
        self.assertTrue(any("italian" in item.lower() for item in payload["items"]))

    def test_recommend_validation_error(self) -> None:
        response = self.client.post(
            "/recommend",
            json={
                "location": "",
                "budget": "premium",
                "cuisine": "",
                "min_rating": 6,
            },
        )
        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertTrue(isinstance(detail, list))
        self.assertGreater(len(detail), 0)

    def test_recommend_no_match(self) -> None:
        response = self.client.post(
            "/recommend",
            json={
                "location": "Bellandur",
                "budget": "low",
                "cuisine": "Ethiopian",
                "min_rating": 4.5,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["state"], "no_match")
        self.assertEqual(payload["recommendations"], [])
        self.assertTrue(payload["refine_hints"])

    @patch("phase6_backend_api.app.services.recommendation_service.run_phase4")
    def test_recommend_success_mocked_llm(self, mock_run_phase4) -> None:
        mock_run_phase4.return_value = Phase4Result(
            recommendations=[
                Recommendation(
                    rank=1,
                    candidate_id="test123",
                    name="Test Cafe",
                    location="Bellandur",
                    cuisines="North Indian",
                    rating="4.5/5",
                    cost="Rs. 500 for two",
                    budget_band="medium",
                    explanation="Great fit for your preferences.",
                    source="llm",
                )
            ],
            summary="One strong match.",
            used_fallback=False,
            llm_model="mock-model",
        )

        response = self.client.post(
            "/recommend",
            json={
                "location": "Bellandur",
                "budget": "medium",
                "cuisine": "North Indian",
                "min_rating": 4.0,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["state"], "results")
        self.assertEqual(len(payload["recommendations"]), 1)
        self.assertEqual(payload["recommendations"][0]["name"], "Test Cafe")
        self.assertEqual(payload["summary"], "One strong match.")


class StartupTests(unittest.TestCase):
    def test_init_app_state_loads_store(self) -> None:
        state = init_app_state(CLEAN_STORE_PATH)
        self.assertTrue(state.store_loaded)
        self.assertGreater(len(state.records), 0)


if __name__ == "__main__":
    unittest.main()
