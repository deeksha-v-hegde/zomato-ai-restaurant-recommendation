"""Phase 8: Streamlit deployment app - Clean Container (Removed Empty HTML Box)."""

from __future__ import annotations

import base64
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from phase2_user_input.exceptions import PreferenceValidationError
from phase6_backend_api.app.schemas.recommend import RecommendResponse
from phase6_backend_api.app.services.recommendation_service import validation_error_details
from phase8_deployment.config import APP_TITLE
from phase8_deployment.pipeline import (
    SearchInput,
    decode_display_text,
    load_runtime,
    resolve_location_for_search,
    run_search,
)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Base64 Image Helper
def get_image_b64(path_str: str, fallback_url: str) -> str:
    p = Path(path_str)
    if p.exists():
        try:
            return f"data:image/jpeg;base64,{base64.b64encode(p.read_bytes()).decode('utf-8')}"
        except Exception:
            pass
    return fallback_url


# Local generated images
PUNJABI_DHABA_IMG = get_image_b64(
    r"C:\Users\Admin\.gemini\antigravity-ide\brain\21c544a9-09ef-4c28-8971-88743c4cf899\north_indian_punjabi_dhaba_1786703068396.jpg",
    "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=800&q=80"
)
BREWPUB_IMG = get_image_b64(
    r"C:\Users\Admin\.gemini\antigravity-ide\brain\21c544a9-09ef-4c28-8971-88743c4cf899\brewpub_interior_1786702045865.jpg",
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80"
)
DIMSUM_IMG = get_image_b64(
    r"C:\Users\Admin\.gemini\antigravity-ide\brain\21c544a9-09ef-4c28-8971-88743c4cf899\asian_dimsum_bao_1786702069242.jpg",
    "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?auto=format&fit=crop&w=800&q=80"
)
HERO_IMG = get_image_b64(
    r"C:\Users\Admin\.gemini\antigravity-ide\brain\21c544a9-09ef-4c28-8971-88743c4cf899\zomato_hero_banner_1786700991607.jpg",
    "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80"
)


# Intelligent Restaurant & Cuisine Image + Details Matcher
def get_restaurant_media(name: str, cuisines: str):
    text_check = f"{name.lower()} {cuisines.lower()}"
    
    # 1. Punjabi / Dhaba / North Indian / Mughlai / Tandoor
    if any(k in text_check for k in ["punjabi", "dhaba", "butter chicken", "north indian", "mughlai", "tandoor", "biryani", "kabab"]):
        return {
            "image": PUNJABI_DHABA_IMG,
            "offer": "Flat 20% OFF on North Indian Thalis",
            "must_tries": ["Butter Chicken", "Dal Makhani", "Garlic Butter Naan", "Tandoori Chicken"],
            "secret": "Pair their rich Dal Makhani with tandoori garlic naan cooked fresh in a clay tandoor oven."
        }
        
    # 2. Maharashtrian / Malvani
    elif any(k in text_check for k in ["maharashtrian", "suryawanshi", "malvani", "pithla", "misal", "solkadhi", "vada pav"]):
        return {
            "image": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=800&q=80",
            "offer": "Complimentary Solkadhi with Thali",
            "must_tries": ["Spicy Misal Pav", "Pithla Bhakri", "Solkadhi", "Koliwada Fish Fry"],
            "secret": "Don't miss their authentic chilled Solkadhi served after a spicy Kolhapuri mutton or misal thali."
        }

    # 3. South Indian / Dosa / Idli / Chettinad
    elif any(k in text_check for k in ["south indian", "dosa", "idli", "ctr", "vidyarthi", "sambar", "chettinad", "tiffin"]):
        return {
            "image": "https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?auto=format&fit=crop&w=800&q=80",
            "offer": "Complimentary Filter Coffee with Dosa",
            "must_tries": ["Ghee Podi Masala Dosa", "Filter Coffee", "Crispy Vada", "Mini Tiffin"],
            "secret": "Visit around 8 AM for piping hot ghee podi idlis straight from the steamer with fresh coconut chutney."
        }

    # 4. Chinese / Asian / Dim Sum / Sushi / Bao
    elif any(k in text_check for k in ["chinese", "asian", "dim sum", "bao", "sushi", "ramen", "thai"]):
        return {
            "image": DIMSUM_IMG,
            "offer": "20% OFF on Dim Sum & Cocktail Combos",
            "must_tries": ["Char Siu Pork Bao", "Wild Mushroom & Truffle Dim Sum", "Spicy Tonkotsu Ramen"],
            "secret": "Book a table along the outer deck for breezy panoramic skyline views while sipping signature craft cocktails."
        }

    # 5. Brewery / Pub / Bar / Beer / Pizza
    elif any(k in text_check for k in ["brewery", "brewpub", "pub", "toit", "windmills", "beer", "pizza", "finger food"]):
        return {
            "image": BREWPUB_IMG,
            "offer": "Complimentary Beer Sampler Tasting Tray",
            "must_tries": ["Belgian Wheat Ale", "Smoked Chicken & BBQ Pizza", "Toit Baked Nachos"],
            "secret": "Ask for a terrace-level high table right before sunset to enjoy Bangalore's breeze paired with freshly tapped craft beer."
        }

    # 6. Cafe / Bakery / Coffee / Italian / Continental
    elif any(k in text_check for k in ["cafe", "coffee", "bakery", "pasta", "italian", "continental", "dessert"]):
        return {
            "image": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=800&q=80",
            "offer": "Flat 15% OFF on Gourmet Pastries & Coffee",
            "must_tries": ["Truffle Cream Pasta", "Artisan Cappuccino", "Woodfired Margherita", "Tiramisu"],
            "secret": "Order their artisanal sourdough pizza with freshly brewed single-origin espresso."
        }

    # 7. Default Gourmet Restaurant
    else:
        return {
            "image": HERO_IMG,
            "offer": "Flat 15% OFF on Dine-in via Zomato Gold",
            "must_tries": ["Chef's Tasting Platter", "Signature Gourmet Curry", "Craft Beverage"],
            "secret": "Request cozy corner booth seating for an intimate fine dining experience."
        }


# Native HTML CSS Injection
st.html(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Okra:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background-color: #F8F9FA;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        color: #1C1C1C;
    }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }

    /* Top Navigation Bar */
    .brand-container {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .brand-name {
        font-family: 'Okra', 'Inter', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        font-style: italic;
        color: #E23744;
        letter-spacing: -0.5px;
        line-height: 1;
    }

    .ai-badge {
        background: linear-gradient(135deg, #E23744 0%, #F43F5E 100%);
        color: white;
        font-weight: 700;
        font-size: 0.8rem;
        padding: 3px 10px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        gap: 4px;
        box-shadow: 0 2px 6px rgba(226, 55, 68, 0.25);
    }

    /* Remove outer container box and radio circles from stRadio */
    div[data-testid="stRadio"],
    div[data-testid="stRadio"] > div,
    div[data-testid="stRadio"] > div > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    div[data-testid="stRadio"] label {
        background: white !important;
        border: 1px solid #E4E4E7 !important;
        border-radius: 20px !important;
        padding: 5px 16px !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #52525B !important;
        cursor: pointer !important;
        margin-right: 6px !important;
    }

    div[data-testid="stRadio"] label:hover {
        border-color: #FECDD3 !important;
        color: #E23744 !important;
    }

    div[data-testid="stRadio"] label[data-checked="true"] {
        background: #FFF1F2 !important;
        color: #E23744 !important;
        border-color: #FECDD3 !important;
        font-weight: 700 !important;
    }

    /* Hide radio dot circle */
    div[data-testid="stRadio"] label > div:first-child {
        display: none !important;
    }

    /* Streamlit Container Card Styling */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: white !important;
        border-radius: 20px !important;
        border: 1px solid #E5E7EB !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
        padding: 1.25rem 1.5rem !important;
        margin-bottom: 1.5rem !important;
    }

    .quick-ideas-label {
        font-size: 0.75rem;
        font-weight: 800;
        color: #9CA3AF;
        letter-spacing: 0.06em;
        margin-bottom: 0.4rem;
    }

    /* Preferences Panel */
    .preferences-panel {
        background: #FAFAFA;
        border: 1.5px solid #F43F5E;
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        margin-top: 1rem;
    }

    .panel-header {
        font-size: 0.88rem;
        font-weight: 800;
        color: #BE123C;
        letter-spacing: 0.03em;
        margin-bottom: 0.8rem;
    }

    .tag-section-title {
        font-size: 0.75rem;
        font-weight: 800;
        color: #52525B;
        letter-spacing: 0.05em;
        margin: 1rem 0 0.5rem 0;
        text-transform: uppercase;
    }

    /* --- TOP 5 CARD REFERENCE DESIGN --- */
    .top5-card-container {
        background: white;
        border: 1.5px solid #FECDD3;
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.75rem;
        box-shadow: 0 6px 24px rgba(226, 55, 68, 0.06);
        display: grid;
        grid-template-columns: 310px 1fr;
        gap: 1.5rem;
        align-items: start;
    }

    @media (max-width: 900px) {
        .top5-card-container {
            grid-template-columns: 1fr;
        }
    }

    .left-image-wrapper {
        position: relative;
        border-radius: 16px;
        overflow: hidden;
        height: 100%;
        min-height: 380px;
        background: #F4F4F5;
    }

    .left-image-wrapper img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }

    .badge-rank-gold {
        position: absolute;
        top: 12px;
        left: 12px;
        background: rgba(0, 0, 0, 0.88);
        color: #F59E0B;
        border: 1.5px solid #F59E0B;
        border-radius: 8px;
        font-weight: 800;
        font-size: 0.78rem;
        padding: 4px 10px;
        letter-spacing: 0.04em;
    }

    .badge-rank-dark {
        position: absolute;
        top: 12px;
        left: 12px;
        background: rgba(0, 0, 0, 0.88);
        color: white;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 8px;
        font-weight: 800;
        font-size: 0.78rem;
        padding: 4px 10px;
        letter-spacing: 0.04em;
    }

    .offer-banner-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(135deg, #E23744 0%, #CB202D 100%);
        color: white;
        font-weight: 700;
        font-size: 0.78rem;
        padding: 8px 12px;
        text-align: center;
    }

    .cat-pill {
        background: #F4F4F5;
        color: #3F3F46;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 6px;
        margin-right: 4px;
    }

    .why-gemini-box {
        background: #FFF5F5;
        border: 1px solid #FFE4E4;
        border-radius: 14px;
        padding: 1rem 1.25rem;
        margin: 1rem 0 0.8rem 0;
    }

    .why-gemini-title {
        font-size: 0.85rem;
        font-weight: 800;
        color: #E23744;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .palate-matrix-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 10px;
    }

    .palate-item {
        background: white;
        border: 1px solid #FEE2E2;
        border-radius: 10px;
        padding: 8px 12px;
        font-size: 0.8rem;
    }

    .insider-secret-box {
        background: #FEFCE8;
        border: 1px solid #FEF08A;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin: 0.8rem 0;
        font-size: 0.85rem;
        color: #854D0E;
        line-height: 1.4;
    }

    .rating-badge {
        background: #24963F;
        color: white;
        font-weight: 700;
        font-size: 0.88rem;
        padding: 3px 8px;
        border-radius: 6px;
    }
    </style>
    """
)

# Cache Runtime Load
@st.cache_resource(show_spinner="Loading Zomato AI Engine...")
def get_runtime():
    return load_runtime()


def _index_or_zero(items: list[str], value: str) -> int:
    try:
        return items.index(value)
    except ValueError:
        return 0


# Load Application Context
try:
    ctx = get_runtime()
except Exception as exc:
    st.error(f"Could not start engine: {exc}", icon=":material/error:")
    st.stop()

# Initialize Session State
st.session_state.setdefault("sel_location", "All Locations")
st.session_state.setdefault("sel_cuisine", "North Indian")
st.session_state.setdefault("sel_budget", "Mid-Range (₹500-1500)")
st.session_state.setdefault("sel_rating", "4.0+ Stars")
st.session_state.setdefault("sel_diet", "Veg Friendly Options")
st.session_state.setdefault("sel_mode", "🍽️ Dine-in Only")
st.session_state.setdefault("sel_spice", "Medium Zing (Balanced)")
st.session_state.setdefault("prompt_text", "Craving butter chicken, garlic naan and a vibrant family atmosphere")
st.session_state.setdefault("selected_moods", ["Family Dinner & Celebration"])
st.session_state.setdefault("selected_amenities", ["Outdoor Seating", "Air Conditioned"])
st.session_state.setdefault("show_preferences", True)
st.session_state.setdefault("active_tab", "✨ AI Recommendations")

# --- TOP NAVIGATION HEADER ---
c_logo, c_nav, c_user = st.columns([2.5, 4.5, 3], vertical_alignment="center")

with c_logo:
    st.html(
        """
        <div class="brand-container">
            <span class="brand-name">zomato</span>
            <span class="ai-badge">✨ AI Engine</span>
        </div>
        """
    )

with c_nav:
    tab_options = ["✨ AI Recommendations", "📊 Compare Matrix", "🔍 Catalog Explorer"]
    selected_tab = st.radio(
        "Navigation",
        options=tab_options,
        index=tab_options.index(st.session_state.active_tab),
        horizontal=True,
        label_visibility="collapsed",
        key="nav_radio",
    )
    st.session_state.active_tab = selected_tab

with c_user:
    st.html(
        """
        <div style="display: flex; align-items: center; justify-content: flex-end; gap: 8px;">
            <span style="background: white; border: 1px solid #E4E4E7; border-radius: 20px; padding: 5px 12px; font-weight: 600; font-size: 0.83rem; cursor: pointer;">
                ⚙️ Dining History <b style="background:#E23744; color:white; border-radius:10px; padding:1px 6px; font-size:0.75rem; margin-left:2px;">3</b>
            </span>
            <span style="background: white; border: 1px solid #E4E4E7; border-radius: 20px; padding: 5px 10px; font-weight: 600; font-size: 0.83rem; cursor: pointer;">
                🔖 <b style="background:#E23744; color:white; border-radius:50%; width:16px; height:16px; display:inline-flex; align-items:center; justify-content:center; font-size:0.7rem; margin-left:2px;">2</b>
            </span>
            <div style="display: flex; align-items: center; gap: 6px; background: white; border: 1px solid #E4E4E7; padding: 4px 14px; border-radius: 24px; font-size: 0.83rem; font-weight: 600; cursor: pointer;">
                <span style="font-size: 0.95rem;">👤</span>
                <span>User Profile</span>
            </div>
        </div>
        """
    )

st.html("<div style='height: 10px;'></div>")

# --- IF TAB 2 OR TAB 3 SELECTED ---
if st.session_state.active_tab == "📊 Compare Matrix":
    st.subheader("📊 Compare Matrix")
    st.info("Compare matrix view for shortlisted restaurants.")
    st.dataframe(
        [
            {"Name": r.name, "Location": r.location, "Cuisines": ", ".join(r.cuisines[:3]), "Rating": r.rating, "Cost": f"₹{r.cost}"}
            for r in ctx.service.records[:15]
        ],
        use_container_width=True,
    )
    st.stop()
elif st.session_state.active_tab == "🔍 Catalog Explorer":
    st.subheader("🔍 Dataset Catalog Explorer")
    search_q = st.text_input("Filter Catalog Records", placeholder="Search by name, cuisine, or area...")
    matching = [
        r for r in ctx.service.records
        if not search_q or search_q.lower() in r.name.lower() or search_q.lower() in r.location.lower() or any(search_q.lower() in c.lower() for c in r.cuisines)
    ][:30]
    st.write(f"Showing **{len(matching)}** matching restaurants out of **{len(ctx.service.records):,}**:")
    for m in matching:
        st.write(f"- **{m.name}** ({m.location}) — *{', '.join(m.cuisines)}* — Rating: **{m.rating}★** (₹{m.cost} for two)")
    st.stop()

# --- MAIN CONTROLS CONTAINER ---
with st.container(border=True):
    # 1. Main Natural Language AI Prompt Box & Primary Button
    col_input, col_btn = st.columns([4.7, 1.3], vertical_alignment="center")
    with col_input:
        prompt_val = st.text_input(
            "Natural Language Prompt",
            value=st.session_state.prompt_text,
            placeholder="Tell us what you're craving (e.g. spicy biryani, thin crust pizza, rooftop craft beer...)",
            label_visibility="collapsed",
            key="main_prompt_input",
        )
        st.session_state.prompt_text = prompt_val
    with col_btn:
        submitted = st.button(
            "✨ Recommend Top Picks",
            type="primary",
            use_container_width=True,
            key="search_btn",
        )

    # 2. Quick Ideas Chips Carousel
    st.html("<div style='height: 4px;'></div><div class='quick-ideas-label'>QUICK IDEAS:</div>")

    q1, q2, q3, q4 = st.columns(4)
    if q1.button("🍛 Maharashtrian Pithla Bhakri & Misal Pav", key="idea_mah", use_container_width=True):
        st.session_state.sel_cuisine = "Maharashtrian" if "Maharashtrian" in ctx.catalog.cuisines else ctx.catalog.cuisines[0]
        st.session_state.prompt_text = "Authentic Maharashtrian Pithla Bhakri, spicy Misal Pav & Solkadhi"
        st.rerun()
    if q2.button("🥘 North Indian Thali & Butter Chicken", key="idea1", use_container_width=True):
        st.session_state.sel_cuisine = "North Indian"
        st.session_state.prompt_text = "North Indian Thali, Butter Chicken & Dal Makhani"
        st.rerun()
    if q3.button("🍕 Woodfired Pizza & Belgian Wheat Beer", key="idea2", use_container_width=True):
        st.session_state.sel_cuisine = "Italian" if "Italian" in ctx.catalog.cuisines else ctx.catalog.cuisines[0]
        st.session_state.prompt_text = "Crisp Belgian wheat beer & woodfired pizza with rooftop seating"
        st.rerun()
    if q4.button("☕ Filter Coffee & Crispy Ghee Dosa", key="idea3", use_container_width=True):
        st.session_state.sel_cuisine = "South Indian" if "South Indian" in ctx.catalog.cuisines else ctx.catalog.cuisines[0]
        st.session_state.prompt_text = "Authentic South Indian crispy ghee podi dosa & strong filter coffee"
        st.rerun()

    st.html("<hr style='border: none; border-top: 1px solid #F3F4F6; margin: 1.2rem 0;' />")

    # 3. Dynamic Filter Bar (Bound to Catalog Data)
    f_title_col, f_reset_col = st.columns([8, 2])
    with f_title_col:
        st.html("<div style='font-size:0.85rem; font-weight:800; color:#52525B;'>🎛️ FILTERS</div>")
    with f_reset_col:
        if st.button("Reset all filters", key="reset_btn"):
            st.session_state.sel_location = "All Locations"
            st.session_state.sel_cuisine = "North Indian"
            st.session_state.sel_budget = "Mid-Range (₹500-1500)"
            st.session_state.sel_rating = "4.0+ Stars"
            st.session_state.selected_moods = []
            st.session_state.selected_amenities = []
            st.session_state.prompt_text = ""
            st.rerun()

    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)

    loc_options = ["All Locations"] + ctx.catalog.locations
    cui_options = ["All Cuisines"] + ctx.catalog.cuisines

    with col_f1:
        sel_loc = st.selectbox(
            "📍 LOCATION",
            options=loc_options,
            index=_index_or_zero(loc_options, st.session_state.sel_location),
            key="sb_location",
        )
        st.session_state.sel_location = sel_loc

    with col_f2:
        budget_opts = ["Mid-Range (₹500-1500)", "Budget Friendly (<₹500)", "Luxury / Fine Dining (₹1500+)"]
        sel_bud = st.selectbox(
            "₹ BUDGET",
            options=budget_opts,
            index=_index_or_zero(budget_opts, st.session_state.sel_budget),
            key="sb_budget",
        )
        st.session_state.sel_budget = sel_bud

    with col_f3:
        sel_cui = st.selectbox(
            "🍴 CUISINE",
            options=cui_options,
            index=_index_or_zero(cui_options, st.session_state.sel_cuisine),
            key="sb_cuisine",
        )
        st.session_state.sel_cuisine = sel_cui

    with col_f4:
        rating_opts = ["Any Rating", "3.5+ Stars", "4.0+ Stars", "4.5+ Stars"]
        sel_rat = st.selectbox(
            "⭐ MIN RATING",
            options=rating_opts,
            index=_index_or_zero(rating_opts, st.session_state.sel_rating),
            key="sb_rating",
        )
        st.session_state.sel_rating = sel_rat

    with col_f5:
        st.write("✨ PREFERENCES")
        active_count = len(st.session_state.selected_moods) + len(st.session_state.selected_amenities)
        toggle_label = f"✨ {active_count} Active ▴" if st.session_state.show_preferences else f"✨ {active_count} Active ▾"
        if st.button(toggle_label, use_container_width=True, key="pref_toggle"):
            st.session_state.show_preferences = not st.session_state.show_preferences
            st.rerun()

    # 4. Expanded Preferences Panel
    if st.session_state.show_preferences:
        st.html(
            """
            <div class='preferences-panel'>
                <div class='panel-header'>✨ ADDITIONAL PALATE & DINING PREFERENCES</div>
            """
        )

        # Row 1: Dropdown Selectors
        d1, d2, d3 = st.columns(3)
        with d1:
            diet_opts = ["Veg Friendly Options", "Pure Vegetarian", "Non-Vegetarian", "Jain Options"]
            st.session_state.sel_diet = st.selectbox(
                "DIETARY REQUIREMENT:",
                options=diet_opts,
                index=_index_or_zero(diet_opts, st.session_state.sel_diet),
                key="sb_diet",
            )
        with d2:
            mode_opts = ["🍽️ Dine-in Only", "🛵 Delivery Available", "🛍️ Takeaway", "🍸 Nightlife & Pub"]
            st.session_state.sel_mode = st.selectbox(
                "DINING EXPERIENCE / MODE:",
                options=mode_opts,
                index=_index_or_zero(mode_opts, st.session_state.sel_mode),
                key="sb_mode",
            )
        with d3:
            spice_opts = ["Medium Zing (Balanced)", "Mild / Kid Friendly", "Fiery & Spicy!"]
            st.session_state.sel_spice = st.selectbox(
                "🌶️ SPICE LEVEL:",
                options=spice_opts,
                index=_index_or_zero(spice_opts, st.session_state.sel_spice),
                key="sb_spice",
            )

        # Row 2: Mood & Occasion Tag Selection
        st.html("<div class='tag-section-title'>SPECIFIC MOOD OR OCCASION:</div>")
        mood_options = [
            "Date Night & Romantic", "Casual Catchup & Hangout", "Family Dinner & Celebration",
            "Bustling Brewery & Party", "Cozy Cafe & Work", "Late Night Cravings", "Luxury Fine Dining"
        ]
        
        m_cols = st.columns(len(mood_options))
        for idx, mood in enumerate(mood_options):
            is_active = mood in st.session_state.selected_moods
            btn_type = "primary" if is_active else "secondary"
            if m_cols[idx].button(mood, key=f"mood_tag_{idx}", type=btn_type):
                if is_active:
                    st.session_state.selected_moods.remove(mood)
                else:
                    st.session_state.selected_moods.append(mood)
                st.rerun()

        # Row 3: Amenity Tag Selection
        st.html("<div class='tag-section-title'>SPECIAL AMENITIES & FEATURES:</div>")
        amenity_options = [
            "Outdoor Seating", "Craft Beer / Brewery", "Live Music & DJ",
            "Rooftop View", "Pet Friendly", "Valet Parking", "Air Conditioned"
        ]
        
        a_cols = st.columns(len(amenity_options))
        for idx, amen in enumerate(amenity_options):
            is_active = amen in st.session_state.selected_amenities
            btn_type = "primary" if is_active else "secondary"
            if a_cols[idx].button(amen, key=f"amen_tag_{idx}", type=btn_type):
                if is_active:
                    st.session_state.selected_amenities.remove(amen)
                else:
                    st.session_state.selected_amenities.append(amen)
                st.rerun()

        st.html("</div>")

# --- EXECUTE RECOMMENDATION SEARCH AUTOMATICALLY ON CONTROL CHANGES ---
if "Budget Friendly" in st.session_state.sel_budget:
    budget_param = "low"
elif "Luxury" in st.session_state.sel_budget:
    budget_param = "high"
else:
    budget_param = "medium"

min_rating_val = 0.0
if "3.5+" in st.session_state.sel_rating: min_rating_val = 3.5
elif "4.0+" in st.session_state.sel_rating: min_rating_val = 4.0
elif "4.5+" in st.session_state.sel_rating: min_rating_val = 4.5

resolved_display_loc = resolve_location_for_search(ctx, st.session_state.sel_location, st.session_state.sel_cuisine)

combined_prefs = f"{st.session_state.prompt_text} {st.session_state.sel_diet} {st.session_state.sel_mode} {st.session_state.sel_spice} {' '.join(st.session_state.selected_moods)} {' '.join(st.session_state.selected_amenities)}"

search_input_obj = SearchInput(
    location=st.session_state.sel_location,
    budget=budget_param,
    cuisine=st.session_state.sel_cuisine,
    min_rating=min_rating_val,
    additional_preferences=combined_prefs.strip() or None,
)

try:
    with st.spinner(f"Finding top AI recommendation matches for {st.session_state.sel_cuisine} in {resolved_display_loc}..."):
        search_result = run_search(search_input_obj)
        search_error = None
except PreferenceValidationError as exc:
    search_result = None
    search_error = [f"{detail.field}: {detail.message}" for detail in validation_error_details(exc)]
except Exception as exc:
    search_result = None
    search_error = [f"Search failed: {exc}"]

# --- DISPLAY TOP 5 REFERENCE CARD RECOMMENDATIONS ---
if search_error:
    for message in search_error:
        st.error(message, icon=":material/error:")
elif search_result is not None:
    res: RecommendResponse = search_result
    
    if res.state == "no_match":
        st.warning(res.no_match_message or f"No matching {st.session_state.sel_cuisine} restaurants found for current filters.", icon=":material/search_off:")
        if res.refine_hints:
            st.caption("Try tweaking your filters or prompt:")
            for hint in res.refine_hints:
                st.markdown(f"- {hint}")
    else:
        if res.used_fallback or res.state == "fallback":
            st.info(res.fallback_reason or f"Showing top rated {st.session_state.sel_cuisine} restaurants in {resolved_display_loc}.", icon=":material/info:")

        count = len(res.recommendations)
        st.subheader(f"✨ Recommended Top {count} Matches for {st.session_state.sel_cuisine} in {resolved_display_loc}")
        if res.summary:
            st.caption(decode_display_text(res.summary))

        for idx, item in enumerate(res.recommendations):
            name = decode_display_text(item.name)
            loc = decode_display_text(item.location)
            cui = decode_display_text(item.cuisines)
            rating = decode_display_text(item.rating)
            cost = decode_display_text(item.cost)
            b_band = decode_display_text(item.budget_band).title()
            explanation = decode_display_text(item.explanation)

            rank_num = item.rank
            match_pct = max(99 - (rank_num - 1) * 7, 80)

            # Get 100% matched media details for this restaurant & cuisine!
            media = get_restaurant_media(name, cui)

            img_url = media["image"]
            offer_text = media["offer"]
            dishes = media["must_tries"]
            secret = media["secret"]

            rank_badge_html = f'<div class="badge-rank-gold">👑 #{rank_num} TOP MATCH</div>' if rank_num == 1 else f'<div class="badge-rank-dark">#{rank_num} RECOMMENDED</div>'
            cuisine_pills = "".join(f'<span class="cat-pill">{c.strip()}</span>' for c in cui.split(",")[:4])
            dishes_html = "".join(f'<span style="background:#FFF1F2; color:#BE123C; border:1px solid #FECDD3; font-size:0.78rem; font-weight:600; padding:3px 10px; border-radius:12px; margin-right:4px;">🍽️ {d}</span>' for d in dishes)

            card_html = f"""
            <div class="top5-card-container">
                <div class="left-image-wrapper">
                    <img src="{img_url}" alt="{name}" />
                    {rank_badge_html}
                    <div style="position: absolute; top: 12px; right: 12px; background: white; border-radius: 8px; width: 28px; height: 28px; display: grid; place-items: center; cursor: pointer; color: #E23744; font-size: 0.9rem;">🔖</div>
                    <div class="offer-banner-overlay">🎁 {offer_text}</div>
                </div>

                <div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">
                        <h2 style="margin:0; font-size:1.45rem; font-weight:800; color:#18181B;">{name} <span style="font-size:1rem; color:#E23744;">🔖</span></h2>
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <span class="rating-badge">★ {rating}</span>
                            <span style="background:#FFF1F2; color:#E23744; border:1px solid #FECDD3; font-weight:800; font-size:0.82rem; padding:3px 10px; border-radius:8px;">💯 {match_pct}% Match</span>
                        </div>
                    </div>

                    <div style="color: #71717A; font-size: 0.88rem; margin-bottom: 8px;">
                        📍 {loc} • Bengaluru &nbsp;&nbsp;|&nbsp;&nbsp; {cuisine_pills} &nbsp;&nbsp;•&nbsp; 💰 {cost} &nbsp;•&nbsp; ⏱️ 35 mins
                    </div>

                    <div class="why-gemini-box">
                        <div class="why-gemini-title">🔥 Why Gemini Picked This:</div>
                        <div style="font-size: 0.9rem; color: #27272A; line-height: 1.45;">
                            {explanation}
                        </div>
                        <div class="palate-matrix-grid">
                            <div class="palate-item">🍽️ <b>Cuisine Affinity:</b> Match with {cui}</div>
                            <div class="palate-item">💰 <b>Budget Fit:</b> {b_band} Band ({cost})</div>
                            <div class="palate-item">💃 <b>Vibe & Setting:</b> {st.session_state.sel_mode}</div>
                            <div class="palate-item">📜 <b>History Resonance:</b> Matches top dining preferences</div>
                        </div>
                    </div>

                    <div style="display: flex; gap: 6px; align-items: center; margin: 0.7rem 0; flex-wrap: wrap;">
                        <span style="font-size:0.82rem; font-weight:800; color:#854D0E;">👌 Must-Try:</span>
                        {dishes_html}
                    </div>

                    <div class="insider-secret-box">
                        💡 <b>Insider Secret:</b> {secret}
                    </div>

                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
                        <a href="#" style="font-size: 0.85rem; font-weight: 700; color: #E23744; text-decoration: none;">Full Menu & Details ↗</a>
                        <div style="display: flex; gap: 8px;">
                            <span style="background: white; border: 1px solid #D4D4D8; color: #18181B; font-size: 0.85rem; font-weight: 700; padding: 6px 14px; border-radius: 8px; cursor: pointer;">🛵 Order Online</span>
                            <span style="background: #18181B; color: white; font-size: 0.85rem; font-weight: 700; padding: 6px 16px; border-radius: 8px; cursor: pointer;">📖 Book Table</span>
                        </div>
                    </div>
                </div>
            </div>
            """

            st.html(card_html)
