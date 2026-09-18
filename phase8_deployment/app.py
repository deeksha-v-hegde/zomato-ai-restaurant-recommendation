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
    initial_sidebar_state="collapsed",
)


# --- CENTRALIZED STYLING & DESIGN SYSTEM ---
def inject_custom_css() -> None:
    """Inject modern, premium light-theme CSS for an AI consumer food discovery product."""
    st.html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        :root {
            --brand-primary: #E11D48;
            --brand-primary-hover: #BE123C;
            --brand-light: #FFF1F2;
            --brand-border: #FECDD3;
            --bg-page: #F8FAFC;
            --surface-card: #FFFFFF;
            --text-heading: #0F172A;
            --text-body: #334155;
            --text-muted: #64748B;
            --border-subtle: #E2E8F0;
            --rating-green: #059669;
            --rating-bg: #DCFCE7;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.04);
            --shadow-md: 0 4px 14px -2px rgba(0, 0, 0, 0.05), 0 2px 6px -1px rgba(0, 0, 0, 0.02);
            --shadow-lg: 0 12px 28px -4px rgba(0, 0, 0, 0.08), 0 4px 10px -2px rgba(0, 0, 0, 0.03);
        }

        /* Base Typography */
        html, body, [class*="css"] {
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
            color: var(--text-body);
            -webkit-font-smoothing: antialiased;
        }

        .stApp {
            background-color: var(--bg-page);
        }

        header[data-testid="stHeader"] {
            background-color: transparent !important;
            z-index: 1 !important;
        }

        .block-container {
            max-width: 900px !important;
            padding-top: 4.5rem !important;
            padding-bottom: 4.5rem !important;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-top: 4rem !important;
            }
            .hero-title {
                font-size: 1.75rem !important;
            }
        }

        /* Top Brand Header */
        .brand-header-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.25rem 0 1.15rem 0;
            border-bottom: 1px solid var(--border-subtle);
            margin-bottom: 1.5rem;
        }

        .brand-logo-area {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-logo-icon {
            font-size: 1.5rem;
            background: linear-gradient(135deg, #FFF1F2 0%, #FFE4E6 100%);
            border: 1px solid var(--brand-border);
            width: 44px;
            height: 44px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 6px rgba(225, 29, 72, 0.08);
        }

        .brand-product-title {
            font-size: 1.3rem;
            font-weight: 850;
            color: var(--text-heading);
            letter-spacing: -0.025em;
            line-height: 1.2;
        }

        .brand-product-sub {
            font-size: 0.82rem;
            color: var(--text-muted);
            font-weight: 500;
        }

        .ai-badge-pill {
            background: #FFF1F2;
            color: var(--brand-primary);
            border: 1px solid var(--brand-border);
            font-size: 0.74rem;
            font-weight: 750;
            padding: 4px 12px;
            border-radius: 20px;
            letter-spacing: 0.04em;
            box-shadow: 0 1px 3px rgba(225, 29, 72, 0.06);
        }

        /* Compact Hero Section */
        .hero-wrap {
            text-align: left;
            margin-bottom: 1.5rem;
        }

        .hero-badge-tag {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 750;
            color: var(--brand-primary);
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }

        .hero-title {
            font-size: 2.25rem;
            font-weight: 850;
            color: var(--text-heading);
            letter-spacing: -0.035em;
            line-height: 1.2;
            margin-bottom: 0.5rem;
        }

        .hero-title-gradient {
            background: linear-gradient(135deg, #E11D48 0%, #EA580C 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero-desc {
            font-size: 0.96rem;
            color: var(--text-muted);
            line-height: 1.55;
            max-width: 720px;
        }

        /* Search Panel Container */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--surface-card) !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: 18px !important;
            padding: 1.5rem 1.65rem !important;
            box-shadow: var(--shadow-md) !important;
            margin-bottom: 1.5rem !important;
        }

        .section-header-tag {
            font-size: 0.76rem;
            font-weight: 800;
            color: #475569;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .craving-title {
            font-size: 0.74rem;
            font-weight: 800;
            color: var(--brand-primary);
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin: 0.75rem 0 0.4rem 0;
        }

        /* Streamlit Input & Selectbox Styling */
        div[data-baseweb="select"] > div {
            background-color: #F8FAFC !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: 10px !important;
            transition: all 0.15s ease !important;
        }

        div[data-baseweb="select"] > div:hover {
            border-color: #CBD5E1 !important;
            background-color: #FFFFFF !important;
        }

        div[data-baseweb="select"] > div:focus-within {
            border-color: var(--brand-primary) !important;
            box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.12) !important;
            background-color: #FFFFFF !important;
        }

        div[data-baseweb="input"] > div {
            background-color: #F8FAFC !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: 10px !important;
            transition: all 0.15s ease !important;
        }

        div[data-baseweb="input"] > div:hover {
            border-color: #CBD5E1 !important;
            background-color: #FFFFFF !important;
        }

        div[data-baseweb="input"] > div:focus-within {
            border-color: var(--brand-primary) !important;
            box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.12) !important;
            background-color: #FFFFFF !important;
        }

        /* Quick Craving Buttons */
        div.stButton > button[key^="chip_"] {
            background: #F8FAFC !important;
            color: #334155 !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: 10px !important;
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            padding: 0.45rem 0.65rem !important;
            transition: all 0.18s ease !important;
            box-shadow: var(--shadow-sm) !important;
        }

        div.stButton > button[key^="chip_"]:hover {
            border-color: var(--brand-border) !important;
            color: var(--brand-primary) !important;
            background: #FFF1F2 !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 10px rgba(225, 29, 72, 0.08) !important;
        }

        /* Full-Width Primary CTA */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #E11D48 0%, #EA580C 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            font-weight: 750 !important;
            font-size: 1.02rem !important;
            letter-spacing: -0.01em !important;
            border-radius: 12px !important;
            padding: 0.75rem 1.5rem !important;
            box-shadow: 0 4px 16px rgba(225, 29, 72, 0.28) !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            margin-top: 0.5rem !important;
        }

        div.stButton > button[kind="primary"]:hover {
            box-shadow: 0 8px 24px rgba(225, 29, 72, 0.38) !important;
            transform: translateY(-2px) !important;
        }

        div.stButton > button[kind="primary"]:active {
            transform: translateY(0px) !important;
        }

        /* Search Summary Header */
        .picks-header-title {
            font-size: 1.35rem;
            font-weight: 850;
            color: var(--text-heading);
            letter-spacing: -0.025em;
            margin-bottom: 0.2rem;
        }

        .picks-header-sub {
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-bottom: 0.85rem;
        }

        .summary-pill-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
            margin-bottom: 1.35rem;
        }

        .summary-badge {
            background: #FFFFFF;
            border: 1px solid var(--border-subtle);
            color: #1E293B;
            font-size: 0.82rem;
            font-weight: 600;
            padding: 5px 12px;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            box-shadow: var(--shadow-sm);
        }

        /* Restaurant Cards */
        .recommendation-card {
            background: var(--surface-card);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            padding: 0;
            margin-bottom: 1.35rem;
            box-shadow: var(--shadow-sm);
            transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease;
            overflow: hidden;
        }

        .recommendation-card:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-3px);
            border-color: #CBD5E1;
        }

        .top-tier-card {
            border: 1.5px solid var(--brand-border);
            box-shadow: 0 6px 20px rgba(225, 29, 72, 0.08);
            background: #FFFFFF;
        }

        .top-tier-card:hover {
            box-shadow: 0 12px 30px rgba(225, 29, 72, 0.14);
            border-color: #FDA4AF;
        }

        .card-img-wrap {
            width: 100%;
            height: 165px;
            overflow: hidden;
            position: relative;
            background-color: #F1F5F9;
        }

        .card-restaurant-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center;
            display: block;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
            transition: transform 0.4s ease;
        }

        .recommendation-card:hover .card-restaurant-img {
            transform: scale(1.03);
        }

        .card-content-wrap {
            padding: 1.25rem 1.45rem 1.35rem 1.45rem;
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
            background: #FFF1F2;
            border: 1px solid var(--brand-border);
            font-weight: 800;
            font-size: 0.78rem;
            letter-spacing: 0.03em;
            padding: 2px 8px;
            border-radius: 6px;
            text-transform: uppercase;
        }

        .rank-label-normal {
            color: var(--text-muted);
            background: #F1F5F9;
            border: 1px solid #E2E8F0;
            font-weight: 750;
            font-size: 0.78rem;
            padding: 2px 8px;
            border-radius: 6px;
        }

        .restaurant-title {
            font-size: 1.3rem;
            font-weight: 800;
            color: var(--text-heading);
            letter-spacing: -0.025em;
            margin: 0;
            line-height: 1.3;
        }

        .rating-badge {
            background: var(--rating-green);
            color: #FFFFFF;
            font-size: 0.82rem;
            font-weight: 750;
            padding: 3px 9px;
            border-radius: 7px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            box-shadow: 0 1px 3px rgba(5, 150, 105, 0.25);
        }

        .card-subtext {
            color: var(--text-muted);
            font-size: 0.88rem;
            font-weight: 500;
            margin-bottom: 0.85rem;
        }

        /* AI Reasoning Box */
        .ai-reasoning-container {
            background: linear-gradient(135deg, #FFF1F2 0%, #FFF5F5 100%);
            border: 1px solid #FFE4E6;
            border-radius: 12px;
            padding: 0.95rem 1.15rem;
            margin-bottom: 0.85rem;
        }

        .ai-reasoning-title {
            font-size: 0.74rem;
            font-weight: 800;
            color: var(--brand-primary);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 0.35rem;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .ai-reasoning-body {
            font-size: 0.91rem;
            color: #1E293B;
            line-height: 1.55;
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
            background: #F8FAFC;
            color: #334155;
            border: 1px solid #E2E8F0;
            font-size: 0.76rem;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 7px;
        }

        /* Empty State */
        .empty-state-wrap {
            background: #FFFFFF;
            border: 1px dashed #CBD5E1;
            border-radius: 16px;
            padding: 2.75rem 1.5rem;
            text-align: center;
            margin: 1.5rem 0;
            box-shadow: var(--shadow-sm);
        }

        .empty-state-icon {
            font-size: 2.4rem;
            margin-bottom: 0.6rem;
        }

        .empty-state-heading {
            font-size: 1.2rem;
            font-weight: 800;
            color: var(--text-heading);
            margin-bottom: 0.35rem;
        }

        .empty-state-sub {
            font-size: 0.92rem;
            color: var(--text-muted);
            max-width: 480px;
            margin: 0 auto;
            line-height: 1.5;
        }

        /* Completely Hide Sidebar and Collapse Toggle */
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        section[data-testid="stSidebar"] {
            display: none !important;
        }

        /* Unobtrusive Reset Button in Search Panel Header */
        div[data-testid="stButton"] button[key="btn_reset_preferences"],
        button[key="btn_reset_preferences"] {
            background-color: #F8FAFC !important;
            color: var(--text-muted) !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: 8px !important;
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            padding: 0.3rem 0.75rem !important;
            transition: all 0.18s ease !important;
        }

        div[data-testid="stButton"] button[key="btn_reset_preferences"]:hover,
        button[key="btn_reset_preferences"]:hover {
            color: var(--brand-primary) !important;
            border-color: var(--brand-border) !important;
            background: #FFF1F2 !important;
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
            <div class="hero-badge-tag">🎯 PERSONALIZED DINING SEARCH</div>
            <div class="hero-title">Find a restaurant you'll <span class="hero-title-gradient">actually love.</span></div>
            <div class="hero-desc">
                Tell us where you're dining, what you're craving, and your budget. Our AI finds the best matches and explains why they fit.
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

    default_location = (
        "Koramangala 5th Block"
        if "Koramangala 5th Block" in ctx.catalog.locations
        else ctx.catalog.locations[0]
    )

    with st.container(border=True):
        # Section 1 Header + Unobtrusive Reset Button in Top-Right
        hdr_col1, hdr_col2 = st.columns([3, 1.3])
        with hdr_col1:
            st.html("<div class='section-header-tag' style='margin-top: 6px;'>📍 WHERE ARE YOU DINING?</div>")
        with hdr_col2:
            st.button(
                "🔄 Reset Preferences",
                use_container_width=True,
                on_click=reset_search_preferences,
                args=(default_location,),
                key="btn_reset_preferences",
                help="Reset all search fields to default values",
            )

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

# Curated location-specific restaurant photos (exterior/interior/storefront)
# Tuples of (restaurant_name_needle, location_needle, image_url)
_RESTAURANT_LOCATION_IMAGE_MAP: list[tuple[str, str, str]] = [
    # Koramangala 5th Block top picks
    (
        "meghana",
        "koramangala",
        "https://b.zmtcdn.com/data/pictures/1/50691/92d9b4053ef0965120828b4fa4eecc3b.jpg",
    ),
    (
        "eat.fit",
        "koramangala",
        "https://dineout-media-assets.swiggy.com/swiggy/image/upload/fl_lossy,f_auto,q_auto,w_600,h_468/v1681158827/4ce6bc0591e3ecb2030079c40d634862.jpg",
    ),
    (
        "eat fit",
        "koramangala",
        "https://dineout-media-assets.swiggy.com/swiggy/image/upload/fl_lossy,f_auto,q_auto,w_600,h_468/v1681158827/4ce6bc0591e3ecb2030079c40d634862.jpg",
    ),
    (
        "box8",
        "koramangala",
        "https://content.jdmagicbox.com/comp/def_content_category/box8/136668172-1545564928962639-5637207615065103483-n-box8-995-p022i.jpg",
    ),
    (
        "desipun",
        "koramangala",
        "https://content.jdmagicbox.com/v2/comp/bangalore/m4/080pxx80.xx80.180918120548.y6m4/catalogue/desipun-koramangala-bangalore-north-indian-restaurants-9t5bu665nu.jpg",
    ),
    (
        "bathinda junction",
        "koramangala",
        "https://b.zmtcdn.com/data/pictures/chains/8/59648/ad6eb9fe407f0099b94bf3f6904bef76.jpg",
    ),
    (
        "bathinda",
        "koramangala",
        "https://b.zmtcdn.com/data/pictures/chains/8/59648/ad6eb9fe407f0099b94bf3f6904bef76.jpg",
    ),
    (
        "toit",
        "indiranagar",
        "https://content3.jdmagicbox.com/v2/comp/bangalore/u1/080pxx80.xx80.101215095310.f5u1/catalogue/toit-brew-pub-indira-nagar-2nd-stage-bangalore-microbrewery-pubs-30mc81k.jpg",
    ),
    (
        "truffles",
        "koramangala",
        "https://content3.jdmagicbox.com/v2/comp/bangalore/i2/080pxx80.xx80.131226124024.h2i2/catalogue/truffles-koramangala-5th-block-bangalore-restaurants-9enq86.jpg",
    ),
    (
        "vidyarthi bhavan",
        "basavanagudi",
        "https://thumb.wikimedia.org/wikipedia/commons/thumb/9/9d/VidyarthiBhavanEntrance.jpg/960px-VidyarthiBhavanEntrance.jpg",
    ),
    (
        "mtr",
        "lalbagh",
        "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a8/Mavalli_Tiffin_Room_%286%29%2C_Lalbagh_Road%2C_Bengaluru.jpg/1280px-Mavalli_Tiffin_Room_%286%29%2C_Lalbagh_Road%2C_Bengaluru.jpg",
    ),
]

# Curated actual restaurant exterior/interior/official brand photography
_BRAND_IMAGE_MAP: dict[str, str] = {
    "meghana": "https://b.zmtcdn.com/data/pictures/1/50691/92d9b4053ef0965120828b4fa4eecc3b.jpg",
    "eat.fit": "https://dineout-media-assets.swiggy.com/swiggy/image/upload/fl_lossy,f_auto,q_auto,w_600,h_468/v1681158827/4ce6bc0591e3ecb2030079c40d634862.jpg",
    "eat fit": "https://dineout-media-assets.swiggy.com/swiggy/image/upload/fl_lossy,f_auto,q_auto,w_600,h_468/v1681158827/4ce6bc0591e3ecb2030079c40d634862.jpg",
    "box8": "https://content.jdmagicbox.com/comp/def_content_category/box8/136668172-1545564928962639-5637207615065103483-n-box8-995-p022i.jpg",
    "desipun": "https://content.jdmagicbox.com/v2/comp/bangalore/m4/080pxx80.xx80.180918120548.y6m4/catalogue/desipun-koramangala-bangalore-north-indian-restaurants-9t5bu665nu.jpg",
    "bathinda junction": "https://b.zmtcdn.com/data/pictures/chains/8/59648/ad6eb9fe407f0099b94bf3f6904bef76.jpg",
    "bathinda": "https://b.zmtcdn.com/data/pictures/chains/8/59648/ad6eb9fe407f0099b94bf3f6904bef76.jpg",
    "toit": "https://content3.jdmagicbox.com/v2/comp/bangalore/u1/080pxx80.xx80.101215095310.f5u1/catalogue/toit-brew-pub-indira-nagar-2nd-stage-bangalore-microbrewery-pubs-30mc81k.jpg",
    "truffles": "https://content3.jdmagicbox.com/v2/comp/bangalore/i2/080pxx80.xx80.131226124024.h2i2/catalogue/truffles-koramangala-5th-block-bangalore-restaurants-9enq86.jpg",
    "vidyarthi": "https://thumb.wikimedia.org/wikipedia/commons/thumb/9/9d/VidyarthiBhavanEntrance.jpg/960px-VidyarthiBhavanEntrance.jpg",
    "mtr": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a8/Mavalli_Tiffin_Room_%286%29%2C_Lalbagh_Road%2C_Bengaluru.jpg/1280px-Mavalli_Tiffin_Room_%286%29%2C_Lalbagh_Road%2C_Bengaluru.jpg",
    "mavalli": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a8/Mavalli_Tiffin_Room_%286%29%2C_Lalbagh_Road%2C_Bengaluru.jpg/1280px-Mavalli_Tiffin_Room_%286%29%2C_Lalbagh_Road%2C_Bengaluru.jpg",
    "barbeque nation": "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f0/Barbeque_Nation_Park_Street.jpg/960px-Barbeque_Nation_Park_Street.jpg",
    "kfc": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a8/Kentucky_Fried_Chicken_%28Tallulah%2C_Louisiana%29_01.jpg/960px-Kentucky_Fried_Chicken_%28Tallulah%2C_Louisiana%29_01.jpg",
    "subway": "https://thumb.wikimedia.org/wikipedia/commons/thumb/7/73/A_Subway_restaurant_in_a_strip_mall_in_Franklin%2C_North_Carolina%2C_United_States.jpg/960px-A_Subway_restaurant_in_a_strip_mall_in_Franklin%2C_North_Carolina%2C_United_States.jpg",
    "starbucks": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ad/Starbuckscenter.jpg/960px-Starbuckscenter.jpg",
    "mcdonald": "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=800&q=80",
    "burger king": "https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=800&q=80",
    "domino": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=800&q=80",
    "pizza hut": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=800&q=80",
}

# Authentic venue interior/dining ambiance pools for appropriate fallback
# When restaurant-specific photos are not available, use authentic dining spaces (not pretending to be a specific dish)
_VENUE_IMAGE_POOLS: dict[str, list[str]] = {
    "indian_dining": [
        "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1590846406792-0adc7f938f1d?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1559339352-11d035aa65de?auto=format&fit=crop&w=800&q=80",
    ],
    "cafe": [
        "https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=800&q=80",
    ],
    "bistro": [
        "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1537047902294-62a40c20a6ae?auto=format&fit=crop&w=800&q=80",
    ],
    "bar": [
        "https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1572116469696-31de0f17cc34?auto=format&fit=crop&w=800&q=80",
    ],
    "asian_dining": [
        "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80",
    ],
    "dining": [
        "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1559339352-11d035aa65de?auto=format&fit=crop&w=800&q=80",
    ],
}


def _deterministic_pick(pool: list[str], seed_str: str) -> str:
    """Pick an image deterministically using md5 hash of restaurant name + location."""
    if not pool:
        return DEFAULT_FALLBACK_IMAGE
    h = int(hashlib.md5(seed_str.lower().strip().encode("utf-8")).hexdigest(), 16)
    return pool[h % len(pool)]


def get_restaurant_image(name: str | None, location: str | None, cuisines: str | None) -> str:
    """Resolve a restaurant image preferring actual exterior/interior restaurant photos.

    1. Checks (restaurant name + location) for specific restaurant outlet/branch photos.
    2. Checks (restaurant name) for official brand/chain exterior/interior photos.
    3. If not found, falls back gracefully to a curated authentic restaurant dining/venue ambiance photo
       using deterministic hashing on (name + location) for visual variety.
    4. Never crashes; falls back safely on any error or missing input.
    """
    try:
        norm_name = (name or "").lower().strip()
        norm_loc = (location or "").lower().strip()
        norm_cui = (cuisines or "").lower().strip()
        seed = f"{norm_name}:{norm_loc}"

        # 1. Location-Specific Restaurant Outlet Match (Name + Location)
        for brand_k, loc_k, img_url in _RESTAURANT_LOCATION_IMAGE_MAP:
            if brand_k in norm_name and loc_k in norm_loc:
                return img_url

        # 2. Restaurant Brand / Venue Match
        for brand_key, img_url in _BRAND_IMAGE_MAP.items():
            if brand_key in norm_name:
                return img_url

        # 3. Appropriate Venue/Ambiance Fallback by Cuisine & Restaurant Type
        combined_text = f"{norm_name} {norm_cui}"
        if any(w in combined_text for w in ["brewery", "pub", "bar", "cocktail", "beer", "lounge"]):
            return _deterministic_pick(_VENUE_IMAGE_POOLS["bar"], seed)
        if any(w in combined_text for w in ["cafe", "coffee", "bakery", "dessert", "tea"]):
            return _deterministic_pick(_VENUE_IMAGE_POOLS["cafe"], seed)
        if any(w in combined_text for w in ["biryani", "north indian", "south indian", "mughlai", "tandoori", "punjabi", "dosa", "thali"]):
            return _deterministic_pick(_VENUE_IMAGE_POOLS["indian_dining"], seed)
        if any(w in combined_text for w in ["pizza", "pasta", "italian", "continental", "european"]):
            return _deterministic_pick(_VENUE_IMAGE_POOLS["bistro"], seed)
        if any(w in combined_text for w in ["chinese", "asian", "thai", "japanese", "sushi"]):
            return _deterministic_pick(_VENUE_IMAGE_POOLS["asian_dining"], seed)

        # 4. Universal Dining Room Ambiance Fallback
        return _deterministic_pick(_VENUE_IMAGE_POOLS["dining"], seed)
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
