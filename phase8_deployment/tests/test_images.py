import unittest
from streamlit.testing.v1 import AppTest
from phase8_deployment.app import (
    DEFAULT_FALLBACK_IMAGE,
    get_restaurant_image,
    render_restaurant_card,
)
from phase6_backend_api.app.schemas.recommend import RecommendationCard

class TestRestaurantImages(unittest.TestCase):
    def test_actual_restaurant_images_for_default_picks(self):
        """Verify the 5 default recommendations have actual restaurant-specific photos."""
        # 1. Meghana Foods in Koramangala
        meghana_img = get_restaurant_image("Meghana Foods", "Koramangala 5th Block", "Biryani, Andhra")
        self.assertIn("zmtcdn.com", meghana_img)
        self.assertIn("50691", meghana_img)

        # 2. eat.fit in Koramangala
        eatfit_img = get_restaurant_image("eat.fit", "Koramangala 5th Block", "Healthy Food, North Indian")
        self.assertIn("swiggy.com", eatfit_img)

        # 3. BOX8- Desi Meals in Koramangala
        box8_img = get_restaurant_image("BOX8- Desi Meals", "Koramangala 5th Block", "North Indian, Fast Food")
        self.assertIn("jdmagicbox.com", box8_img)
        self.assertIn("box8", box8_img)

        # 4. Desipun in Koramangala
        desipun_img = get_restaurant_image("Desipun", "Koramangala 5th Block", "North Indian")
        self.assertIn("jdmagicbox.com", desipun_img)
        self.assertIn("desipun", desipun_img)

        # 5. Bathinda Junction in Koramangala
        bathinda_img = get_restaurant_image("Bathinda Junction", "Koramangala 5th Block", "North Indian, Mughlai")
        self.assertIn("zmtcdn.com", bathinda_img)
        self.assertIn("59648", bathinda_img)

    def test_image_resolution_brand(self):
        toit_img = get_restaurant_image("Toit", "Indiranagar", "Brewery, Finger Food")
        self.assertIn("jdmagicbox.com", toit_img)
        self.assertIn("toit", toit_img)

        truffles_img = get_restaurant_image("Truffles", "Koramangala 5th Block", "Cafe, Burger")
        self.assertIn("jdmagicbox.com", truffles_img)
        self.assertIn("truffles", truffles_img)

        kfc_img = get_restaurant_image("KFC", "Indiranagar", "Fast Food, Burger")
        self.assertIn("wikimedia.org", kfc_img)

    def test_image_resolution_venue_fallback(self):
        url1 = get_restaurant_image("Cozy Corner Cafe", "Indiranagar", "Cafe, Bakery")
        url2 = get_restaurant_image("Royal Punjab Dhaba", "Koramangala", "North Indian, Punjabi")
        self.assertTrue(url1.startswith("https://"))
        self.assertTrue(url2.startswith("https://"))
        self.assertNotEqual(url1, url2)

    def test_image_resolution_fallback_on_unknown(self):
        url = get_restaurant_image("Unknown XYZ", "Nowhere", "")
        self.assertTrue(url.startswith("https://"))

    def test_image_resolution_handles_exceptions_gracefully(self):
        url = get_restaurant_image(None, None, None)
        self.assertEqual(url, DEFAULT_FALLBACK_IMAGE)

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
            self.assertTrue(img.startswith("https://"))
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
