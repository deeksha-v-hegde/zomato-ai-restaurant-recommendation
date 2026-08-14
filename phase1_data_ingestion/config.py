"""Configuration for Phase 1: Data Ingestion."""

from pathlib import Path

PHASE1_ROOT = Path(__file__).resolve().parent
CACHE_DIR = PHASE1_ROOT / "data" / "cache"
CLEAN_STORE_PATH = CACHE_DIR / "restaurants_clean.json"
CLEAN_STORE_CSV_PATH = CACHE_DIR / "restaurants_clean.csv"

HF_DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"
HF_SPLIT = "train"

# Raw Hugging Face columns required for schema validation (DI-03, DI-13)
REQUIRED_RAW_COLUMNS = (
    "name",
    "location",
    "cuisines",
    "approx_cost(for two people)",
    "rate",
)

# Related attributes retained for later phases
OPTIONAL_RAW_COLUMNS = (
    "url",
    "address",
    "online_order",
    "book_table",
    "votes",
    "rest_type",
    "dish_liked",
    "listed_in(type)",
    "listed_in(city)",
)

# Budget band thresholds on approx cost for two (INR)
BUDGET_LOW_MAX = 300
BUDGET_MEDIUM_MAX = 700

# Location display aliases -> normalized key
LOCATION_ALIASES = {
    "bengaluru": "bangalore",
    "bangaluru": "bangalore",
    "blr": "bangalore",
    "new delhi": "delhi",
    "ncr": "delhi",
    "delhi ncr": "delhi",
    "mumbai suburban": "mumbai",
    "navi mumbai": "mumbai",
}
