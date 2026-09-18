"""Phase 8: Streamlit Deployment Application.

A modern, consumer-grade AI-powered restaurant discovery interface.
Connects in-process to the recommendation service (Phases 1 → 2 → 3 → 4 → 6).
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
    initial_sidebar_state="collapsed",
)


# --- CUSTOM DESIGN SYSTEM & CSS INJECTION ---
def inject_custom_css() -> None:
    """Inject polished, modern SaaS styling for the restaurant discovery UI."""
    st.html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --brand-primary: #E23744;
            --brand-primary-hover: #CB202D;
            --brand-primary-light: #FFF5F5;
            --brand-primary-border: #FECDD3;
            --bg-page: #FAFAF9;
            --surface-card: #FFFFFF;
            --text-heading: #18181B;
            --text-body: #3F3F46;
            --text-muted: #71717A;
            --border-subtle: #E4E4E7;
            --rating-green: #15803D;
            --rating-bg: #DCFCE7;
            --gold-rank: #D97706;
            --gold-bg: #FEF3C7;
        }

        /* Global Reset & Typography */
        html, body, [class*="css"] {
            font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif !important;
            color: var(--text-body);
        }

        .stApp {
            background-color: var(--bg-page);
        }

        .block-container {
            max-width: 920px !important;
            padding-top: 1.5rem !important;
            padding-bottom: 4rem !important;
        }

        /* Header Branding */
        .brand-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.5rem 0 1.25rem 0;
            border-bottom: 1px solid var(--border-subtle);
            margin-bottom: 1.5rem;
        }

        .brand-title-wrap {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-icon-box {
            background: linear-gradient(135deg, #FFF1F2 0%, #FFE4E6 100%);
            border: 1px solid var(--brand-primary-border);
            width: 44px;
            height: 44px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            box-shadow: 0 2px 8px rgba(226, 55, 68, 0.12);
        }

        .brand-name {
            font-size: 1.35rem;
            font-weight: 800;
            color: var(--text-heading);
            letter-spacing: -0.02em;
            line-height: 1.2;
        }

        .brand-tagline {
            font-size: 0.82rem;
            color: var(--text-muted);
            font-weight: 500;
        }

        .ai-status-pill {
            background: #FFF1F2;
            color: var(--brand-primary);
            border: 1px solid var(--brand-primary-border);
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 20px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            letter-spacing: 0.02em;
        }

        /* Hero Section */
        .hero-container {
            text-align: center;
            padding: 1.25rem 0 1.75rem 0;
        }

        .hero-headline {
            font-size: 2.25rem;
            font-weight: 800;
            color: var(--text-heading);
            letter-spacing: -0.03em;
            line-height: 1.2;
            margin-bottom: 0.6rem;
        }

        .hero-subtitle {
            font-size: 1rem;
            color: var(--text-muted);
            line-height: 1.5;
            max-width: 620px;
            margin: 0 auto;
            font-weight: 400;
        }

        /* Search & Preference Card */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--surface-card) !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 18px !important;
            padding: 1.5rem 1.75rem !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
            margin-bottom: 2rem !important;
        }

        .form-section-title {
            font-size: 0.8rem;
            font-weight: 800;
            color: #4B5563;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.6rem;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* Quick Inspiration Chips */
        .quick-chips-row {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin: 0.6rem 0 1.2rem 0;
        }

        .chip-label {
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 0.4rem;
        }

        /* Primary Button Accent */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #E23744 0%, #EA580C 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            font-weight: 700 !important;
            font-size: 1.05rem !important;
            border-radius: 12px !important;
            padding: 0.65rem 1.5rem !important;
            box-shadow: 0 4px 14px rgba(226, 55, 68, 0.28) !important;
            transition: all 0.2s ease !important;
        }

        div.stButton > button[kind="primary"]:hover {
            box-shadow: 0 6px 20px rgba(226, 55, 68, 0.38) !important;
            transform: translateY(-1px) !important;
        }

        /* Search Summary Banner */
        .search-summary-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 14px;
            padding: 1rem 1.25rem;
            margin-bottom: 1.75rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        }

        .search-summary-header {
            font-size: 0.8rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }

        .search-criteria-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
            margin-bottom: 0.4rem;
        }

        .criteria-pill {
            background: #F4F4F5;
            color: #27272A;
            border: 1px solid #E4E4E7;
            font-size: 0.82rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }

        .summary-count-line {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--brand-primary);
            margin-top: 0.4rem;
        }

        /* Restaurant Card (Clean, Modern, No Fake Images) */
        .restaurant-card {
            background: var(--surface-card);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        .restaurant-card:hover {
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
            transform: translateY(-2px);
        }

        .top-match-card {
            border: 1.5px solid var(--brand-primary-border);
            box-shadow: 0 6px 24px rgba(226, 55, 68, 0.08);
            background: linear-gradient(180deg, #FFFDFD 0%, #FFFFFF 100%);
        }

        .card-header-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.5rem;
        }

        .rank-badge-top {
            background: #FFF1F2;
            color: var(--brand-primary);
            border: 1px solid var(--brand-primary-border);
            font-size: 0.76rem;
            font-weight: 800;
            padding: 3px 10px;
            border-radius: 20px;
            letter-spacing: 0.04em;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .rank-badge-standard {
            background: #F4F4F5;
            color: #52525B;
            border: 1px solid var(--border-subtle);
            font-size: 0.76rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 20px;
            letter-spacing: 0.04em;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .rating-badge-pill {
            background: var(--rating-green);
            color: #FFFFFF;
            font-size: 0.85rem;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            gap: 3px;
        }

        .restaurant-name {
            font-size: 1.4rem;
            font-weight: 800;
            color: var(--text-heading);
            margin: 0.25rem 0 0.5rem 0;
            letter-spacing: -0.02em;
        }

        .card-meta-row {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 10px;
            color: var(--text-muted);
            font-size: 0.88rem;
            margin-bottom: 0.9rem;
        }

        .cuisine-pill {
            background: #F4F4F5;
            color: #3F3F46;
            font-size: 0.78rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 6px;
        }

        /* AI Recommendation Box */
        .ai-explanation-box {
            background: var(--brand-primary-light);
            border: 1px solid #FFE4E6;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin-top: 0.8rem;
        }

        .ai-explanation-header {
            font-size: 0.8rem;
            font-weight: 800;
            color: var(--brand-primary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.4rem;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .ai-explanation-text {
            font-size: 0.92rem;
            color: #27272A;
            line-height: 1.55;
            font-weight: 450;
        }

        .ai-explanation-footer {
            margin-top: 0.6rem;
            font-size: 0.72rem;
            color: #9CA3AF;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        /* Empty State */
        .empty-state-box {
            background: #FFFFFF;
            border: 1px dashed #D1D5DB;
            border-radius: 16px;
            padding: 2.5rem 1.5rem;
            text-align: center;
            margin: 2rem 0;
        }

        .empty-state-icon {
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
        }

        .empty-state-title {
            font-size: 1.2rem;
            font-weight: 800;
            color: var(--text-heading);
            margin-bottom: 0.4rem;
        }

        .empty-state-desc {
            font-size: 0.92rem;
            color: var(--text-muted);
            max-width: 480px;
            margin: 0 auto 1.25rem auto;
            line-height: 1.5;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E5E7EB !important;
        }
        </style>
        """
    )


# --- CACHED RUNTIME LOADER ---
@st.cache_resource(show_spinner="Connecting to restaurant catalog...")
def get_runtime() -> AppContext:
    return load_runtime()


def _index_or_zero(items: list[str], value: str) -> int:
    try:
        return items.index(value)
    except ValueError:
        return 0


# --- COMPONENT HELPERS ---
def render_header() -> None:
    """Render the top brand bar with product name and AI badge."""
    st.html(
        """
        <div class="brand-bar">
            <div class="brand-title-wrap">
                <div class="brand-icon-box">🍽️</div>
                <div>
                    <div class="brand-name">AI Restaurant Finder</div>
                    <div class="brand-tagline">Personalized restaurant recommendations powered by AI</div>
                </div>
            </div>
            <div>
                <span class="ai-status-pill">✨ AI-POWERED</span>
            </div>
        </div>
        """
    )


def render_hero() -> None:
    """Render the hero headline and value proposition."""
    st.html(
        """
        <div class="hero-container">
            <div class="hero-headline">Find a restaurant you'll actually love.</div>
            <div class="hero-subtitle">
                Discover your next dining spot tailored to your neighborhood, budget tier, favorite cuisine, and exact dining mood.
            </div>
        </div>
        """
    )


def render_search_panel(ctx: AppContext) -> bool:
    """Render the structured 3-row preference panel and return submission state."""
    loc_options = ctx.catalog.locations
    cui_options = ctx.catalog.cuisines

    budget_options = [
        "Medium (₹500 - ₹1,500)",
        "Low (Under ₹500)",
        "High (₹1,500+)",
    ]

    rating_options = [
        "4.0+ Stars",
        "4.5+ Stars",
        "3.5+ Stars",
        "Any Rating",
    ]

    with st.container(border=True):
        st.html("<div class='form-section-title'>📍 WHERE & HOW MUCH</div>")

        # Row 1: Location & Budget
        r1_col1, r1_col2 = st.columns(2)
        with r1_col1:
            sel_loc = st.selectbox(
                "Select Location / Neighborhood",
                options=loc_options,
                index=_index_or_zero(loc_options, st.session_state.pref_location),
                help="Neighborhood in Bengaluru to search",
            )
            st.session_state.pref_location = sel_loc

        with r1_col2:
            sel_bud = st.selectbox(
                "Select Budget Tier",
                options=budget_options,
                index=_index_or_zero(budget_options, st.session_state.pref_budget),
                help="Estimated dining cost for two people",
            )
            st.session_state.pref_budget = sel_bud

        st.html("<div style='height: 8px;'></div>")
        st.html("<div class='form-section-title'>🍴 FLAVORS & STANDARDS</div>")

        # Row 2: Cuisine & Minimum Rating
        r2_col1, r2_col2 = st.columns(2)
        with r2_col1:
            sel_cui = st.selectbox(
                "Select Cuisine",
                options=cui_options,
                index=_index_or_zero(cui_options, st.session_state.pref_cuisine),
                help="Primary cuisine preference",
            )
            st.session_state.pref_cuisine = sel_cui

        with r2_col2:
            sel_rat = st.selectbox(
                "Minimum Dining Rating",
                options=rating_options,
                index=_index_or_zero(rating_options, st.session_state.pref_min_rating),
                help="Minimum diner rating on a 5-star scale",
            )
            st.session_state.pref_min_rating = sel_rat

        st.html("<div style='height: 8px;'></div>")
        st.html("<div class='form-section-title'>✨ SPECIFIC VIBE & CRAVINGS</div>")

        # Row 3: Additional Preferences & Natural Language Input
        pref_text = st.text_input(
            "Additional Preferences (Optional)",
            value=st.session_state.pref_additional,
            placeholder="e.g., quiet romantic dinner, authentic woodfired pizza, outdoor garden seating...",
            help="Tell AI anything specific: vibes, must-have dishes, dietary constraints, or occasions.",
        )
        st.session_state.pref_additional = pref_text

        # Quick inspiration chips
        st.html("<div class='chip-label'>Quick inspiration:</div>")
        chip_cols = st.columns(4)
        if chip_cols[0].button("🌆 Rooftop & Drinks", use_container_width=True):
            st.session_state.pref_additional = "rooftop terrace with city views and craft cocktails"
            st.rerun()
        if chip_cols[1].button("🥘 Butter Chicken", use_container_width=True):
            st.session_state.pref_additional = "authentic rich butter chicken, garlic naan and family seating"
            st.rerun()
        if chip_cols[2].button("☕ Cozy Cafe", use_container_width=True):
            st.session_state.pref_additional = "cozy quiet cafe with artisan coffee and gourmet pasta"
            st.rerun()
        if chip_cols[3].button("🥞 Ghee Roast Dosa", use_container_width=True):
            st.session_state.pref_additional = "crispy ghee roast masala dosa with fresh coconut chutney"
            st.rerun()

        st.html("<div style='height: 12px;'></div>")

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
    used_fallback: bool,
) -> None:
    """Display a clean summary card of the active search criteria above results."""
    fallback_badge = (
        "<span style='background:#FEF3C7; color:#92400E; border:1px solid #FDE68A; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:6px; margin-left:8px;'>Heuristic Ranking Mode</span>"
        if used_fallback
        else ""
    )

    st.html(
        f"""
        <div class="search-summary-card">
            <div class="search-summary-header">Restaurants matching your search</div>
            <div class="search-criteria-badges">
                <span class="criteria-pill">📍 {html.escape(location)}</span>
                <span class="criteria-pill">🍴 {html.escape(cuisine)}</span>
                <span class="criteria-pill">💰 {html.escape(budget_label)}</span>
                <span class="criteria-pill">⭐ {html.escape(rating_label)}</span>
            </div>
            <div class="summary-count-line">
                ✨ {count} restaurant{"s" if count != 1 else ""} curated & ranked by AI {fallback_badge}
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

    # Rank badge treatment
    if rank == 1:
        rank_badge_html = '<span class="rank-badge-top">👑 #1 TOP MATCH</span>'
        card_class = "restaurant-card top-match-card"
    elif rank == 2:
        rank_badge_html = '<span class="rank-badge-standard">🥈 #2 GREAT MATCH</span>'
        card_class = "restaurant-card"
    elif rank == 3:
        rank_badge_html = '<span class="rank-badge-standard">🥉 #3 RECOMMENDED</span>'
        card_class = "restaurant-card"
    else:
        rank_badge_html = f'<span class="rank-badge-standard">#{rank} RECOMMENDED</span>'
        card_class = "restaurant-card"

    # Cuisine pill tags
    cuisine_list = [c.strip() for c in cui.split(",") if c.strip()]
    cuisines_html = "".join(f'<span class="cuisine-pill">{html.escape(c)}</span>' for c in cuisine_list[:4])

    source_label = "Grounded by Groq LLM" if item.source == "llm" else "Deterministic Fallback Score"

    card_html = f"""
    <div class="{card_class}">
        <div class="card-header-row">
            <div>
                {rank_badge_html}
            </div>
            <div>
                <span class="rating-badge-pill">★ {html.escape(rating)}</span>
            </div>
        </div>

        <div class="restaurant-name">{html.escape(name)}</div>

        <div class="card-meta-row">
            <span>📍 {html.escape(loc)}</span>
            <span>•</span>
            <span>💰 {html.escape(cost)} for two</span>
            <span>•</span>
            <div style="display:inline-flex; gap:4px; align-items:center;">{cuisines_html}</div>
        </div>

        <div class="ai-explanation-box">
            <div class="ai-explanation-header">✨ Why AI recommends this</div>
            <div class="ai-explanation-text">"{html.escape(explanation)}"</div>
            <div class="ai-explanation-footer">Analysis Engine: {source_label}</div>
        </div>
    </div>
    """
    st.html(card_html)


def render_empty_state(case: str, message: str | None = None, hints: list[str] | None = None) -> None:
    """Render polished empty states with actionable guidance."""
    if case == "no_match":
        title = "Nothing matched your search"
        desc = (
            message
            or "We couldn't find restaurants matching all your criteria simultaneously in this area. "
            "Try adjusting your filters to expand the search."
        )
        icon = "🔍"
    else:
        title = "Recommendations could not be generated"
        desc = (
            message
            or "The recommendation engine was unable to synthesize grounded recommendations for this query. "
            "Please try refining your preferences."
        )
        icon = "🍽️"

    hints_html = ""
    if hints:
        hints_items = "".join(f"<li>{html.escape(h)}</li>" for h in hints)
        hints_html = f"<ul style='text-align:left; display:inline-block; margin-top:0.5rem; font-size:0.88rem; color:#4B5563;'>{hints_items}</ul>"

    st.html(
        f"""
        <div class="empty-state-box">
            <div class="empty-state-icon">{icon}</div>
            <div class="empty-state-title">{html.escape(title)}</div>
            <div class="empty-state-desc">{html.escape(desc)}</div>
            {hints_html}
        </div>
        """
    )


def render_developer_details(res: RecommendResponse, ctx: AppContext) -> None:
    """Collapsible expander containing runtime diagnostics."""
    with st.expander("🛠️ Developer & Pipeline Details"):
        d_col1, d_col2, d_col3 = st.columns(3)
        with d_col1:
            st.metric("Total Catalog", f"{ctx.status.restaurant_count:,}")
        with d_col2:
            st.metric("Groq LLM Active", "Yes" if ctx.status.groq_configured else "Fallback")
        with d_col3:
            st.metric("Response State", res.state.title())

        if res.filter_diagnostics:
            fd = res.filter_diagnostics
            st.caption("Deterministic Screening Pipeline Funnel:")
            st.write(
                f"- Total records examined: **{fd.total_records:,}**\n"
                f"- After location filter: **{fd.after_location:,}**\n"
                f"- After budget tier filter: **{fd.after_budget:,}**\n"
                f"- After cuisine match: **{fd.after_cuisine:,}**\n"
                f"- After minimum rating: **{fd.after_rating:,}**\n"
                f"- Candidates supplied to reasoning engine: **{fd.shortlist_count}**"
            )

        if res.llm_model:
            st.caption(f"Reasoning Model: `{res.llm_model}`")

        if res.used_fallback:
            st.warning(f"Fallback reason: {res.fallback_reason or 'API limits or offline mode'}")


def render_sidebar(ctx: AppContext) -> None:
    """Render a clean, product-focused sidebar with no technical clutter."""
    with st.sidebar:
        st.html(
            """
            <div style="padding: 0.5rem 0 1rem 0; border-bottom: 1px solid #E5E7EB; margin-bottom: 1rem;">
                <div style="font-size: 1.2rem; font-weight: 800; color: #18181B;">🍽️ AI Restaurant Finder</div>
                <div style="font-size: 0.8rem; color: #71717A;">Intelligent Dining Recommendations</div>
            </div>
            """
        )

        st.markdown("### How It Works")
        st.markdown(
            "1. **Deterministic Screening**: Filters real restaurant records matching your location, budget band, and cuisine.\n"
            "2. **AI Reasoning**: Analyzes trade-offs and explains *why* each spot fits your vibe.\n"
            "3. **Zero Downtime**: Automatically falls back to deterministic heuristic ranking if API limits occur."
        )

        st.markdown("---")
        st.markdown("### Catalog Scope")
        st.markdown(
            f"- **City**: Bengaluru\n"
            f"- **Restaurants Cached**: {ctx.status.restaurant_count:,}\n"
            f"- **Neighborhoods**: {len(ctx.catalog.locations)}\n"
            f"- **Cuisines**: {len(ctx.catalog.cuisines)}"
        )

        st.markdown("---")
        if st.button("🔄 Reset Search Preferences", use_container_width=True):
            st.session_state.pref_location = "Koramangala 5th Block" if "Koramangala 5th Block" in ctx.catalog.locations else ctx.catalog.locations[0]
            st.session_state.pref_budget = "Medium (₹500 - ₹1,500)"
            st.session_state.pref_cuisine = "North Indian"
            st.session_state.pref_min_rating = "4.0+ Stars"
            st.session_state.pref_additional = "quiet rooftop dining with good ambience"
            st.session_state.pop("search_result", None)
            st.session_state.pop("search_error", None)
            st.rerun()


# --- MAIN APPLICATION CONTROLLER ---
def main() -> None:
    inject_custom_css()

    # Load application runtime and data catalog
    try:
        ctx = get_runtime()
    except Exception as exc:
        st.error(
            "Something went wrong while initializing the restaurant catalog. Please ensure the Phase 1 cache exists.",
            icon=":material/error:",
        )
        with st.expander("Technical details"):
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
    st.session_state.setdefault("pref_additional", "quiet rooftop dining with good ambience")

    # Render Sidebar
    render_sidebar(ctx)

    # Render Top Elements
    render_header()
    render_hero()

    # Render Preference Panel
    submitted = render_search_panel(ctx)

    # Execute Search on Click
    if submitted:
        # Map human-friendly budget to backend contract
        if "Low" in st.session_state.pref_budget:
            budget_key = "low"
        elif "High" in st.session_state.pref_budget:
            budget_key = "high"
        else:
            budget_key = "medium"

        # Map human-friendly rating to float
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
            with st.spinner("Finding your best matches... Analyzing restaurants based on your preferences..."):
                result = run_search(search_payload)
                st.session_state.search_result = result
                st.session_state.search_error = None
                st.session_state.resolved_display_loc = resolved_loc
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

    # Display Results or State
    search_error = st.session_state.get("search_error")
    search_result: RecommendResponse | None = st.session_state.get("search_result")
    summary_meta = st.session_state.get("last_search_summary")

    if search_error:
        for err_msg in search_error:
            st.error(err_msg, icon="⚠️")
        if st.session_state.get("last_exception"):
            with st.expander("Technical details"):
                st.code(st.session_state.get("last_exception"))

    elif search_result is not None:
        if search_result.state == "no_match" or not search_result.recommendations:
            render_empty_state(
                case="no_match",
                message=search_result.no_match_message,
                hints=search_result.refine_hints,
            )
        else:
            # Render Search Summary
            if summary_meta:
                render_search_summary(
                    location=summary_meta["location"],
                    budget_label=summary_meta["budget"],
                    cuisine=summary_meta["cuisine"],
                    rating_label=summary_meta["rating"],
                    count=len(search_result.recommendations),
                    used_fallback=search_result.used_fallback or (search_result.state == "fallback"),
                )

            # Render Cards
            for idx, card_item in enumerate(search_result.recommendations):
                render_restaurant_card(card_item, is_top=(idx == 0))

        # Developer details expander
        render_developer_details(search_result, ctx)


if __name__ == "__main__":
    main()
