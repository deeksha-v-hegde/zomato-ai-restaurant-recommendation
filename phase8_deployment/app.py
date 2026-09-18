"""Phase 8: Streamlit Deployment Application.

A modern, consumer-grade AI Restaurant Finder frontend.
Preserves all existing backend logic, pipelines, dataset handling, and Groq integration.
"""

from __future__ import annotations

import hashlib
import html
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from phase2_user_input.exceptions import PreferenceValidationError
from phase6_backend_api.app.schemas.recommend import RecommendationCard, RecommendResponse
from phase6_backend_api.app.services.recommendation_service import validation_error_details
from phase8_deployment.config import APP_ICON, APP_TITLE
from phase8_deployment.pipeline import (
    AppContext,
    SearchInput,
    decode_display_text,
    load_runtime,
    resolve_location_for_search,
    run_search,
)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title=f"{APP_TITLE} · AI Restaurant Finder",
    page_icon=APP_ICON,
    layout="centered",
    initial_sidebar_state="expanded",
)


# --- CENTRALIZED STYLING & DESIGN SYSTEM ---
def inject_custom_css() -> None:
    """Inject modern, restrained CSS for an AI consumer food discovery product."""
    st.html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --brand-primary: #E23744;
            --brand-primary-hover: #CB202D;
            --brand-light: #FFF5F5;
            --brand-border: #FECDD3;
            --bg-page: #FAFAF9;
            --surface-card: #FFFFFF;
            --text-heading: #18181B;
            --text-body: #3F3F46;
            --text-muted: #71717A;
            --border-subtle: #E4E4E7;
            --rating-green: #15803D;
            --rating-bg: #DCFCE7;
        }

        /* Base Typography */
        html, body, [class*="css"] {
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
            color: var(--text-body);
        }

        .stApp {
            background-color: var(--bg-page);
        }

        .block-container {
            max-width: 860px !important;
            padding-top: 1.5rem !important;
            padding-bottom: 4rem !important;
        }

        /* Top Brand Header */
        .brand-header-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.25rem 0 1rem 0;
            border-bottom: 1px solid var(--border-subtle);
            margin-bottom: 1.25rem;
        }

        .brand-logo-area {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .brand-logo-icon {
            font-size: 1.5rem;
            background: #FFF1F2;
            border: 1px solid var(--brand-border);
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .brand-product-title {
            font-size: 1.25rem;
            font-weight: 800;
            color: var(--text-heading);
            letter-spacing: -0.02em;
            line-height: 1.2;
        }

        .brand-product-sub {
            font-size: 0.8rem;
            color: var(--text-muted);
            font-weight: 500;
        }

        .ai-badge-pill {
            background: #FFF1F2;
            color: var(--brand-primary);
            border: 1px solid var(--brand-border);
            font-size: 0.72rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 20px;
            letter-spacing: 0.03em;
        }

        /* Compact Hero Section */
        .hero-wrap {
            text-align: left;
            margin-bottom: 1.25rem;
        }

        .hero-title {
            font-size: 2.1rem;
            font-weight: 800;
            color: var(--text-heading);
            letter-spacing: -0.03em;
            line-height: 1.25;
            margin-bottom: 0.35rem;
        }

        .hero-desc {
            font-size: 0.95rem;
            color: var(--text-muted);
            line-height: 1.5;
            max-width: 680px;
        }

        /* Search Panel Container */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--surface-card) !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: 16px !important;
            padding: 1.25rem 1.5rem !important;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.03) !important;
            margin-bottom: 1.5rem !important;
        }

        .section-header-tag {
            font-size: 0.76rem;
            font-weight: 800;
            color: #4B5563;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .craving-title {
            font-size: 0.76rem;
            font-weight: 800;
            color: var(--brand-primary);
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin: 0.6rem 0 0.35rem 0;
        }

        /* Full-Width Primary CTA */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #E23744 0%, #EA580C 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
            border-radius: 12px !important;
            padding: 0.65rem 1.5rem !important;
            box-shadow: 0 4px 14px rgba(226, 55, 68, 0.25) !important;
            transition: all 0.2s ease !important;
            margin-top: 0.4rem !important;
        }

        div.stButton > button[kind="primary"]:hover {
            box-shadow: 0 6px 20px rgba(226, 55, 68, 0.35) !important;
            transform: translateY(-1px) !important;
        }

        /* Search Summary Header */
        .picks-header-title {
            font-size: 1.3rem;
            font-weight: 800;
            color: var(--text-heading);
            letter-spacing: -0.02em;
            margin-bottom: 0.15rem;
        }

        .picks-header-sub {
            font-size: 0.88rem;
            color: var(--text-muted);
            margin-bottom: 0.75rem;
        }

        .summary-pill-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
            margin-bottom: 1.25rem;
        }

        .summary-badge {
            background: #FFFFFF;
            border: 1px solid var(--border-subtle);
            color: #27272A;
            font-size: 0.82rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }

        /* Restaurant Cards */
        .recommendation-card {
            background: var(--surface-card);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            padding: 0;
            margin-bottom: 1.25rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            overflow: hidden;
        }

        .recommendation-card:hover {
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
            transform: translateY(-2px);
        }

        .top-tier-card {
            border: 1.5px solid var(--brand-border);
            box-shadow: 0 4px 18px rgba(226, 55, 68, 0.08);
            background: #FFFFFF;
        }

        .card-img-wrap {
            width: 100%;
            height: 200px;
            overflow: hidden;
            position: relative;
            background-color: #F4F4F5;
        }

        .card-restaurant-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center;
            display: block;
            border-top-left-radius: 13px;
            border-top-right-radius: 13px;
            transition: transform 0.3s ease;
        }

        .recommendation-card:hover .card-restaurant-img {
            transform: scale(1.02);
        }

        .card-content-wrap {
            padding: 1.15rem 1.35rem 1.25rem 1.35rem;
        }

        .card-top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.35rem;
        }

        .card-rank-title-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .rank-label-top {
            color: var(--brand-primary);
            font-weight: 800;
            font-size: 0.88rem;
            letter-spacing: -0.01em;
        }

        .rank-label-normal {
            color: var(--text-muted);
            font-weight: 700;
            font-size: 0.88rem;
        }

        .restaurant-title {
            font-size: 1.25rem;
            font-weight: 800;
            color: var(--text-heading);
            letter-spacing: -0.02em;
            margin: 0;
            line-height: 1.3;
        }

        .rating-badge {
            background: var(--rating-green);
            color: #FFFFFF;
            font-size: 0.82rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            gap: 3px;
        }

        .card-subtext {
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-bottom: 0.75rem;
        }

        /* AI Reasoning Box */
        .ai-reasoning-container {
            background: var(--brand-light);
            border: 1px solid #FFE4E6;
            border-radius: 10px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.75rem;
        }

        .ai-reasoning-title {
            font-size: 0.76rem;
            font-weight: 800;
            color: var(--brand-primary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.3rem;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .ai-reasoning-body {
            font-size: 0.9rem;
            color: #27272A;
            line-height: 1.5;
            font-weight: 450;
        }

        /* Card Tags Footer */
        .card-tags-footer {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 6px;
        }

        .tag-pill {
            background: #F4F4F5;
            color: #3F3F46;
            border: 1px solid #E4E4E7;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 6px;
        }

        /* Empty State */
        .empty-state-wrap {
            background: #FFFFFF;
            border: 1px dashed #D1D5DB;
            border-radius: 14px;
            padding: 2.5rem 1.5rem;
            text-align: center;
            margin: 1.5rem 0;
        }

        .empty-state-icon {
            font-size: 2.2rem;
            margin-bottom: 0.5rem;
        }

        .empty-state-heading {
            font-size: 1.15rem;
            font-weight: 800;
            color: var(--text-heading);
            margin-bottom: 0.35rem;
        }

        .empty-state-sub {
            font-size: 0.9rem;
            color: var(--text-muted);
            max-width: 460px;
            margin: 0 auto;
            line-height: 1.45;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid var(--border-subtle) !important;
        }

        .sidebar-brand-title {
            font-size: 1.15rem;
            font-weight: 800;
            color: var(--text-heading);
        }

        .sidebar-brand-sub {
            font-size: 0.78rem;
            color: var(--text-muted);
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border-subtle);
        }

        .step-item {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            margin-bottom: 0.6rem;
            font-size: 0.85rem;
            color: var(--text-body);
            line-height: 1.4;
        }

        .step-num {
            font-weight: 800;
            color: var(--brand-primary);
            font-size: 0.8rem;
            min-width: 20px;
        }
        </style>
        """
    )


# --- RUNTIME LOADER ---
@st.cache_resource(show_spinner="Connecting to dining catalog...")
def get_runtime() -> AppContext:
    return load_runtime()


def _index_or_zero(items: list[str], value: str) -> int:
    try:
        return items.index(value)
    except ValueError:
        return 0


# --- UI COMPONENT FUNCTIONS ---
def render_header() -> None:
    """Render compact brand header."""
    st.html(
        """
        <div class="brand-header-row">
            <div class="brand-logo-area">
                <div class="brand-logo-icon">🍽️</div>
                <div>
                    <div class="brand-product-title">AI Restaurant Finder</div>
                    <div class="brand-product-sub">Personalized dining recommendations</div>
                </div>
            </div>
            <div>
                <span class="ai-badge-pill">✨ AI-POWERED</span>
            </div>
        </div>
        """
    )


def render_hero() -> None:
    """Render compact customer-focused hero section."""
    st.html(
        """
        <div class="hero-wrap">
            <div class="hero-title">Find a restaurant you'll actually love.</div>
            <div class="hero-desc">
                Tell us where you're dining, what you're craving, and your budget. We'll find restaurants that match.
            </div>
        </div>
        """
    )


def reset_search_preferences(default_location: str) -> None:
    """Reset all search preference widgets and results in session state."""
    st.session_state["pref_location"] = default_location
    st.session_state["pref_budget"] = "Medium (₹500 - ₹1,500)"
    st.session_state["pref_cuisine"] = "North Indian"
    st.session_state["pref_min_rating"] = "4.0+ Stars"
    st.session_state["pref_additional"] = ""
    st.session_state["search_result"] = None
    st.session_state["search_error"] = None
    st.session_state["last_search_summary"] = None
    st.session_state["last_exception"] = None


def set_craving(text: str) -> None:
    """Set the additional preferences craving text."""
    st.session_state["pref_additional"] = text


def render_sidebar(ctx: AppContext) -> None:
    """Render compact, product-level sidebar."""
    with st.sidebar:
        st.html(
            """
            <div class="sidebar-brand-title">🍽️ AI Restaurant Finder</div>
            <div class="sidebar-brand-sub">Personalized dining recommendations</div>
            """
        )

        default_location = (
            "Koramangala 5th Block"
            if "Koramangala 5th Block" in ctx.catalog.locations
            else ctx.catalog.locations[0]
        )
        st.button(
            "🔄 Reset Search Preferences",
            use_container_width=True,
            on_click=reset_search_preferences,
            args=(default_location,),
            key="btn_reset_preferences",
        )

        with st.expander("ℹ️ About this project", expanded=False):
            st.caption(
                "Discover curated restaurants in Bengaluru tailored to your dining vibe, cuisine cravings, budget, and ratings powered by AI."
            )


def render_quick_inspiration() -> None:
    """Render compact pill/chip buttons for one-click cravings."""
    st.html("<div class='craving-title'>✨ TRY A CRAVING</div>")
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)

    q_col1.button(
        "🌃 Rooftop & Drinks",
        use_container_width=True,
        on_click=set_craving,
        args=("rooftop terrace with city views and craft cocktails",),
        key="chip_rooftop",
    )
    q_col2.button(
        "🍗 Butter Chicken",
        use_container_width=True,
        on_click=set_craving,
        args=("authentic rich butter chicken, garlic naan and family seating",),
        key="chip_butter_chicken",
    )
    q_col3.button(
        "☕ Cozy Cafe",
        use_container_width=True,
        on_click=set_craving,
        args=("cozy quiet cafe with artisan coffee and gourmet pasta",),
        key="chip_cozy_cafe",
    )
    q_col4.button(
        "🥘 Ghee Roast Dosa",
        use_container_width=True,
        on_click=set_craving,
        args=("crispy ghee roast masala dosa with fresh coconut chutney",),
        key="chip_ghee_roast_dosa",
    )


def render_search_panel(ctx: AppContext) -> bool:
    """Render the structured preference panel with 2-column layout."""
    loc_options = ctx.catalog.locations
    cui_options = ctx.catalog.cuisines

    budget_options = [
        "Medium (₹500 - ₹1,500)",
        "Budget-Friendly (< ₹500)",
        "Fine Dining (₹1,500+)",
    ]

    rating_options = [
        "4.0+ Stars",
        "4.5+ Stars",
        "3.5+ Stars",
        "Any Rating",
    ]

    with st.container(border=True):
        # Section 1: Where Are You Dining?
        st.html("<div class='section-header-tag'>📍 WHERE ARE YOU DINING?</div>")
        r1_col1, r1_col2 = st.columns(2)
        with r1_col1:
            st.selectbox(
                "Location",
                options=loc_options,
                key="pref_location",
            )

        with r1_col2:
            st.selectbox(
                "Budget",
                options=budget_options,
                key="pref_budget",
            )

        st.html("<div style='height: 4px;'></div>")

        # Section 2: What Are You In The Mood For?
        st.html("<div class='section-header-tag'>🍴 WHAT ARE YOU IN THE MOOD FOR?</div>")
        r2_col1, r2_col2 = st.columns(2)
        with r2_col1:
            st.selectbox(
                "Cuisine",
                options=cui_options,
                key="pref_cuisine",
            )

        with r2_col2:
            st.selectbox(
                "Minimum Rating",
                options=rating_options,
                key="pref_min_rating",
            )

        st.html("<div style='height: 4px;'></div>")

        # Section 3: Anything Else?
        st.html("<div class='section-header-tag'>✨ ANYTHING ELSE?</div>")
        st.text_input(
            "Additional Preferences",
            placeholder="e.g., quiet romantic dinner, authentic woodfired pizza, outdoor garden seating...",
            label_visibility="collapsed",
            key="pref_additional",
        )

        # Quick inspiration chips
        render_quick_inspiration()

        st.html("<div style='height: 8px;'></div>")

        # Primary Call to Action
        submitted = st.button(
            "✨ Find My Restaurants",
            type="primary",
            use_container_width=True,
            key="btn_find_restaurants",
        )

    return submitted


def _format_cost(raw_cost: str) -> str:
    """Format cost cleanly without duplicate currency symbols or 'for two' text."""
    clean = raw_cost.replace("for two", "").replace("for 2", "").strip()
    clean = clean.replace("₹", "").strip()
    return f"₹{clean} for two" if clean else "N/A"


def render_search_summary(
    location: str,
    budget_label: str,
    cuisine: str,
    rating_label: str,
    count: int,
    used_fallback: bool = False,
) -> None:
    """Render clean search summary above recommendation results."""
    # Clean budget display string
    if "Budget-Friendly" in budget_label or "<" in budget_label:
        budget_disp = "< ₹500"
    elif "Fine Dining" in budget_label or "1,500+" in budget_label:
        budget_disp = "₹1,500+"
    else:
        budget_disp = "₹500–₹1,500"

    # Clean rating display string
    rating_disp = rating_label.replace(" Stars", "")

    st.html(
        f"""
        <div class="picks-header-container" style="margin-top: 1rem; margin-bottom: 0.5rem;">
            <div class="picks-header-title">✨ YOUR AI RESTAURANT PICKS</div>
            <div class="picks-header-sub">{count} restaurant{"s" if count != 1 else ""} matched your preferences</div>
            <div class="summary-pill-container">
                <span class="summary-badge">📍 {html.escape(location)}</span>
                <span class="summary-badge">🍛 {html.escape(cuisine)}</span>
                <span class="summary-badge">💰 {html.escape(budget_disp)}</span>
                <span class="summary-badge">⭐ {html.escape(rating_disp)}</span>
            </div>
        </div>
        """
    )


DEFAULT_FALLBACK_IMAGE = (
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80"
)

# Curated brand photography for popular Bangalore dining icons and chains
_BRAND_IMAGE_MAP: dict[str, str] = {
    "meghana": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=800&q=80",
    "eat.fit": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80",
    "eat fit": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80",
    "truffles": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=800&q=80",
    "toit": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=800&q=80",
    "vidyarthi": "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=800&q=80",
    "mtr": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&w=800&q=80",
    "mavalli": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&w=800&q=80",
    "empire": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=800&q=80",
    "chai point": "https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=800&q=80",
    "third wave": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=800&q=80",
    "glen's": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=800&q=80",
    "glens": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=800&q=80",
    "corner house": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?auto=format&fit=crop&w=800&q=80",
    "onesta": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=800&q=80",
    "behrouz": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=800&q=80",
    "faasos": "https://images.unsplash.com/photo-1626776876729-bab4369a5a5a?auto=format&fit=crop&w=800&q=80",
    "kfc": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?auto=format&fit=crop&w=800&q=80",
    "five star chicken": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?auto=format&fit=crop&w=800&q=80",
    "mcdonald": "https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=800&q=80",
    "burger king": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=800&q=80",
    "domino": "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?auto=format&fit=crop&w=800&q=80",
    "pizza hut": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=800&q=80",
    "subway": "https://images.unsplash.com/photo-1509722747041-616f39b57569?auto=format&fit=crop&w=800&q=80",
    "cafe coffee day": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=800&q=80",
    "ccd": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=800&q=80",
    "starbucks": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=800&q=80",
    "baskin robbins": "https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?auto=format&fit=crop&w=800&q=80",
    "polar bear": "https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?auto=format&fit=crop&w=800&q=80",
    "a2b": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=800&q=80",
    "adyar ananda": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=800&q=80",
    "kanti sweets": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=800&q=80",
    "barbeque nation": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=800&q=80",
    "california burrito": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=800&q=80",
    "leon grill": "https://images.unsplash.com/photo-1529006557810-274b9b2fc783?auto=format&fit=crop&w=800&q=80",
    "just shawarma": "https://images.unsplash.com/photo-1529006557810-274b9b2fc783?auto=format&fit=crop&w=800&q=80",
    "social": "https://images.unsplash.com/photo-1572116469696-31de0f17cc34?auto=format&fit=crop&w=800&q=80",
    "smoke house deli": "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?auto=format&fit=crop&w=800&q=80",
    "mainland china": "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?auto=format&fit=crop&w=800&q=80",
    "beijing bites": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=800&q=80",
    "chung wah": "https://images.unsplash.com/photo-1525755662778-989d0524087e?auto=format&fit=crop&w=800&q=80",
    "nagarjuna": "https://images.unsplash.com/photo-1610057099443-fde8c4d50f91?auto=format&fit=crop&w=800&q=80",
    "sweet truth": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=800&q=80",
    "sweet chariot": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=800&q=80",
    "just bake": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=800&q=80",
    "amma's pastries": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=800&q=80",
    "drunken monkey": "https://images.unsplash.com/photo-1551024709-8f23befc6f87?auto=format&fit=crop&w=800&q=80",
    "lassi shop": "https://images.unsplash.com/photo-1551024709-8f23befc6f87?auto=format&fit=crop&w=800&q=80",
    "frozen bottle": "https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?auto=format&fit=crop&w=800&q=80",
    "box8": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=800&q=80",
    "petoo": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=800&q=80",
    "mojo pizza": "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?auto=format&fit=crop&w=800&q=80",
    "ovenstory": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=800&q=80",
    "firangi bake": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=800&q=80",
    "the good bowl": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80",
    "rolls on wheels": "https://images.unsplash.com/photo-1626776876729-bab4369a5a5a?auto=format&fit=crop&w=800&q=80",
    "ande ka funda": "https://images.unsplash.com/photo-1626776876729-bab4369a5a5a?auto=format&fit=crop&w=800&q=80",
    "goli vada pav": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=800&q=80",
}

# Rich category pools for cuisine and keyword matching
_CUISINE_IMAGE_POOLS: dict[str, list[str]] = {
    "biryani": [
        "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1631515243349-e0cb75fb8d3a?auto=format&fit=crop&w=800&q=80",
    ],
    "north_indian": [
        "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=800&q=80",
    ],
    "south_indian": [
        "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1630383249896-424e482df921?auto=format&fit=crop&w=800&q=80",
    ],
    "cafe": [
        "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=800&q=80",
    ],
    "italian": [
        "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?auto=format&fit=crop&w=800&q=80",
    ],
    "chinese": [
        "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1525755662778-989d0524087e?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=800&q=80",
    ],
    "fast_food": [
        "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1626776876729-bab4369a5a5a?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?auto=format&fit=crop&w=800&q=80",
    ],
    "bar": [
        "https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1572116469696-31de0f17cc34?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1574096079513-d8259312b785?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=800&q=80",
    ],
    "seafood": [
        "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1579631542720-3a87824fff86?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=800&q=80",
    ],
    "dining": [
        "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80",
    ],
}


def _deterministic_pick(pool: list[str], seed_str: str) -> str:
    """Pick an image deterministically using md5 hash of restaurant name + location."""
    if not pool:
        return DEFAULT_FALLBACK_IMAGE
    h = int(hashlib.md5(seed_str.lower().strip().encode("utf-8")).hexdigest(), 16)
    return pool[h % len(pool)]


def get_restaurant_image(name: str, location: str, cuisines: str) -> str:
    """Resolve a relevant, high-resolution image for a restaurant.

    Uses brand matching first, followed by cuisine and restaurant keyword
    pools with deterministic name+location hashing for visual variety.
    Gracefully falls back to a universal ambient dining image on any failure.
    """
    try:
        norm_name = (name or "").lower().strip()
        norm_loc = (location or "").lower().strip()
        norm_cui = (cuisines or "").lower().strip()
        seed = f"{norm_name}:{norm_loc}"

        # 1. Direct Brand Match
        for brand_key, img_url in _BRAND_IMAGE_MAP.items():
            if brand_key in norm_name:
                return img_url

        # 2. Cuisine / Keyword Category Match
        combined_text = f"{norm_name} {norm_cui}"
        if any(w in combined_text for w in ["biryani", "hyderabadi", "dum biryani", "awadhi"]):
            return _deterministic_pick(_CUISINE_IMAGE_POOLS["biryani"], seed)
        if any(w in combined_text for w in ["dosa", "idli", "south indian", "udupi", "chettinad", "kerala", "tiffin"]):
            return _deterministic_pick(_CUISINE_IMAGE_POOLS["south_indian"], seed)
        if any(w in combined_text for w in ["north indian", "mughlai", "tandoori", "punjabi", "curry", "roti", "paneer"]):
            return _deterministic_pick(_CUISINE_IMAGE_POOLS["north_indian"], seed)
        if any(w in combined_text for w in ["pizza", "pasta", "italian"]):
            return _deterministic_pick(_CUISINE_IMAGE_POOLS["italian"], seed)
        if any(w in combined_text for w in ["chinese", "asian", "thai", "dim sum", "momo", "noodle", "japanese", "sushi"]):
            return _deterministic_pick(_CUISINE_IMAGE_POOLS["chinese"], seed)
        if any(w in combined_text for w in ["cafe", "coffee", "bakery", "dessert", "cake", "pastry", "tea", "waffle", "ice cream"]):
            return _deterministic_pick(_CUISINE_IMAGE_POOLS["cafe"], seed)
        if any(w in combined_text for w in ["burger", "fast food", "roll", "wrap", "sandwich", "shawarma", "snack"]):
            return _deterministic_pick(_CUISINE_IMAGE_POOLS["fast_food"], seed)
        if any(w in combined_text for w in ["brewery", "pub", "bar", "cocktail", "beer", "lounge", "rooftop"]):
            return _deterministic_pick(_CUISINE_IMAGE_POOLS["bar"], seed)
        if any(w in combined_text for w in ["seafood", "fish", "prawn", "crab", "coastal", "mangalorean"]):
            return _deterministic_pick(_CUISINE_IMAGE_POOLS["seafood"], seed)

        # 3. Dining pool fallback with deterministic pick
        return _deterministic_pick(_CUISINE_IMAGE_POOLS["dining"], seed)
    except Exception:
        return DEFAULT_FALLBACK_IMAGE


def render_restaurant_card(item: RecommendationCard, is_top: bool) -> None:
    """Render a single restaurant recommendation card using real returned data."""
    name = decode_display_text(item.name)
    loc = decode_display_text(item.location)
    cui = decode_display_text(item.cuisines)
    rating = decode_display_text(item.rating)
    cost = decode_display_text(item.cost)
    explanation = decode_display_text(item.explanation)
    rank = item.rank

    # Ranking label
    if rank == 1:
        rank_label = '<span class="rank-label-top">#1 Top Pick</span>'
        card_class = "recommendation-card top-tier-card"
    else:
        rank_label = f'<span class="rank-label-normal">#{rank}</span>'
        card_class = "recommendation-card"

    # Budget tier symbol based on item.budget_band
    band = (item.budget_band or "").lower()
    if band == "low":
        tier_symbol = "₹"
    elif band == "high":
        tier_symbol = "₹₹₹"
    else:
        tier_symbol = "₹₹"

    # First cuisine for primary tag
    first_cuisine = cui.split(",")[0].strip() if cui else "Dining"
    formatted_cost = _format_cost(cost)
    img_url = get_restaurant_image(name, loc, cui)

    card_html = f"""
    <div class="{card_class}">
        <div class="card-img-wrap">
            <img
                src="{html.escape(img_url)}"
                alt="{html.escape(name)}"
                class="card-restaurant-img"
                loading="lazy"
                onerror="this.onerror=null;this.src='{DEFAULT_FALLBACK_IMAGE}';"
            />
        </div>

        <div class="card-content-wrap">
            <div class="card-top-bar">
                <div class="card-rank-title-group">
                    {rank_label}
                    <span class="restaurant-title">{html.escape(name)}</span>
                </div>
                <div>
                    <span class="rating-badge">⭐ {html.escape(rating)}</span>
                </div>
            </div>

            <div class="card-subtext">
                {html.escape(cui)} • {html.escape(formatted_cost)}
            </div>

            <div class="ai-reasoning-container">
                <div class="ai-reasoning-title">✨ WHY THIS MATCHES</div>
                <div class="ai-reasoning-body">"{html.escape(explanation)}"</div>
            </div>

            <div class="card-tags-footer">
                <span class="tag-pill">{html.escape(first_cuisine)}</span>
                <span class="tag-pill">⭐ {html.escape(rating)}</span>
                <span class="tag-pill">{html.escape(tier_symbol)}</span>
                <span class="tag-pill">📍 {html.escape(loc)}</span>
            </div>
        </div>
    </div>
    """
    st.html(card_html)


def render_empty_state(case: str, message: str | None = None, hints: list[str] | None = None) -> None:
    """Render clean, friendly empty state."""
    title = "No restaurants matched your search."
    desc = (
        message
        or "Try changing your cuisine, budget, location, or minimum rating."
    )

    hints_html = ""
    if hints:
        hints_items = "".join(f"<li>{html.escape(h)}</li>" for h in hints)
        hints_html = f"<ul style='text-align:left; display:inline-block; margin-top:0.6rem; font-size:0.85rem; color:#4B5563;'>{hints_items}</ul>"

    st.html(
        f"""
        <div class="empty-state-wrap">
            <div class="empty-state-icon">🍽️</div>
            <div class="empty-state-heading">{html.escape(title)}</div>
            <div class="empty-state-sub">{html.escape(desc)}</div>
            {hints_html}
        </div>
        """
    )


# --- CONTROLLER ---
def main() -> None:
    inject_custom_css()

    # Load runtime
    try:
        ctx = get_runtime()
    except Exception as exc:
        st.error(
            "Something went wrong while initializing the restaurant catalog. Please ensure the Phase 1 cache exists.",
            icon=":material/error:",
        )
        with st.expander("Developer details"):
            st.code(str(exc))
        return

    # Session State Initialization
    st.session_state.setdefault(
        "pref_location",
        "Koramangala 5th Block" if "Koramangala 5th Block" in ctx.catalog.locations else ctx.catalog.locations[0],
    )
    st.session_state.setdefault("pref_budget", "Medium (₹500 - ₹1,500)")
    st.session_state.setdefault("pref_cuisine", "North Indian")
    st.session_state.setdefault("pref_min_rating", "4.0+ Stars")
    st.session_state.setdefault("pref_additional", "")

    # Render Sidebar
    render_sidebar(ctx)

    # Render Header & Hero
    render_header()
    render_hero()

    # Render Search Panel
    submitted = render_search_panel(ctx)

    # Execute Search on Submission
    if submitted:
        # Map budget
        if "Budget-Friendly" in st.session_state.pref_budget or "<" in st.session_state.pref_budget:
            budget_key = "low"
        elif "Fine Dining" in st.session_state.pref_budget or "1,500+" in st.session_state.pref_budget:
            budget_key = "high"
        else:
            budget_key = "medium"

        # Map rating
        rating_str = st.session_state.pref_min_rating
        if "4.5+" in rating_str:
            min_rating_val = 4.5
        elif "4.0+" in rating_str:
            min_rating_val = 4.0
        elif "3.5+" in rating_str:
            min_rating_val = 3.5
        else:
            min_rating_val = 0.0

        resolved_loc = resolve_location_for_search(ctx, st.session_state.pref_location, st.session_state.pref_cuisine)

        search_payload = SearchInput(
            location=st.session_state.pref_location,
            budget=budget_key,
            cuisine=st.session_state.pref_cuisine,
            min_rating=min_rating_val,
            additional_preferences=st.session_state.pref_additional.strip() or None,
        )

        try:
            with st.spinner("✨ Finding your best matches..."):
                result = run_search(search_payload)
                st.session_state.search_result = result
                st.session_state.search_error = None
                st.session_state.last_search_summary = {
                    "location": resolved_loc,
                    "budget": st.session_state.pref_budget,
                    "cuisine": st.session_state.pref_cuisine,
                    "rating": st.session_state.pref_min_rating,
                }
        except PreferenceValidationError as exc:
            st.session_state.search_result = None
            st.session_state.search_error = [
                f"{detail.field.capitalize()}: {detail.message}" for detail in validation_error_details(exc)
            ]
        except Exception as exc:
            st.session_state.search_result = None
            st.session_state.search_error = [
                "Something went wrong while finding recommendations. Please try again."
            ]
            st.session_state.last_exception = str(exc)

    # Render Results / Error / Empty States
    search_error = st.session_state.get("search_error")
    search_result: RecommendResponse | None = st.session_state.get("search_result")
    summary_meta = st.session_state.get("last_search_summary")

    if search_error:
        for err in search_error:
            st.error(err, icon="⚠️")
        if st.session_state.get("last_exception"):
            with st.expander("Developer details"):
                st.code(st.session_state.get("last_exception"))

    elif search_result is not None:
        if search_result.state == "no_match" or not search_result.recommendations:
            render_empty_state(
                case="no_match",
                message=search_result.no_match_message,
                hints=search_result.refine_hints,
            )
        else:
            # Summary header above results
            loc = (summary_meta or {}).get("location") or st.session_state.get("pref_location") or "Bengaluru"
            bud = (summary_meta or {}).get("budget") or st.session_state.get("pref_budget") or "Medium"
            cui = (summary_meta or {}).get("cuisine") or st.session_state.get("pref_cuisine") or "All Cuisines"
            rat = (summary_meta or {}).get("rating") or st.session_state.get("pref_min_rating") or "4.0+"
            used_fb = search_result.used_fallback or (search_result.state == "fallback")

            render_search_summary(
                location=loc,
                budget_label=bud,
                cuisine=cui,
                rating_label=rat,
                count=len(search_result.recommendations),
                used_fallback=used_fb,
            )

            # Recommendation Cards
            for idx, card in enumerate(search_result.recommendations):
                render_restaurant_card(card, is_top=(idx == 0))


if __name__ == "__main__":
    main()
