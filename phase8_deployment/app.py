"""Phase 8: Streamlit Deployment Application.

A modern, consumer-grade AI Restaurant Finder frontend.
Preserves all existing backend logic, pipelines, dataset handling, and Groq integration.
"""

from __future__ import annotations

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
            padding: 1.25rem 1.4rem;
            margin-bottom: 1.1rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        .recommendation-card:hover {
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.05);
            transform: translateY(-1px);
        }

        .top-tier-card {
            border: 1.5px solid var(--brand-border);
            box-shadow: 0 4px 18px rgba(226, 55, 68, 0.06);
            background: linear-gradient(180deg, #FFFDFD 0%, #FFFFFF 100%);
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
        <div style="margin-top: 1rem;">
            <div class="picks-header-title">✨ YOUR AI PICKS</div>
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
        rank_label = '<span class="rank-label-top">#1 Top Match</span>'
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

    card_html = f"""
    <div class="{card_class}">
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
            {html.escape(cui)} • ₹{html.escape(cost)} for two
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


def render_developer_details(res: RecommendResponse, ctx: AppContext) -> None:
    """Collapsible expander containing technical pipeline diagnostics."""
    with st.expander("Developer details", expanded=False):
        d_col1, d_col2, d_col3 = st.columns(3)
        with d_col1:
            st.caption("Catalog Size")
            st.write(f"**{ctx.status.restaurant_count:,}** restaurants")
        with d_col2:
            st.caption("Recommendation Source")
            st.write(f"**{res.state.title()}** ({'Fallback' if res.used_fallback else 'LLM'})")
        with d_col3:
            st.caption("Reasoning Model")
            st.write(f"`{res.llm_model or 'Deterministic Heuristic'}`")

        st.caption("Catalog Scope:")
        st.write(
            f"- City: Bengaluru\n"
            f"- Records: **{ctx.status.restaurant_count:,}**\n"
            f"- Neighborhoods: **{len(ctx.catalog.locations)}**\n"
            f"- Cuisines: **{len(ctx.catalog.cuisines)}**"
        )

        if res.filter_diagnostics:
            fd = res.filter_diagnostics
            st.caption("Candidate Screening Funnel:")
            st.write(
                f"- Total records examined: **{fd.total_records:,}**\n"
                f"- After location filter: **{fd.after_location:,}**\n"
                f"- After budget tier filter: **{fd.after_budget:,}**\n"
                f"- After cuisine match: **{fd.after_cuisine:,}**\n"
                f"- After minimum rating: **{fd.after_rating:,}**\n"
                f"- Final shortlist to reasoning engine: **{fd.shortlist_count}**"
            )

        if res.used_fallback and res.fallback_reason:
            st.info(f"Fallback reason: {res.fallback_reason}")


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
            # Summary above results
            if summary_meta:
                render_search_summary(
                    location=summary_meta["location"],
                    budget_label=summary_meta["budget"],
                    cuisine=summary_meta["cuisine"],
                    rating_label=summary_meta["rating"],
                    count=len(search_result.recommendations),
                    used_fallback=search_result.used_fallback or (search_result.state == "fallback"),
                )

            # Recommendation Cards
            for idx, card in enumerate(search_result.recommendations):
                render_restaurant_card(card, is_top=(idx == 0))

        # Secondary Developer details at bottom
        render_developer_details(search_result, ctx)


if __name__ == "__main__":
    main()
