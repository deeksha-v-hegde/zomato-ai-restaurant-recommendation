import unittest
from streamlit.testing.v1 import AppTest
from phase8_deployment.app import (
    DEFAULT_FALLBACK_IMAGE,
    get_restaurant_image,
    render_restaurant_card,
)
from phase6_backend_api.app.schemas.recommend import RecommendationCard

class TestRestaurantImages(unittest.TestCase):
    def test_image_resolution_brand(self):
        url = get_restaurant_image("Meghana Foods", "Koramangala 5th Block", "Biryani, Andhra")
        self.assertTrue(url.startswith("https://images.unsplash.com/"))
        self.assertIn("563379091339", url)

    def test_image_resolution_cuisine(self):
        url1 = get_restaurant_image("Bhartiya Jalpan", "Indiranagar", "North Indian, Street Food")
        url2 = get_restaurant_image("Kapoor's Cafe", "Koramangala", "North Indian, Punjabi")
        self.assertTrue(url1.startswith("https://images.unsplash.com/"))
        self.assertTrue(url2.startswith("https://images.unsplash.com/"))
        self.assertNotEqual(url1, url2)

    def test_image_resolution_fallback_on_unknown(self):
        url = get_restaurant_image("Unknown XYZ", "Nowhere", "")
        self.assertTrue(url.startswith("https://images.unsplash.com/"))

    def test_image_resolution_handles_exceptions_gracefully(self):
        url = get_restaurant_image(None, None, None)
        self.assertTrue(url.startswith("https://images.unsplash.com/"))

    def test_card_structure(self):
        card = RecommendationCard(
            rank=1,
            candidate_id="test-1",
            name="Meghana Foods",
            location="Koramangala 5th Block",
            cuisines="Biryani, Andhra",
            rating="4.4",
            cost="₹600 for two",
            budget_band="medium",
            explanation="Spicy biryani",
            source="llm",
        )
        url = get_restaurant_image(card.name, card.location, card.cuisines)
        self.assertTrue(url.startswith("https://"))

    def test_app_test_search_and_reset(self):
        at = AppTest.from_file("phase8_deployment/app.py", default_timeout=30)
        at.run()
        self.assertFalse(at.exception)

        # Trigger search
        at.button(key="btn_find_restaurants").click().run()
        self.assertFalse(at.exception)

        # Verify search result has 5 recommendations
        res = at.session_state["search_result"]
        self.assertIsNotNone(res)
        self.assertEqual(len(res.recommendations), 5)

        # Verify all 5 recommendations have valid image URLs and all fields
        for card in res.recommendations:
            img = get_restaurant_image(card.name, card.location, card.cuisines)
            self.assertTrue(img.startswith("https://images.unsplash.com/"))
            self.assertTrue(bool(card.name))
            self.assertTrue(bool(card.cuisines))
            self.assertTrue(bool(card.rating))
            self.assertTrue(bool(card.cost))
            self.assertTrue(bool(card.explanation))

        # Test Reset Search Preferences button
        at.button(key="btn_reset_preferences").click().run()
        self.assertFalse(at.exception)
        self.assertIsNone(at.session_state["search_result"])
        self.assertEqual(at.session_state["pref_budget"], "Medium (₹500 - ₹1,500)")

if __name__ == "__main__":
    unittest.main()
