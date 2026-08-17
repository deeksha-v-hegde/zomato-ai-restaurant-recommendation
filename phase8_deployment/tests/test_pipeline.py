"""Tests for Phase 8 Streamlit pipeline wrapper."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from phase6_backend_api.app.schemas.recommend import RecommendResponse
from phase8_deployment.pipeline import SearchInput, decode_display_text, load_runtime, run_search


class PipelineTests(unittest.TestCase):
    def test_load_runtime(self) -> None:
        load_runtime.cache_clear()
        ctx = load_runtime()
        self.assertTrue(ctx.status.store_loaded)
        self.assertGreater(ctx.status.restaurant_count, 0)
        self.assertGreater(len(ctx.catalog.locations), 0)
        self.assertGreater(len(ctx.catalog.cuisines), 0)

    def test_decode_display_text(self) -> None:
        self.assertEqual(decode_display_text("MoMo&#x27;s"), "MoMo's")
        self.assertEqual(decode_display_text(None), "N/A")
        self.assertEqual(decode_display_text(""), "N/A")

    def test_run_search_mocked(self) -> None:
        mock_ctx = MagicMock()
        mock_ctx.service.recommend.return_value = RecommendResponse(
            state="results",
            recommendations=[],
            used_fallback=False,
        )

        with patch("phase8_deployment.pipeline.load_runtime", return_value=mock_ctx):
            result = run_search(
                SearchInput(
                    location="Bellandur",
                    budget="high",
                    cuisine="North Indian",
                    min_rating=4.0,
                )
            )

        self.assertEqual(result.state, "results")
        mock_ctx.service.recommend.assert_called_once()

    @patch("phase4_recommendation_engine.groq_client.GroqLLMClient.complete")
    def test_load_runtime_does_not_call_groq_api(self, mock_complete: MagicMock) -> None:
        load_runtime.cache_clear()
        load_runtime()
        mock_complete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
