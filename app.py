"""
Business Advisor
AI-Powered Business Intelligence & Decision Support Platform.
All business logic is delegated to the existing backend.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.agent.coordinator_agent import run_full_business_analysis
from src.finance.simulator import simulate_financials
from src.analysis.what_if import (
    compare_financial_scenarios,
    compare_ml_scenarios,
    describe_financial_changes,
)
from src.analysis.location_context import get_location_context


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Business Advisor · AI Business Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────────────────────
# PROFESSIONAL SAAS BI STYLING (COMMERCIAL QUALITY)
# ─────────────────────────────────────────────────────────────────────────────

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

#MainMenu, footer, header {
    visibility: hidden;
}

.stApp {
    background-color: #F7F8FA;
    color: #111827;
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1280px;
}

[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E5E7EB;
    padding-top: 0.5rem;
}

.sidebar-title {
    font-size: 1.1rem;
    font-weight: 800;
    color: #111827;
    letter-spacing: 0.04em;
}

.sidebar-subtitle {
    font-size: 0.7rem;
    color: #6B7280;
    margin-top: 0.15rem;
    line-height: 1.35;
}

.main-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.2rem;
    line-height: 1.2;
}

.main-subtitle {
    font-size: 0.88rem;
    color: #4B5563;
    margin-bottom: 1.2rem;
    line-height: 1.4;
}

.section-hdr {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #374151;
    border-bottom: 1px solid #E5E7EB;
    padding-bottom: 0.35rem;
    margin: 1.4rem 0 0.8rem 0;
}

.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 0.85rem 1rem;
    text-align: center;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
    height: 100%;
}

.kpi-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #6B7280;
    margin-bottom: 0.25rem;
}

.kpi-value {
    font-size: 1.45rem;
    font-weight: 700;
    color: #111827;
    line-height: 1.1;
}

.kpi-value.success { color: #10B981; }
.kpi-value.warning { color: #F59E0B; }
.kpi-value.danger { color: #EF4444; }
.kpi-value.accent { color: #2563EB; }

.kpi-sub {
    font-size: 0.72rem;
    color: #6B7280;
    margin-top: 0.25rem;
}

.disclaimer {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-left: 3px solid #2563EB;
    border-radius: 6px;
    padding: 0.6rem 0.9rem;
    font-size: 0.78rem;
    color: #4B5563;
    margin: 0.8rem 0;
    line-height: 1.45;
}

.change-pos { color: #10B981; font-weight: 600; }
.change-neg { color: #EF4444; font-weight: 600; }
.change-neu { color: #6B7280; font-weight: 500; }

.comp-table {
    width: 100%;
    border-collapse: collapse;
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    overflow: hidden;
    margin: 0.8rem 0;
    box-shadow: 0 1px 2px 0 rgba(0,0,0,0.03);
}

.comp-table th {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #4B5563;
    background: #F9FAFB;
    padding: 0.65rem 0.85rem;
    text-align: left;
    border-bottom: 1px solid #E5E7EB;
}

.comp-table td {
    font-size: 0.84rem;
    padding: 0.65rem 0.85rem;
    border-bottom: 1px solid #F3F4F6;
    color: #111827;
}

.comp-table td.metric {
    font-weight: 600;
    color: #1F2937;
    font-size: 0.86rem;
}

/* Landing Page Styles */
.landing-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0 1.5rem 0;
    border-bottom: 1px solid #E5E7EB;
    margin-bottom: 2rem;
}

.landing-brand {
    font-size: 1.25rem;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.landing-tagline {
    font-size: 0.82rem;
    color: #6B7280;
    font-weight: 500;
    margin-top: 0.15rem;
}

.hero-tag {
    display: inline-block;
    background: #EFF6FF;
    color: #2563EB;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 0.3rem 0.75rem;
    border-radius: 9999px;
    margin-bottom: 1rem;
    border: 1px solid #DBEAFE;
}

.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.15;
    margin-bottom: 1rem;
    letter-spacing: -0.02em;
}

.hero-sub {
    font-size: 1.05rem;
    color: #4B5563;
    line-height: 1.55;
    margin-bottom: 1.6rem;
}

.feature-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 1.3rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
    height: 100%;
}

.feature-num {
    font-size: 0.75rem;
    font-weight: 800;
    color: #FF4B4B;
    letter-spacing: 0.1em;
    margin-bottom: 0.35rem;
}

.feature-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.4rem;
    letter-spacing: 0.02em;
}

.feature-desc {
    font-size: 0.82rem;
    color: #4B5563;
    line-height: 1.45;
}

.step-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 1.1rem 0.95rem;
    text-align: center;
    box-shadow: 0 1px 2px 0 rgba(0,0,0,0.03);
    height: 100%;
}

.step-badge {
    display: inline-block;
    background: #F3F4F6;
    color: #374151;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 0.2rem 0.55rem;
    border-radius: 5px;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
}

.step-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.3rem;
}

.step-desc {
    font-size: 0.78rem;
    color: #6B7280;
    line-height: 1.4;
}

.agent-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-top: 3px solid #2563EB;
    border-radius: 8px;
    padding: 1.1rem 0.95rem;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
    height: 100%;
}

.engine-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-top: 3px solid #64748B;
    border-radius: 8px;
    padding: 1.1rem 0.95rem;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
    height: 100%;
}

.agent-name {
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #111827;
    margin-bottom: 0.35rem;
}

.agent-desc {
    font-size: 0.8rem;
    color: #4B5563;
    line-height: 1.4;
}

.arch-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 1.3rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.arch-node {
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 0.45rem 0.7rem;
    text-align: center;
    font-size: 0.72rem;
    font-weight: 700;
    color: #1E293B;
}

.arch-node.coordinator {
    background: #EFF6FF;
    border-color: #93C5FD;
    color: #1E40AF;
}

.arch-node.opportunity {
    background: #FDF2F8;
    border-color: #FBCFE8;
    color: #9D174D;
}

.arch-node.insights {
    background: #ECFDF5;
    border-color: #A7F3D0;
    color: #065F46;
}

.arch-arrow {
    text-align: center;
    color: #94A3B8;
    font-size: 0.85rem;
    line-height: 1.2;
    margin: 0.2rem 0;
}

.cta-box {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 2.2rem 1.8rem;
    text-align: center;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    margin: 2.5rem 0 1.5rem 0;
}

.cta-title {
    font-size: 1.45rem;
    font-weight: 800;
    color: #0F172A;
    margin-bottom: 0.4rem;
}

.cta-subtitle {
    font-size: 0.95rem;
    color: #4B5563;
    margin-bottom: 1.2rem;
}

.footer-text {
    font-size: 0.75rem;
    color: #9CA3AF;
    text-align: center;
    padding: 1.2rem 0 0.8rem 0;
    border-top: 1px solid #E5E7EB;
    margin-top: 1.8rem;
}

/* Pipeline Flow on Overview Page */
.pipe-node {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-top: 3px solid #2563EB;
    border-radius: 6px;
    padding: 0.75rem 0.65rem;
    text-align: center;
    height: 100%;
    box-shadow: 0 1px 2px 0 rgba(0,0,0,0.02);
}

.pipe-node-calc {
    border-top: 3px solid #64748B;
}

.pipe-status {
    color: #10B981;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    margin-bottom: 0.25rem;
}

.pipe-status-calc {
    color: #4B5563;
}

.pipe-role {
    color: #111827;
    font-size: 0.76rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}

.pipe-desc {
    color: #6B7280;
    font-size: 0.68rem;
    line-height: 1.3;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & HUMAN-READABLE FEATURE LABELS
# ─────────────────────────────────────────────────────────────────────────────

PLOT_DEFAULTS = {
    "plot_bgcolor": "#FFFFFF",
    "paper_bgcolor": "#FFFFFF",
    "font": {"color": "#4B5563", "family": "Inter, sans-serif"},
}

PERFORMANCE_COLORS = {
    "High": "#10B981",
    "Medium": "#F59E0B",
    "Low": "#EF4444",
}


def _human_feature_name(feature_name: str) -> str:
    """Map raw model feature name to clear, human-readable UI label."""
    if not feature_name:
        return ""

    direct_map = {
        "online_order_1": "Online Ordering (Yes)",
        "online_order_0": "Online Ordering (No)",
        "online_order": "Online Ordering",
        "book_table_1": "Table Booking (Yes)",
        "book_table_0": "Table Booking (No)",
        "book_table": "Table Booking",
        "approx_costfor_two_people": "Cost for Two",
        "log_cost": "Cost Level (Log Scale)",
        "cuisine_count": "Cuisine Count",
        "historical_restaurant_count": "Local Restaurant Density",
        "location_median_cost": "Median Cost in Location",
        "location_online_order_rate": "Location Online Order Rate",
        "location_book_table_rate": "Location Table Booking Rate",
        "location_cuisine_diversity": "Location Cuisine Diversity",
        "location_business_type_diversity": "Business Type Diversity",
        "votes": "Customer Review Votes",
    }

    if feature_name in direct_map:
        return direct_map[feature_name]

    if feature_name.startswith("cost_band_"):
        return f"Cost Band: {feature_name.replace('cost_band_', '').title()}"
    if feature_name.startswith("primary_cuisine_"):
        return f"Cuisine: {feature_name.replace('primary_cuisine_', '').replace('_', ' ').title()}"
    if feature_name.startswith("primary_rest_type_"):
        return f"Type: {feature_name.replace('primary_rest_type_', '').replace('_', ' ').title()}"
    if feature_name.startswith("location_") and not any(
        feature_name.startswith(p) for p in [
            "location_median", "location_online", "location_book", "location_cuisine", "location_business"
        ]
    ):
        return f"Location: {feature_name.replace('location_', '').replace('_', ' ').title()}"

    return feature_name.replace("_", " ").title()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _inr(value):
    """Format a numeric value as Indian currency (₹)."""
    if value is None:
        return "N/A"

    sign = "-" if value < 0 else ""
    amount = abs(value)

    if amount >= 100000:
        return f"{sign}₹{amount / 100000:.2f}L"

    return f"{sign}₹{amount:,.0f}"


def _perf_color(prediction):
    return {
        "High": "success",
        "Medium": "warning",
        "Low": "danger",
    }.get(prediction, "accent")


def _opp_color(score):
    if score >= 70:
        return "success"
    if score >= 40:
        return "warning"
    return "danger"


def _kpi(label, value, sub="", color=""):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    color_class = f" {color}" if color else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value{color_class}">{value}</div>'
        f'{sub_html}'
        f'</div>'
    )


def _section(title):
    st.markdown(
        f'<div class="section-hdr">{title}</div>',
        unsafe_allow_html=True,
    )


def _bar_config(height=280, show_legend=True, barmode=None, y_prefix="", y_suffix=""):
    cfg = {
        "plot_bgcolor": "#FFFFFF",
        "paper_bgcolor": "#FFFFFF",
        "font": {
            "family": 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            "size": 11,
            "color": "#4B5563",
        },
        "hoverlabel": {
            "bgcolor": "#111827",
            "font_size": 12,
            "font_family": "Inter, sans-serif",
            "font_color": "#FFFFFF",
            "bordercolor": "#111827",
        },
        "height": height,
        "margin": dict(l=45 if y_prefix else 25, r=20, t=30, b=25),
        "showlegend": show_legend,
        "xaxis": {
            "showgrid": False,
            "zeroline": False,
            "tickfont": {"color": "#6B7280", "size": 11},
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": "#E5E7EB",
            "gridwidth": 1,
            "zeroline": True,
            "zerolinecolor": "#E5E7EB",
            "tickfont": {"color": "#6B7280", "size": 11},
            "tickprefix": y_prefix,
            "ticksuffix": y_suffix,
        },
    }
    if barmode:
        cfg["barmode"] = barmode
    if show_legend:
        cfg["legend"] = {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.05,
            "xanchor": "left",
            "x": 0.0,
            "bgcolor": "rgba(255,255,255,0.92)",
            "bordercolor": "#E5E7EB",
            "borderwidth": 1,
            "font": {"color": "#374151", "size": 11},
        }
    return cfg


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

def sidebar():
    if st.session_state.get("page", "landing") == "landing":
        return

    with st.sidebar:
        st.markdown(
            '<div style="padding:0.2rem 0 0.8rem 0;">'
            '<div class="sidebar-title">BUSINESS ADVISOR</div>'
            '<div class="sidebar-subtitle">AI-Powered Business Intelligence &amp; Decision Support</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")

        navigation = {
            "Overview": "overview",
            "Business Analysis": "analysis",
            "Competition": "competition",
            "Financials": "financials",
            "What-If Analysis": "whatif",
        }

        current_page = st.session_state.get("page", "overview")

        for label, key in navigation.items():
            active = (current_page == key)
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.page = key
                st.rerun()

        st.markdown("---")

        if st.button("New Analysis", key="btn_new_analysis", use_container_width=True):
            st.session_state.page = "input"
            st.rerun()

        if st.session_state.get("analysis_done", False):
            inputs = st.session_state.get("form_inputs", {})
            result = st.session_state.get("analysis_result", {})
            prediction = result.get("performance_result", {}).get("prediction", "--")

            st.markdown("---")
            st.markdown(
                '<div style="font-size:0.65rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#6B7280;margin-bottom:.3rem;">'
                'Current Business'
                '</div>',
                unsafe_allow_html=True,
            )
            st.markdown(f"**{inputs.get('location', '--')}**")
            st.caption(
                f"{inputs.get('primary_cuisine', '--')} | {inputs.get('primary_rest_type', '--')}"
            )
            perf_cls = _perf_color(prediction)
            st.markdown(
                f'<div class="kpi-card" style="padding:0.4rem 0.6rem;margin-top:0.35rem;text-align:center;">'
                f'<div class="kpi-value {perf_cls}" style="font-size:1.05rem;">{prediction}</div>'
                f'<div class="kpi-sub" style="font-size:0.68rem;">Predicted Performance</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        if st.button("Product Overview", key="btn_home_info", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCT LANDING PAGE
# ─────────────────────────────────────────────────────────────────────────────

def page_landing():
    # Hide sidebar on landing page via CSS injection
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Top Brand Bar
    st.markdown(
        '<div class="landing-header">'
        '<div>'
        '<div class="landing-brand">BUSINESS ADVISOR</div>'
        '<div class="landing-tagline">AI-Powered Business Intelligence &amp; Decision Support</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Hero Section
    col_hero_left, col_hero_right = st.columns([1.15, 0.85], gap="large")

    with col_hero_left:
        st.markdown('<div class="hero-tag">ENTERPRISE DECISION INTELLIGENCE</div>', unsafe_allow_html=True)
        st.markdown(
            '<h1 class="hero-title">AI-POWERED<br>BUSINESS DECISION INTELLIGENCE</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="hero-sub">'
            'Analyze your market, predict business performance, '
            'understand competition, and evaluate financial scenarios before you invest.'
            '</p>',
            unsafe_allow_html=True,
        )

        c_cta, c_exp = st.columns([1.2, 1])
        with c_cta:
            if st.button("START BUSINESS ANALYSIS →", key="hero_start_btn", type="primary", use_container_width=True):
                st.session_state.page = "input"
                st.rerun()
        with c_exp:
            st.markdown(
                '<div style="font-size:0.86rem;color:#6B7280;padding-top:0.6rem;">'
                'Explore how it works ↓'
                '</div>',
                unsafe_allow_html=True,
            )

    with col_hero_right:
        # Conceptual AI Pipeline Architecture Card
        st.markdown(
            '<div class="arch-card">'
            '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#6B7280;margin-bottom:0.7rem;text-align:center;">'
            'AI Multi-Agent Pipeline Architecture'
            '</div>'
            '<div class="arch-node">BUSINESS INPUT DATA<br><span style="font-size:0.65rem;font-weight:400;color:#64748B;">Location · Cuisine · Operating Assumptions</span></div>'
            '<div class="arch-arrow">↓</div>'
            '<div class="arch-node coordinator">COORDINATOR AGENT<br><span style="font-size:0.65rem;font-weight:400;color:#3B82F6;">Orchestrates Specialist Agents</span></div>'
            '<div class="arch-arrow">↓</div>'
            '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.35rem;">'
            '<div class="arch-node" style="font-size:0.68rem;">LOCATION<br>AGENT<br><span style="font-size:0.6rem;font-weight:400;color:#64748B;">Market Context</span></div>'
            '<div class="arch-node" style="font-size:0.68rem;">PERFORMANCE<br>AGENT<br><span style="font-size:0.6rem;font-weight:400;color:#64748B;">ML + SHAP</span></div>'
            '<div class="arch-node" style="font-size:0.68rem;">COMPETITION<br>AGENT<br><span style="font-size:0.6rem;font-weight:400;color:#64748B;">Local Density</span></div>'
            '</div>'
            '<div class="arch-arrow">↓</div>'
            '<div class="arch-node opportunity">OPPORTUNITY AGENT<br><span style="font-size:0.65rem;font-weight:400;color:#DB2777;">Composite Opportunity Assessment</span></div>'
            '<div class="arch-arrow">↓</div>'
            '<div class="arch-node insights">BUSINESS INSIGHTS &amp; SIMULATION<br><span style="font-size:0.65rem;font-weight:400;color:#059669;">Financial Simulator · What-If Sensitivity</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # Why Business Advisor?
    st.markdown('<div class="section-hdr">WHY BUSINESS ADVISOR?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.95rem;color:#374151;margin-bottom:1rem;">'
        'Enterprise-grade intelligence combining multi-agent AI, machine learning, and deterministic financial modeling.'
        '</div>',
        unsafe_allow_html=True,
    )

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        st.markdown(
            '<div class="feature-card">'
            '<div class="feature-num">01</div>'
            '<div class="feature-title">MARKET INTELLIGENCE</div>'
            '<div class="feature-desc">Understand location and market context using historical business data.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with f2:
        st.markdown(
            '<div class="feature-card">'
            '<div class="feature-num">02</div>'
            '<div class="feature-title">PERFORMANCE PREDICTION</div>'
            '<div class="feature-desc">Predict expected business performance using machine learning.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with f3:
        st.markdown(
            '<div class="feature-card">'
            '<div class="feature-num">03</div>'
            '<div class="feature-title">COMPETITION INTELLIGENCE</div>'
            '<div class="feature-desc">Evaluate the competitive landscape using local business data.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with f4:
        st.markdown(
            '<div class="feature-card">'
            '<div class="feature-num">04</div>'
            '<div class="feature-title">FINANCIAL &amp; SCENARIO ANALYSIS</div>'
            '<div class="feature-desc">Estimate revenue, operating costs, break-even and evaluate What-If scenarios.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # How It Works
    st.markdown('<div class="section-hdr">HOW IT WORKS</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.95rem;color:#374151;margin-bottom:1rem;">'
        'A disciplined 4-step framework from initial business profile to executive decision support.'
        '</div>',
        unsafe_allow_html=True,
    )

    s1, s2, s3, s4 = st.columns(4)

    with s1:
        st.markdown(
            '<div class="step-card">'
            '<div class="step-badge">Step 01</div>'
            '<div class="step-title">Business Profile</div>'
            '<div class="step-desc">Enter location, cuisine, business type and operating assumptions.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with s2:
        st.markdown(
            '<div class="step-card">'
            '<div class="step-badge">Step 02</div>'
            '<div class="step-title">Multi-Agent Analysis</div>'
            '<div class="step-desc">Specialized agents analyze location, performance, competition and opportunity.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with s3:
        st.markdown(
            '<div class="step-card">'
            '<div class="step-badge">Step 03</div>'
            '<div class="step-title">Decision Intelligence</div>'
            '<div class="step-desc">Combine ML predictions, SHAP explanations, competition intelligence and financial simulation.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with s4:
        st.markdown(
            '<div class="step-card">'
            '<div class="step-badge">Step 04</div>'
            '<div class="step-title">Scenario Planning</div>'
            '<div class="step-desc">Change assumptions and evaluate What-If outcomes.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Built on Multi-Agent Intelligence
    st.markdown('<div class="section-hdr">BUILT ON MULTI-AGENT INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.95rem;color:#374151;margin-bottom:1rem;">'
        'Specialized agents work together to turn business inputs into actionable analysis.'
        '</div>',
        unsafe_allow_html=True,
    )

    a1, a2, a3, a4, a5 = st.columns(5)

    with a1:
        st.markdown(
            '<div class="agent-card">'
            '<div class="agent-name">Coordinator Agent</div>'
            '<div class="agent-desc">Orchestrates the analysis across all specialized agents.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with a2:
        st.markdown(
            '<div class="agent-card">'
            '<div class="agent-name">Location Agent</div>'
            '<div class="agent-desc">Analyzes market and location context using historical data.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with a3:
        st.markdown(
            '<div class="agent-card">'
            '<div class="agent-name">Performance Agent</div>'
            '<div class="agent-desc">ML prediction + SHAP explainability for performance drivers.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with a4:
        st.markdown(
            '<div class="agent-card">'
            '<div class="agent-name">Competition Agent</div>'
            '<div class="agent-desc">Competitive intelligence and local market density metrics.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with a5:
        st.markdown(
            '<div class="agent-card">'
            '<div class="agent-name">Opportunity Agent</div>'
            '<div class="agent-desc">Business opportunity assessment and composite scoring.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Decision-Support Engines
    st.markdown(
        '<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748B;margin-bottom:0.5rem;">'
        'DECISION-SUPPORT ENGINES'
        '</div>',
        unsafe_allow_html=True,
    )

    e1, e2 = st.columns(2)

    with e1:
        st.markdown(
            '<div class="engine-card">'
            '<div class="agent-name" style="color:#334155;">Financial Simulator</div>'
            '<div class="agent-desc">Deterministic revenue, operating expense breakdown, contribution margin, and break-even customer modeling.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with e2:
        st.markdown(
            '<div class="engine-card">'
            '<div class="agent-name" style="color:#334155;">What-If Engine</div>'
            '<div class="agent-desc">Deterministic scenario comparison engine evaluating the impact of parameter adjustments on financial and ML outcomes.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Bottom Call to Action
    st.markdown(
        '<div class="cta-box">'
        '<div class="cta-title">READY TO ANALYZE YOUR BUSINESS?</div>'
        '<div class="cta-subtitle">Turn business assumptions into data-driven decision intelligence.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    _, col_btn, _ = st.columns([1, 1, 1])
    with col_btn:
        if st.button("START ANALYSIS →", key="bottom_start_btn", type="primary", use_container_width=True):
            st.session_state.page = "input"
            st.rerun()

    # Footer
    st.markdown(
        '<div class="footer-text">'
        '<strong>BUSINESS ADVISOR</strong> · AI-Powered Business Intelligence &amp; Decision Support<br>'
        '<span style="font-size:0.7rem;color:#9CA3AF;">Multi-Agent Decision Intelligence • ML • Explainable AI • Scenario Analysis</span>'
        '</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# LIVE MULTI-AGENT EXECUTION PANEL
# ─────────────────────────────────────────────────────────────────────────────

def _render_live_pipeline(placeholder, pipeline_status):
    items = [
        ("coordinator", "Coordinator Agent", "AI AGENT"),
        ("location", "Location Agent", "AI AGENT"),
        ("performance", "Performance Agent", "AI AGENT"),
        ("shap", "SHAP Explainer", "ANALYTICAL COMPONENT"),
        ("competition", "Competition Agent", "AI AGENT"),
        ("opportunity", "Opportunity Agent", "AI AGENT"),
        ("financial", "Financial Analysis", "ANALYTICAL COMPONENT"),
    ]

    card_rows = []
    for key, name, category in items:
        info = pipeline_status.get(key, {"status": "waiting", "message": "Waiting"})
        st_val = info.get("status", "waiting")
        msg = info.get("message", "Waiting")

        if st_val == "completed":
            icon = '<span style="color:#10B981;font-weight:700;font-size:1.15rem;margin-right:0.65rem;">✓</span>'
            border_style = "border:1px solid #D1FAE5;background:#F0FDF4;"
            tag_color = "#059669"
            tag_bg = "#DCFCE7"
            msg_color = "#065F46"
        elif st_val == "running":
            icon = '<span style="color:#2563EB;font-weight:700;font-size:1.15rem;margin-right:0.65rem;">⟳</span>'
            border_style = "border:1px solid #BFDBFE;background:#EFF6FF;box-shadow:0 1px 3px rgba(37,99,235,0.08);"
            tag_color = "#1D4ED8"
            tag_bg = "#DBEAFE"
            msg_color = "#1E40AF"
        else:  # waiting
            icon = '<span style="color:#9CA3AF;font-weight:600;font-size:1.15rem;margin-right:0.65rem;">○</span>'
            border_style = "border:1px solid #E5E7EB;background:#FFFFFF;"
            tag_color = "#6B7280"
            tag_bg = "#F3F4F6"
            msg_color = "#6B7280"

        badge = (
            f'<span style="font-size:0.68rem;font-weight:700;letter-spacing:0.04em;'
            f'color:{tag_color};background:{tag_bg};padding:0.18rem 0.45rem;'
            f'border-radius:4px;text-transform:uppercase;">{category}</span>'
        )

        card_rows.append(
            f'<div style="padding:0.65rem 0.9rem;border-radius:8px;margin-bottom:0.45rem;{border_style}'
            f'display:flex;align-items:center;justify-content:space-between;">'
            f'<div style="display:flex;align-items:center;">'
            f'{icon}'
            f'<div>'
            f'<div style="font-size:0.9rem;font-weight:700;color:#111827;display:flex;align-items:center;gap:0.5rem;">'
            f'{name}'
            f'{badge}'
            f'</div>'
            f'<div style="font-size:0.8rem;color:{msg_color};margin-top:0.12rem;font-weight:500;">{msg}</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )

    html = (
        '<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;padding:1.25rem 1.5rem;margin-top:1.25rem;box-shadow:0 4px 6px -1px rgba(0,0,0,0.04);">'
        '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;border-bottom:1px solid #F3F4F6;padding-bottom:0.75rem;">'
        '<div>'
        '<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.08em;color:#FF4B4B;text-transform:uppercase;">Multi-Agent Orchestration</div>'
        '<div style="font-size:1.15rem;font-weight:800;color:#111827;margin-top:0.15rem;">AI ANALYSIS IN PROGRESS</div>'
        '</div>'
        '<div style="font-size:0.78rem;color:#4B5563;background:#F3F4F6;padding:0.25rem 0.65rem;border-radius:9999px;font-weight:600;">'
        'Real-Time Execution'
        '</div>'
        '</div>'
        + "".join(card_rows) +
        '</div>'
    )
    placeholder.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS INPUT PAGE
# ─────────────────────────────────────────────────────────────────────────────

def page_input():
    st.markdown(
        '<h2 class="main-title">Business Analysis</h2>'
        '<div class="main-subtitle">Enter your business details to generate an AI-powered analysis.</div>',
        unsafe_allow_html=True,
    )

    with st.form("business_form"):
        _section("Business Profile")

        c1, c2, c3 = st.columns(3)

        with c1:
            location = st.text_input(
                "Location",
                value="Koramangala",
                placeholder="e.g. Koramangala, Bengaluru",
            )
            online_order = st.selectbox(
                "Online Ordering",
                [1, 0],
                format_func=lambda x: "Yes" if x else "No",
            )

        with c2:
            cuisine = st.text_input(
                "Primary Cuisine",
                value="North Indian",
            )
            book_table = st.selectbox(
                "Table Booking",
                [0, 1],
                format_func=lambda x: "Yes" if x else "No",
            )

        with c3:
            restaurant_type = st.selectbox(
                "Business Type",
                [
                    "Casual Dining",
                    "Quick Bites",
                    "Fine Dining",
                    "Cafe",
                    "Delivery",
                    "Beverage Shop",
                    "Food Court",
                    "Bakery",
                ],
            )
            cuisine_count = st.number_input(
                "Cuisine Count",
                min_value=1,
                max_value=20,
                value=2,
                step=1,
            )

        c4, c5 = st.columns(2)

        with c4:
            cost_for_two = st.number_input(
                "Approx Cost for Two (₹)",
                min_value=100,
                max_value=10000,
                value=800,
                step=50,
            )

        with c5:
            cost_band = st.selectbox(
                "Cost Band",
                [
                    "Budget",
                    "Low",
                    "Medium",
                    "High",
                    "Premium",
                ],
                index=2,
            )

        _section("Operations")

        o1, o2, o3 = st.columns(3)

        with o1:
            customers_per_day = st.number_input(
                "Customers Per Day",
                min_value=0,
                max_value=5000,
                value=100,
                step=5,
            )

        with o2:
            average_order_value = st.number_input(
                "Average Order Value (₹)",
                min_value=0,
                max_value=10000,
                value=400,
                step=25,
            )

        with o3:
            working_days = st.number_input(
                "Working Days Per Month",
                min_value=1,
                max_value=31,
                value=30,
                step=1,
            )

        _section("Cost Structure")

        cs1, cs2, cs3 = st.columns(3)

        with cs1:
            rent = st.number_input(
                "Monthly Rent (₹)",
                min_value=0,
                max_value=2000000,
                value=60000,
                step=5000,
            )
            food_cost_percent = st.slider(
                "Food Cost (%)",
                min_value=0.0,
                max_value=100.0,
                value=32.0,
                step=0.5,
            )

        with cs2:
            staff_cost = st.number_input(
                "Staff Cost (₹)",
                min_value=0,
                max_value=2000000,
                value=50000,
                step=5000,
            )
            utilities = st.number_input(
                "Utilities (₹)",
                min_value=0,
                max_value=500000,
                value=15000,
                step=1000,
            )

        with cs3:
            marketing = st.number_input(
                "Marketing (₹)",
                min_value=0,
                max_value=500000,
                value=10000,
                step=1000,
            )
            other_expenses = st.number_input(
                "Other Expenses (₹)",
                min_value=0,
                max_value=500000,
                value=5000,
                step=1000,
            )

        submitted = st.form_submit_button(
            "Run Full Analysis",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not location.strip():
            st.error("Location is required.")
            return

        if not cuisine.strip():
            st.error("Primary cuisine is required.")
            return

        st.session_state.form_inputs = {
            "location": location.strip(),
            "primary_cuisine": cuisine.strip(),
            "primary_rest_type": restaurant_type,
            "cuisine_count": int(cuisine_count),
            "approx_costfor_two_people": float(cost_for_two),
            "cost_band": cost_band,
            "online_order": int(online_order),
            "book_table": int(book_table),
            "customers_per_day": float(customers_per_day),
            "average_order_value": float(average_order_value),
            "working_days": float(working_days),
            "rent": float(rent),
            "staff_cost": float(staff_cost),
            "food_cost_percent": float(food_cost_percent),
            "utilities": float(utilities),
            "marketing": float(marketing),
            "other_expenses": float(other_expenses),
        }

        progress_placeholder = st.empty()

        pipeline_status = {
            "coordinator": {"status": "running", "message": "Orchestrating specialist analysis"},
            "location": {"status": "waiting", "message": "Waiting"},
            "performance": {"status": "waiting", "message": "Waiting"},
            "shap": {"status": "waiting", "message": "Waiting"},
            "competition": {"status": "waiting", "message": "Waiting"},
            "opportunity": {"status": "waiting", "message": "Waiting"},
            "financial": {"status": "waiting", "message": "Waiting"},
        }

        def on_progress(stage, status, message=None):
            pipeline_status[stage] = {
                "status": "running" if status == "started" else status,
                "message": message or ("Completed" if status == "completed" else "Running..."),
            }
            _render_live_pipeline(progress_placeholder, pipeline_status)

        # Initial live render
        _render_live_pipeline(progress_placeholder, pipeline_status)

        try:
            result = run_full_business_analysis(
                location=location,
                search_query=f"{cuisine} restaurants in {location}",
                online_order=int(online_order),
                book_table=int(book_table),
                approx_costfor_two_people=float(cost_for_two),
                cost_band=cost_band,
                primary_cuisine=cuisine,
                cuisine_count=int(cuisine_count),
                primary_rest_type=restaurant_type,
                progress_callback=on_progress,
            )

            on_progress("financial", "started", "Calculating revenue, expenses and break-even...")

            financial_result = simulate_financials(
                customers_per_day=float(customers_per_day),
                average_order_value=float(average_order_value),
                rent=float(rent),
                staff_cost=float(staff_cost),
                food_cost_percent=float(food_cost_percent),
                utilities=float(utilities),
                marketing=float(marketing),
                other_expenses=float(other_expenses),
                working_days=float(working_days),
            )

            on_progress("financial", "completed", "Financial model calculated")

            result["financial_result"] = financial_result

            st.session_state.analysis_result = result
            st.session_state.analysis_done = True
            st.session_state.page = "overview"

            for key in ["whatif_result", "whatif_ml_result", "whatif_type"]:
                st.session_state.pop(key, None)

            st.rerun()

        except Exception as error:
            st.error(f"Analysis failed: {error}")


# ─────────────────────────────────────────────────────────────────────────────
# OVERVIEW PAGE (EXECUTIVE DASHBOARD GRID)
# ─────────────────────────────────────────────────────────────────────────────

def page_overview():
    result = st.session_state.get("analysis_result", {})
    inputs = st.session_state.get("form_inputs", {})
    performance = result.get("performance_result", {})
    opportunity = result.get("opportunity_result", {})
    financial = result.get("financial_result", {})

    prediction = performance.get("prediction", "--")
    opportunity_score = opportunity.get("opportunity_score", {}).get("score", 0)
    opportunity_signal = opportunity.get("opportunity_score", {}).get("signal", "--")

    revenue = financial.get("monthly_revenue")
    expenses = financial.get("monthly_expenses", 0)
    operating_profit = financial.get("estimated_operating_profit")
    operating_margin = financial.get("operating_profit_margin", 0.0)
    break_even = financial.get("break_even_customers_per_day")

    # Header
    st.markdown(
        f'<h2 class="main-title">Business Overview</h2>'
        f'<div class="main-subtitle">'
        f'{inputs.get("primary_cuisine", "--")} &nbsp;·&nbsp; '
        f'{inputs.get("primary_rest_type", "--")} &nbsp;·&nbsp; '
        f'{inputs.get("location", "--")}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # 1. Compact KPI Cards (Structured 5-card row)
    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        st.markdown(
            _kpi(
                "Predicted Performance",
                prediction,
                "Random Forest model",
                _perf_color(prediction),
            ),
            unsafe_allow_html=True,
        )

    with k2:
        st.markdown(
            _kpi(
                "Opportunity Score",
                f"{opportunity_score:.1f}",
                opportunity_signal,
                _opp_color(opportunity_score),
            ),
            unsafe_allow_html=True,
        )

    with k3:
        st.markdown(
            _kpi(
                "Monthly Revenue",
                _inr(revenue),
                "Assumption-based",
                "accent",
            ),
            unsafe_allow_html=True,
        )

    with k4:
        profit_color = "success" if (operating_profit or 0) >= 0 else "danger"
        st.markdown(
            _kpi(
                "Est. Operating Profit",
                _inr(operating_profit),
                f"{operating_margin:.1f}% margin",
                profit_color,
            ),
            unsafe_allow_html=True,
        )

    with k5:
        break_even_text = f"{break_even:.1f}/day" if break_even is not None else "N/A"
        st.markdown(
            _kpi(
                "Break-Even Point",
                break_even_text,
                "customers/day",
                "accent",
            ),
            unsafe_allow_html=True,
        )

    # Planning notice disclaimer
    st.markdown(
        """<div class="disclaimer">
            <strong>Planning Notice:</strong> Financial calculations are assumption-based estimates.
            Estimated Operating Profit is <strong>not Net Profit</strong>. ML predictions reflect historical pattern classification and do not guarantee future revenue.
        </div>""",
        unsafe_allow_html=True,
    )

    # 2. AI ANALYSIS PIPELINE (Horizontal Compact Multi-Agent Flow)
    _section("AI Analysis Pipeline")
    st.markdown(
        '<div style="font-size:0.82rem;color:#4B5563;margin-bottom:0.6rem;">'
        'Multi-agent orchestration powering your business analysis'
        '</div>',
        unsafe_allow_html=True,
    )

    p1, p2, p3, p4, p5, p6 = st.columns(6)

    with p1:
        st.markdown(
            '<div class="pipe-node">'
            '<div class="pipe-status">✓ COMPLETE</div>'
            '<div class="pipe-role">Coordinator Agent</div>'
            '<div class="pipe-desc">Orchestrates specialist analysis</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with p2:
        st.markdown(
            '<div class="pipe-node">'
            '<div class="pipe-status">✓ COMPLETE</div>'
            '<div class="pipe-role">Location Agent</div>'
            '<div class="pipe-desc">Market &amp; location context</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with p3:
        st.markdown(
            '<div class="pipe-node">'
            '<div class="pipe-status">✓ COMPLETE</div>'
            '<div class="pipe-role">Performance Agent</div>'
            '<div class="pipe-desc">ML prediction + SHAP</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with p4:
        st.markdown(
            '<div class="pipe-node">'
            '<div class="pipe-status">✓ COMPLETE</div>'
            '<div class="pipe-role">Competition Agent</div>'
            '<div class="pipe-desc">Competitive intelligence</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with p5:
        st.markdown(
            '<div class="pipe-node">'
            '<div class="pipe-status">✓ COMPLETE</div>'
            '<div class="pipe-role">Opportunity Agent</div>'
            '<div class="pipe-desc">Opportunity assessment</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with p6:
        st.markdown(
            '<div class="pipe-node pipe-node-calc">'
            '<div class="pipe-status pipe-status-calc">✓ COMPUTED</div>'
            '<div class="pipe-role">Financial Analysis</div>'
            '<div class="pipe-desc">Revenue, costs &amp; break-even</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # 3. Analytics Grid: Side-by-Side (Financial Overview + Performance Probabilities)
    _section("Executive Analytics Grid")

    col_fin, col_perf = st.columns([1.2, 0.8], gap="medium")

    with col_fin:
        if revenue is not None:
            st.markdown(
                '<div style="font-size:0.8rem;font-weight:700;color:#111827;margin-bottom:0.4rem;">'
                'Financial Overview: Revenue vs Total Expenses vs Operating Profit'
                '</div>',
                unsafe_allow_html=True,
            )

            figure = go.Figure()

            figure.add_bar(
                name="Revenue",
                x=["Monthly"],
                y=[revenue],
                marker_color="#2563EB",
                text=[_inr(revenue)],
                textposition="auto",
            )

            figure.add_bar(
                name="Total Expenses",
                x=["Monthly"],
                y=[expenses],
                marker_color="#64748B",
                text=[_inr(expenses)],
                textposition="auto",
            )

            figure.add_bar(
                name="Operating Profit",
                x=["Monthly"],
                y=[operating_profit],
                marker_color="#10B981" if (operating_profit or 0) >= 0 else "#EF4444",
                text=[_inr(operating_profit)],
                textposition="auto",
            )

            config = _bar_config(290)
            config["barmode"] = "group"
            config["yaxis"]["tickprefix"] = "₹"

            figure.update_layout(**config)

            st.plotly_chart(figure, use_container_width=True)

    with col_perf:
        probabilities = performance.get("probabilities", {})

        if probabilities:
            st.markdown(
                '<div style="font-size:0.8rem;font-weight:700;color:#111827;margin-bottom:0.4rem;">'
                'Performance Probability Distribution'
                '</div>',
                unsafe_allow_html=True,
            )

            ordered_classes = ["High", "Medium", "Low"]
            classes = [cls for cls in ordered_classes if cls in probabilities] or list(probabilities.keys())
            values = [probabilities.get(cls, 0.0) * 100 for cls in classes]

            figure = go.Figure(
                go.Bar(
                    x=classes,
                    y=values,
                    marker_color=[PERFORMANCE_COLORS.get(cls, "#2563EB") for cls in classes],
                    text=[f"{val:.1f}%" for val in values],
                    textposition="outside",
                )
            )

            perf_cfg = _bar_config(290, show_legend=False, y_suffix="%")
            perf_cfg["yaxis"]["range"] = [0, 110]
            perf_cfg["margin"] = dict(l=35, r=15, t=25, b=20)
            figure.update_layout(**perf_cfg)

            st.plotly_chart(figure, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS ANALYSIS PAGE
# ─────────────────────────────────────────────────────────────────────────────

def page_analysis():
    result = st.session_state.get("analysis_result", {})
    performance = result.get("performance_result", {})
    opportunity = result.get("opportunity_result", {})
    inputs = st.session_state.get("form_inputs", {})

    st.markdown('<h2 class="main-title">Business Analysis</h2>', unsafe_allow_html=True)

    # 1. Location Intelligence (Displays REAL backend values from location_result)
    _section("Location Intelligence")

    location_data = result.get("location_result", {})
    if not location_data:
        location_data = get_location_context(inputs.get("location", ""))

    found = location_data.get("found", False)

    if found:
        l1, l2, l3, l4 = st.columns(4)

        with l1:
            st.markdown(
                _kpi(
                    "Historical Restaurants",
                    str(location_data.get("historical_restaurant_count", "--")),
                    "Location dataset sample",
                ),
                unsafe_allow_html=True,
            )

        with l2:
            st.markdown(
                _kpi(
                    "Median Cost in Area",
                    _inr(location_data.get("location_median_cost")),
                    "Typical cost for two",
                ),
                unsafe_allow_html=True,
            )

        with l3:
            online_rate = location_data.get("location_online_order_rate", 0) * 100
            st.markdown(
                _kpi(
                    "Online Order Rate",
                    f"{online_rate:.1f}%",
                    "Area delivery adoption",
                ),
                unsafe_allow_html=True,
            )

        with l4:
            table_rate = location_data.get("location_book_table_rate", 0) * 100
            st.markdown(
                _kpi(
                    "Table Booking Rate",
                    f"{table_rate:.1f}%",
                    "Reservation prevalence",
                ),
                unsafe_allow_html=True,
            )

        # Context details
        c_div = location_data.get("location_cuisine_diversity", "--")
        b_div = location_data.get("location_business_type_diversity", "--")
        st.markdown(
            f'<div class="disclaimer">'
            f'<strong>Locality Profile:</strong> {inputs.get("location", "Selected locality")} reflects '
            f'<strong>{c_div} distinct cuisines</strong> and <strong>{b_div} restaurant formats</strong> in historical benchmarks. '
            f'Median dining cost for two people is <strong>{_inr(location_data.get("location_median_cost"))}</strong>.'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info(
            f"Historical dataset has limited baseline profiles for '{inputs.get('location', '')}'. "
            f"Local market density and competition intelligence are supplemented live via local competitor analysis."
        )

    # 2. Performance Prediction
    _section("Performance Prediction")

    prediction = performance.get("prediction", "--")
    probabilities = performance.get("probabilities", {})

    p1, p2 = st.columns([0.8, 1.2])

    with p1:
        st.markdown(
            _kpi(
                "Predicted Performance Class",
                prediction,
                "Random Forest model",
                _perf_color(prediction),
            ),
            unsafe_allow_html=True,
        )

    with p2:
        if probabilities:
            ordered_classes = ["High", "Medium", "Low"]
            classes = [cls for cls in ordered_classes if cls in probabilities] or list(probabilities.keys())
            values = [probabilities.get(cls, 0.0) * 100 for cls in classes]

            figure = go.Figure(
                go.Bar(
                    x=classes,
                    y=values,
                    marker_color=[
                        PERFORMANCE_COLORS.get(k, "#2563EB")
                        for k in classes
                    ],
                    text=[f"{val:.1f}%" for val in values],
                    textposition="outside",
                )
            )

            prob_cfg = _bar_config(200, show_legend=False, y_suffix="%")
            prob_cfg["yaxis"]["range"] = [0, 110]
            prob_cfg["margin"] = dict(l=35, r=15, t=20, b=15)
            figure.update_layout(**prob_cfg)

            st.plotly_chart(figure, use_container_width=True)

    # 3. SHAP Explainability (Human-Readable UI Labels)
    explanation = performance.get("explanation", {})
    top_features = explanation.get("top_features", [])

    if top_features:
        _section("SHAP Feature Explainability")

        st.caption(
            "Positive contribution means the feature pushed the model toward the predicted class. "
            "It reflects model decision weighting, not an absolute qualitative judgment."
        )

        features = [_human_feature_name(item["feature"]) for item in top_features]
        contributions = [item["contribution"] for item in top_features]
        directions = [item["direction"] for item in top_features]

        bar_colors = [
            "#10B981" if direction == "positive" else "#EF4444"
            for direction in directions
        ]

        figure = go.Figure(
            go.Bar(
                y=features[::-1],
                x=contributions[::-1],
                orientation="h",
                marker_color=bar_colors[::-1],
                text=[f"{val:+.4f}" for val in contributions[::-1]],
                textposition="outside",
            )
        )

        figure.update_layout(
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(family='Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', size=11, color="#374151"),
            hoverlabel=dict(bgcolor="#111827", font_size=12, font_family="Inter, sans-serif", font_color="#FFFFFF"),
            height=max(220, len(top_features) * 36 + 45),
            showlegend=False,
            xaxis=dict(
                showgrid=True,
                gridcolor="#E5E7EB",
                gridwidth=1,
                zeroline=True,
                zerolinecolor="#94A3B8",
                zerolinewidth=1.5,
                tickfont=dict(color="#6B7280", size=11),
            ),
            yaxis=dict(tickfont=dict(color="#111827", size=11)),
            margin=dict(l=10, r=40, t=15, b=10),
        )

        st.plotly_chart(figure, use_container_width=True)

    # 4. Opportunity Assessment (Displays REAL component values returned by opportunity.py)
    if opportunity:
        _section("Opportunity Assessment")

        opp_score_data = opportunity.get("opportunity_score", {})
        hist_perf = opportunity.get("historical_performance", {})
        comp_str = opportunity.get("competition_strength", {})

        s1, s2, s3 = st.columns(3)

        with s1:
            st.markdown(
                _kpi(
                    "Composite Opportunity Score",
                    f"{opp_score_data.get('score', 0):.1f} / 100",
                    f"Signal: {opp_score_data.get('signal', '--')}",
                    _opp_color(opp_score_data.get("score", 0)),
                ),
                unsafe_allow_html=True,
            )

        with s2:
            st.markdown(
                _kpi(
                    "Historical Performance (60% weight)",
                    f"{hist_perf.get('score', 0):.1f} / 100",
                    hist_perf.get("signal", "--"),
                    "accent",
                ),
                unsafe_allow_html=True,
            )

        with s3:
            comp_score = comp_str.get("score", 0)
            comp_color = "warning" if comp_score >= 60 else "success"
            st.markdown(
                _kpi(
                    "Competition Strength (40% weight)",
                    f"{comp_score:.1f} / 100",
                    comp_str.get("signal", "--"),
                    comp_color,
                ),
                unsafe_allow_html=True,
            )

        st.caption(
            "Opportunity formula balances historical success probability (60% weight) against market saturation / competitor strength (40% weight)."
        )


# ─────────────────────────────────────────────────────────────────────────────
# COMPETITION PAGE (TWO-COLUMN DASHBOARD)
# ─────────────────────────────────────────────────────────────────────────────

def page_competition():
    result = st.session_state.get("analysis_result", {})
    competition = result.get("competition_result", {})
    summary = competition.get("competition_summary", {})
    competitors = competition.get("competitors", [])

    st.markdown('<h2 class="main-title">Competition Intelligence</h2>', unsafe_allow_html=True)

    _section("Competition Summary")

    s1, s2, s3, s4 = st.columns(4)

    with s1:
        st.markdown(
            _kpi(
                "Competitors Found",
                str(summary.get("competitor_count_retrieved", "--")),
                "Nearby establishments",
            ),
            unsafe_allow_html=True,
        )

    with s2:
        st.markdown(
            _kpi(
                "Average Rating",
                f"{summary.get('avg_competitor_rating', 0):.2f} / 5",
                f"Median: {summary.get('median_competitor_rating', 0):.2f}",
            ),
            unsafe_allow_html=True,
        )

    with s3:
        st.markdown(
            _kpi(
                "Average Reviews",
                f"{summary.get('avg_competitor_reviews', 0):.0f}",
                f"Median: {summary.get('median_competitor_reviews', 0):.0f}",
            ),
            unsafe_allow_html=True,
        )

    with s4:
        st.markdown(
            _kpi(
                "High-Rating Competitors",
                str(summary.get("high_rating_competitors", "--")),
                f"High reviews: {summary.get('high_review_competitors', '--')}",
                "warning" if summary.get("high_rating_competitors", 0) > 5 else "success",
            ),
            unsafe_allow_html=True,
        )

    # Competitor Landscape & Map (Two-Column Layout)
    if competitors:
        _section("Competitor Landscape")

        col_table, col_map = st.columns([1, 1], gap="medium")

        dataframe = pd.DataFrame(competitors)
        columns = [
            col for col in [
                "name",
                "rating",
                "review_count",
                "competition_category",
            ]
            if col in dataframe.columns
        ]

        with col_table:
            st.markdown(
                '<div style="font-size:0.8rem;font-weight:700;color:#111827;margin-bottom:0.4rem;">'
                'Competitor Directory'
                '</div>',
                unsafe_allow_html=True,
            )
            if columns:
                display_df = dataframe[columns].rename(
                    columns={
                        "name": "Name",
                        "rating": "Rating",
                        "review_count": "Reviews",
                        "competition_category": "Category",
                    }
                )

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    height=380,
                )

        with col_map:
            st.markdown(
                '<div style="font-size:0.8rem;font-weight:700;color:#111827;margin-bottom:0.4rem;">'
                'Local Competitor Map'
                '</div>',
                unsafe_allow_html=True,
            )

            # 1. Clean and validate competitor coordinates
            has_lat = "latitude" in dataframe.columns
            has_lon = "longitude" in dataframe.columns

            valid_comps = pd.DataFrame()
            if has_lat and has_lon:
                comp_clean = dataframe.copy()
                comp_clean["latitude"] = pd.to_numeric(comp_clean["latitude"], errors="coerce")
                comp_clean["longitude"] = pd.to_numeric(comp_clean["longitude"], errors="coerce")

                valid_mask = (
                    comp_clean["latitude"].notna()
                    & comp_clean["longitude"].notna()
                    & (comp_clean["latitude"].abs() <= 90)
                    & (comp_clean["longitude"].abs() <= 180)
                    & ((comp_clean["latitude"] != 0) | (comp_clean["longitude"] != 0))
                )
                valid_comps = comp_clean[valid_mask].copy()

            if valid_comps.empty:
                st.markdown(
                    f'<div style="background:#F9FAFB;border:1px dashed #D1D5DB;border-radius:8px;padding:2rem;text-align:center;color:#6B7280;height:380px;display:flex;flex-direction:column;justify-content:center;align-items:center;">'
                    '<div style="font-weight:600;font-size:0.95rem;color:#374151;margin-bottom:0.4rem;">Competitor coordinates are unavailable for this dataset.</div>'
                    f'<div style="font-size:0.82rem;">{len(dataframe)} competitor records were retrieved, but lack valid geographic coordinate data.</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                try:
                    # Target business location & coordinates
                    inputs = st.session_state.get("form_inputs", {})
                    target_loc = inputs.get("location") or competition.get("location") or "Target Location"
                    target_cuisine = inputs.get("cuisine") or "Proposed Concept"
                    target_name = inputs.get("business_name") or "Your Business"

                    target_lat = competition.get("latitude")
                    target_lon = competition.get("longitude")

                    if target_lat is not None and target_lon is not None:
                        try:
                            target_lat = float(target_lat)
                            target_lon = float(target_lon)
                        except (ValueError, TypeError):
                            target_lat = None
                            target_lon = None

                    if target_lat is None or target_lon is None:
                        target_lat = float(valid_comps["latitude"].mean())
                        target_lon = float(valid_comps["longitude"].mean())

                    center_lat = float(target_lat)
                    center_lon = float(target_lon)

                    # Prepare custom hover data
                    valid_comps["rating_num"] = pd.to_numeric(valid_comps.get("rating", 0), errors="coerce").fillna(0.0)
                    valid_comps["reviews_num"] = pd.to_numeric(valid_comps.get("review_count", 0), errors="coerce").fillna(0).astype(int)
                    valid_comps["cat_str"] = valid_comps.get("competition_category", "Direct").fillna("Direct").astype(str).str.capitalize()

                    custom_data = valid_comps[["rating_num", "reviews_num", "cat_str"]].values

                    map_figure = go.Figure()
                    ScatterMap = getattr(go, "Scattermap", None) or getattr(go, "Scattermapbox", None)

                    # Competitors trace (● Competitors)
                    map_figure.add_trace(
                        ScatterMap(
                            lat=valid_comps["latitude"].tolist(),
                            lon=valid_comps["longitude"].tolist(),
                            mode="markers",
                            marker=dict(
                                size=9,
                                color="#2563EB",
                                opacity=0.88,
                            ),
                            name="Competitors",
                            text=valid_comps["name"].fillna("Competitor").tolist(),
                            customdata=custom_data,
                            hovertemplate=(
                                "<b>%{text}</b><br><br>"
                                "Rating: %{customdata[0]:.1f} / 5<br>"
                                "Reviews: %{customdata[1]:,}<br>"
                                "Category: %{customdata[2]}<extra></extra>"
                            ),
                        )
                    )

                    # Target business trace (★ Target Business)
                    map_figure.add_trace(
                        ScatterMap(
                            lat=[center_lat],
                            lon=[center_lon],
                            mode="markers+text",
                            marker=dict(
                                size=16,
                                color="#EF4444",
                                symbol="circle",
                            ),
                            name=f"★ {target_name}",
                            text=[f"★ {target_name}"],
                            textposition="top right",
                            textfont=dict(
                                size=11,
                                color="#111827",
                                family='Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                            ),
                            hovertemplate=(
                                f"<b>★ {target_name}</b><br><br>"
                                f"Location: {target_loc}<br>"
                                f"Cuisine: {target_cuisine}<extra></extra>"
                            ),
                        )
                    )

                    map_style_layout = dict(
                        style="open-street-map",
                        center=dict(lat=center_lat, lon=center_lon),
                        zoom=13.5,
                    )

                    layout_kwargs = dict(
                        height=380,
                        paper_bgcolor="#FFFFFF",
                        plot_bgcolor="#FFFFFF",
                        margin=dict(l=0, r=0, t=0, b=0),
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=0.02,
                            xanchor="left",
                            x=0.02,
                            bgcolor="rgba(255, 255, 255, 0.92)",
                            bordercolor="#E5E7EB",
                            borderwidth=1,
                            font=dict(size=11, color="#374151"),
                        ),
                    )

                    if hasattr(go, "Scattermap"):
                        layout_kwargs["map"] = map_style_layout
                    else:
                        layout_kwargs["mapbox"] = map_style_layout

                    map_figure.update_layout(**layout_kwargs)

                    st.plotly_chart(map_figure, use_container_width=True)

                except Exception as error:
                    st.caption(f"Map rendering: {error}")
    else:
        st.info("No competitor data retrieved for this query.")


# ─────────────────────────────────────────────────────────────────────────────
# FINANCIALS PAGE (STRUCTURED GRID)
# ─────────────────────────────────────────────────────────────────────────────

def page_financials():
    result = st.session_state.get("analysis_result", {})
    financial = result.get("financial_result", {})
    inputs = st.session_state.get("form_inputs", {})

    st.markdown(
        '<h2 class="main-title">Financial Projections & Cost Model</h2>'
        '<div class="main-subtitle">Deterministic, assumption-based operating cost and revenue model.</div>',
        unsafe_allow_html=True,
    )

    if not financial:
        st.warning("No financial simulation data is available.")
        return

    st.markdown(
        """<div class="disclaimer">
            <strong>Important Planning Notice:</strong>
            Financial figures are deterministic calculations based strictly on your input assumptions.
            Estimated Operating Profit is <strong>NOT Net Profit</strong>. This model does not account for income tax,
            GST, loan interest, depreciation of equipment, platform commissions (Swiggy/Zomato), or owner drawings.
        </div>""",
        unsafe_allow_html=True,
    )

    _section("Executive Financial Summary")

    monthly_customers = financial.get("monthly_customers", 0)
    monthly_revenue = financial.get("monthly_revenue", 0.0)
    food_cost = financial.get("food_cost", 0.0)
    fixed_costs = financial.get("fixed_costs", 0.0)
    monthly_expenses = financial.get("monthly_expenses", 0.0)
    operating_profit = financial.get("estimated_operating_profit", 0.0)
    operating_margin = financial.get("operating_profit_margin", 0.0)
    break_even = financial.get("break_even_customers_per_day")

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(
            _kpi(
                "Monthly Customers",
                f"{monthly_customers:,}",
                f"{inputs.get('customers_per_day', 0)} / day",
                "accent",
            ),
            unsafe_allow_html=True,
        )

    with k2:
        st.markdown(
            _kpi(
                "Monthly Revenue",
                _inr(monthly_revenue),
                f"AOV: ₹{inputs.get('average_order_value', 0):,.0f}",
                "accent",
            ),
            unsafe_allow_html=True,
        )

    with k3:
        exp_color = "danger" if monthly_expenses > monthly_revenue else "warning"
        st.markdown(
            _kpi(
                "Total Monthly Expenses",
                _inr(monthly_expenses),
                f"Fixed: {_inr(fixed_costs)}",
                exp_color,
            ),
            unsafe_allow_html=True,
        )

    with k4:
        profit_color = "success" if operating_profit >= 0 else "danger"
        st.markdown(
            _kpi(
                "Est. Operating Profit",
                _inr(operating_profit),
                f"Margin: {operating_margin:.1f}%",
                profit_color,
            ),
            unsafe_allow_html=True,
        )

    k5, k6, k7, k8 = st.columns(4)

    with k5:
        margin_color = "success" if operating_margin >= 15 else ("warning" if operating_margin >= 0 else "danger")
        st.markdown(
            _kpi(
                "Operating Margin",
                f"{operating_margin:.1f}%",
                "Profit / Revenue",
                margin_color,
            ),
            unsafe_allow_html=True,
        )

    with k6:
        st.markdown(
            _kpi(
                "Food / Variable Cost",
                _inr(food_cost),
                f"{inputs.get('food_cost_percent', 0):.0f}% of revenue",
            ),
            unsafe_allow_html=True,
        )

    with k7:
        st.markdown(
            _kpi(
                "Total Fixed Costs",
                _inr(fixed_costs),
                "Rent + Staff + Ops",
            ),
            unsafe_allow_html=True,
        )

    with k8:
        break_even_text = f"{break_even:.1f} / day" if break_even is not None else "N/A"
        working_days = inputs.get("working_days", 30)
        be_sub = f"{int(break_even * working_days):,} / month" if break_even is not None else "Undefined"
        st.markdown(
            _kpi(
                "Break-even Point",
                break_even_text,
                be_sub,
                "accent",
            ),
            unsafe_allow_html=True,
        )

    _section("Financial Visualizations")

    c1, c2 = st.columns(2, gap="medium")

    with c1:
        st.markdown(
            '<div style="font-size:0.8rem;font-weight:700;color:#111827;margin-bottom:0.4rem;">'
            'Revenue vs Total Expenses vs Operating Profit'
            '</div>',
            unsafe_allow_html=True,
        )

        fig_bar = go.Figure()

        fig_bar.add_trace(
            go.Bar(
                name="Revenue",
                x=["Monthly"],
                y=[monthly_revenue],
                marker_color="#2563EB",
                text=[_inr(monthly_revenue)],
                textposition="auto",
            )
        )

        fig_bar.add_trace(
            go.Bar(
                name="Total Expenses",
                x=["Monthly"],
                y=[monthly_expenses],
                marker_color="#64748B",
                text=[_inr(monthly_expenses)],
                textposition="auto",
            )
        )

        fig_bar.add_trace(
            go.Bar(
                name="Est. Operating Profit",
                x=["Monthly"],
                y=[operating_profit],
                marker_color="#10B981" if operating_profit >= 0 else "#EF4444",
                text=[_inr(operating_profit)],
                textposition="auto",
            )
        )

        bar_cfg = _bar_config(310)
        bar_cfg["barmode"] = "group"
        bar_cfg["yaxis"]["tickprefix"] = "₹"
        fig_bar.update_layout(**bar_cfg)

        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        st.markdown(
            '<div style="font-size:0.8rem;font-weight:700;color:#111827;margin-bottom:0.4rem;">'
            'Operating Expense Breakdown'
            '</div>',
            unsafe_allow_html=True,
        )

        cost_breakdown = {
            "Rent": float(inputs.get("rent", 0.0)),
            "Staff Cost": float(inputs.get("staff_cost", 0.0)),
            "Utilities": float(inputs.get("utilities", 0.0)),
            "Marketing": float(inputs.get("marketing", 0.0)),
            "Other Expenses": float(inputs.get("other_expenses", 0.0)),
            "Food / Variable": float(food_cost),
        }

        active_costs = {k: v for k, v in cost_breakdown.items() if v > 0}

        if active_costs:
            fig_pie = go.Figure(
                data=[
                    go.Pie(
                        labels=list(active_costs.keys()),
                        values=list(active_costs.values()),
                        hole=0.58,
                        marker=dict(
                            colors=[
                                "#2563EB",
                                "#64748B",
                                "#0D9488",
                                "#F59E0B",
                                "#8B5CF6",
                                "#3B82F6",
                            ]
                        ),
                        textinfo="none",
                        hovertemplate="<b>%{label}</b><br>Amount: ₹%{value:,.0f}<br>Share: %{percent:.1%}<extra></extra>",
                    )
                ]
            )

            fig_pie.update_layout(
                **PLOT_DEFAULTS,
                height=310,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.08,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=11, color="#4B5563"),
                ),
                margin=dict(l=10, r=10, t=10, b=45),
            )

            st.plotly_chart(fig_pie, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# WHAT-IF COMPARISON RENDERERS (CLEAN UNINDENTED HTML)
# ─────────────────────────────────────────────────────────────────────────────

def _format_delta(abs_val, pct_val, is_currency=False, is_percent=False, invert=False):
    """Format an absolute and percentage delta into a styled HTML badge."""
    if abs_val is None:
        return '<span class="change-neu">N/A</span>'

    if abs_val > 0:
        css_class = "change-neg" if invert else "change-pos"
        sign = "+"
    elif abs_val < 0:
        css_class = "change-pos" if invert else "change-neg"
        sign = "-"
    else:
        css_class = "change-neu"
        sign = ""

    abs_num = abs(abs_val)
    if is_currency:
        if abs_num >= 100000:
            abs_str = f"{sign}₹{abs_num / 100000:.2f}L"
        else:
            abs_str = f"{sign}₹{abs_num:,.0f}"
    elif is_percent:
        abs_str = f"{sign}{abs_num:.1f}%"
    else:
        abs_str = f"{sign}{abs_num:.1f}"

    if pct_val is not None:
        pct_sign = "+" if pct_val >= 0 else ""
        pct_str = f" ({pct_sign}{pct_val:.1f}%)"
    else:
        pct_str = ""

    return f'<span class="{css_class}">{abs_str}{pct_str}</span>'


def _render_financial_comparison(comparison):
    """Render the comparison table, charts, and bullet points for financial What-If."""
    baseline = comparison.get("baseline", {})
    scenario = comparison.get("scenario", {})
    changes = comparison.get("changes", {})

    _section("Scenario Comparison Breakdown")

    metrics_config = [
        ("Monthly Revenue", "monthly_revenue", True, False, False),
        ("Monthly Expenses", "monthly_expenses", True, False, True),
        ("Est. Operating Profit", "estimated_operating_profit", True, False, False),
        ("Operating Margin", "operating_profit_margin", False, True, False),
        ("Break-Even (Cust/Day)", "break_even_customers_per_day", False, False, True),
    ]

    rows = []
    for label, key, is_curr, is_pct, inv in metrics_config:
        b_val = baseline.get(key)
        s_val = scenario.get(key)
        chg = changes.get(key, {})
        abs_val = chg.get("absolute")
        pct_val = chg.get("percentage")

        if is_curr:
            b_str = _inr(b_val)
            s_str = _inr(s_val)
        elif is_pct:
            b_str = f"{b_val:.1f}%" if b_val is not None else "N/A"
            s_str = f"{s_val:.1f}%" if s_val is not None else "N/A"
        else:
            b_str = f"{b_val:.1f}" if b_val is not None else "N/A"
            s_str = f"{s_val:.1f}" if s_val is not None else "N/A"

        delta_html = _format_delta(
            abs_val,
            pct_val,
            is_currency=is_curr,
            is_percent=is_pct,
            invert=inv,
        )

        rows.append(
            f'<tr><td><strong>{label}</strong></td>'
            f'<td class="metric">{b_str}</td>'
            f'<td class="metric">{s_str}</td>'
            f'<td>{delta_html}</td></tr>'
        )

    # Clean unindented string: zero CommonMark code-block wrapping
    table_html = (
        '<table class="comp-table">'
        '<thead><tr>'
        '<th>Metric</th><th>Baseline</th><th>What-If Scenario</th><th>Change (Delta)</th>'
        '</tr></thead>'
        '<tbody>' + ''.join(rows) + '</tbody>'
        '</table>'
    )

    st.markdown(table_html, unsafe_allow_html=True)

    _section("Scenario Visualizer")

    chart_keys = [
        ("Revenue", "monthly_revenue"),
        ("Expenses", "monthly_expenses"),
        ("Est. Operating Profit", "estimated_operating_profit"),
    ]

    labels = [item[0] for item in chart_keys]
    base_values = [baseline.get(item[1], 0.0) for item in chart_keys]
    scen_values = [scenario.get(item[1], 0.0) for item in chart_keys]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Baseline",
            x=labels,
            y=base_values,
            marker_color="#2563EB",
            text=[_inr(v) for v in base_values],
            textposition="outside",
        )
    )

    fig.add_trace(
        go.Bar(
            name="What-If",
            x=labels,
            y=scen_values,
            marker_color="#7C3AED",
            text=[_inr(v) for v in scen_values],
            textposition="outside",
        )
    )

    chart_cfg = _bar_config(300)
    chart_cfg["barmode"] = "group"
    chart_cfg["yaxis"]["tickprefix"] = "₹"
    fig.update_layout(**chart_cfg)

    st.plotly_chart(fig, use_container_width=True)

    statements = describe_financial_changes(comparison)
    if statements:
        _section("Calculated Directional Effects")
        for stmt in statements:
            st.markdown(f"- {stmt}")


def _render_ml_comparison(comparison, include_shap=False):
    """Render the comparison of ML predictions, probabilities, and SHAP."""
    baseline = comparison.get("baseline", {})
    scenario = comparison.get("scenario", {})
    changes = comparison.get("changes", {})

    _section("Prediction Outcome")

    b_pred = baseline.get("prediction", "--")
    s_pred = scenario.get("prediction", "--")
    pred_changed = changes.get("prediction_changed", False)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            _kpi(
                "Baseline Prediction",
                b_pred,
                "Random Forest model",
                _perf_color(b_pred),
            ),
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            _kpi(
                "What-If Prediction",
                s_pred,
                "Scenario model output",
                _perf_color(s_pred),
            ),
            unsafe_allow_html=True,
        )

    with c3:
        status_label = "CHANGED" if pred_changed else "UNCHANGED"
        status_color = "warning" if pred_changed else "accent"
        sub_text = "Classification shifted" if pred_changed else "Same predicted class"
        st.markdown(
            _kpi(
                "Prediction Status",
                status_label,
                sub_text,
                status_color,
            ),
            unsafe_allow_html=True,
        )

    _section("Probability Distribution Shift")

    b_probs = baseline.get("probabilities", {})
    s_probs = scenario.get("probabilities", {})
    ordered_classes = ["High", "Medium", "Low"]
    classes = [cls for cls in ordered_classes if cls in b_probs or cls in s_probs] or sorted(list(set(b_probs.keys()) | set(s_probs.keys())))

    if classes:
        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                name="Baseline",
                x=classes,
                y=[b_probs.get(cls, 0.0) * 100 for cls in classes],
                marker_color="#2563EB",
                text=[f"{b_probs.get(cls, 0.0) * 100:.1f}%" for cls in classes],
                textposition="outside",
            )
        )

        fig.add_trace(
            go.Bar(
                name="What-If",
                x=classes,
                y=[s_probs.get(cls, 0.0) * 100 for cls in classes],
                marker_color="#7C3AED",
                text=[f"{s_probs.get(cls, 0.0) * 100:.1f}%" for cls in classes],
                textposition="outside",
            )
        )

        prob_cfg = _bar_config(260)
        prob_cfg["barmode"] = "group"
        prob_cfg["yaxis"]["ticksuffix"] = "%"
        prob_cfg["yaxis"]["range"] = [0, 110]
        prob_cfg["legend"]["y"] = 1.15
        fig.update_layout(**prob_cfg)

        st.plotly_chart(fig, use_container_width=True)

    b_shap = baseline.get("shap")
    s_shap = scenario.get("shap")

    if include_shap and b_shap and s_shap:
        _section("SHAP Feature Attribution Comparison")
        st.caption(
            "Side-by-side comparison of features pushing the model toward the predicted class."
        )

        b_features = b_shap.get("top_features", [])
        s_features = s_shap.get("top_features", [])

        col_b, col_s = st.columns(2)

        with col_b:
            st.markdown(f"**Baseline: {b_pred}**")
            if b_features:
                bf_names = [_human_feature_name(f["feature"]) for f in b_features][::-1]
                bf_vals = [f["contribution"] for f in b_features][::-1]
                bf_cols = [
                    "#10B981" if f["direction"] == "positive" else "#EF4444"
                    for f in b_features
                ][::-1]

                fig_b = go.Figure(
                    go.Bar(
                        y=bf_names,
                        x=bf_vals,
                        orientation="h",
                        marker_color=bf_cols,
                        text=[f"{v:+.3f}" for v in bf_vals],
                        textposition="outside",
                    )
                )

                fig_b.update_layout(
                    plot_bgcolor="#FFFFFF",
                    paper_bgcolor="#FFFFFF",
                    font=dict(family='Inter, sans-serif', size=11, color="#374151"),
                    hoverlabel=dict(bgcolor="#111827", font_size=12, font_color="#FFFFFF"),
                    height=max(200, len(b_features) * 34 + 40),
                    showlegend=False,
                    xaxis=dict(
                        showgrid=True,
                        gridcolor="#E5E7EB",
                        gridwidth=1,
                        zeroline=True,
                        zerolinecolor="#94A3B8",
                        zerolinewidth=1.5,
                        tickfont=dict(color="#6B7280"),
                    ),
                    yaxis=dict(tickfont=dict(color="#111827")),
                    margin=dict(l=10, r=30, t=10, b=5),
                )

                st.plotly_chart(fig_b, use_container_width=True)
            else:
                st.info("No baseline SHAP features available.")

        with col_s:
            st.markdown(f"**What-If: {s_pred}**")
            if s_features:
                sf_names = [_human_feature_name(f["feature"]) for f in s_features][::-1]
                sf_vals = [f["contribution"] for f in s_features][::-1]
                sf_cols = [
                    "#10B981" if f["direction"] == "positive" else "#EF4444"
                    for f in s_features
                ][::-1]

                fig_s = go.Figure(
                    go.Bar(
                        y=sf_names,
                        x=sf_vals,
                        orientation="h",
                        marker_color=sf_cols,
                        text=[f"{v:+.3f}" for v in sf_vals],
                        textposition="outside",
                    )
                )

                fig_s.update_layout(
                    plot_bgcolor="#FFFFFF",
                    paper_bgcolor="#FFFFFF",
                    font=dict(family='Inter, sans-serif', size=11, color="#374151"),
                    hoverlabel=dict(bgcolor="#111827", font_size=12, font_color="#FFFFFF"),
                    height=max(200, len(s_features) * 34 + 40),
                    showlegend=False,
                    xaxis=dict(
                        showgrid=True,
                        gridcolor="#E5E7EB",
                        gridwidth=1,
                        zeroline=True,
                        zerolinecolor="#94A3B8",
                        zerolinewidth=1.5,
                        tickfont=dict(color="#6B7280"),
                    ),
                    yaxis=dict(tickfont=dict(color="#374151")),
                    margin=dict(l=10, r=30, t=10, b=5),
                )

                st.plotly_chart(fig_s, use_container_width=True)
            else:
                st.info("No scenario SHAP features available.")


# ─────────────────────────────────────────────────────────────────────────────
# WHAT-IF PAGE (SCENARIO PLANNING TOOL)
# ─────────────────────────────────────────────────────────────────────────────

def page_whatif():
    inputs = st.session_state.get("form_inputs", {})

    st.markdown(
        '<h2 class="main-title">What-If Scenario Planning</h2>'
        '<div class="main-subtitle">'
        'Simulate operational and market adjustments against your baseline business model.'
        '</div>',
        unsafe_allow_html=True,
    )

    tab_fin, tab_ml = st.tabs(
        ["Financial What-If", "ML Performance What-If"]
    )

    # ── TAB 1: FINANCIAL WHAT-IF ─────────────────────────────────────────────
    with tab_fin:
        c_base_info, c_scen_desc = st.columns(2, gap="medium")
        with c_base_info:
            st.markdown(
                f'<div class="kpi-card" style="text-align:left;padding:0.85rem 1rem;">'
                f'<div class="kpi-label" style="text-align:left;">CURRENT BUSINESS (Baseline Assumptions)</div>'
                f'<strong>Customers:</strong> {int(inputs.get("customers_per_day", 100))}/day &nbsp;|&nbsp; '
                f'<strong>AOV:</strong> {_inr(inputs.get("average_order_value", 400))} &nbsp;|&nbsp; '
                f'<strong>Food Cost:</strong> {float(inputs.get("food_cost_percent", 32.0)):.1f}%<br>'
                f'<strong>Rent:</strong> {_inr(inputs.get("rent", 60000))} &nbsp;|&nbsp; '
                f'<strong>Staff:</strong> {_inr(inputs.get("staff_cost", 50000))} &nbsp;|&nbsp; '
                f'<strong>Utilities:</strong> {_inr(inputs.get("utilities", 15000))}'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c_scen_desc:
            st.markdown(
                f'<div class="kpi-card" style="text-align:left;padding:0.85rem 1rem;">'
                f'<div class="kpi-label" style="text-align:left;">WHAT-IF SCENARIO (Planning Objectives)</div>'
                f'<div style="font-size:0.82rem;color:#4B5563;line-height:1.45;">'
                f'Adjust operating assumptions below to evaluate calculated effects on monthly revenue, '
                f'expense burden, operating profit margin, and break-even customer volume.'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

        with st.form("whatif_fin_form"):
            c1, c2, c3 = st.columns(3)

            with c1:
                wi_cust = st.number_input(
                    "Customers Per Day",
                    min_value=0,
                    max_value=5000,
                    value=int(inputs.get("customers_per_day", 100)),
                    step=5,
                    key="wi_fin_cust",
                )
                wi_rent = st.number_input(
                    "Monthly Rent (₹)",
                    min_value=0,
                    max_value=2000000,
                    value=int(inputs.get("rent", 60000)),
                    step=5000,
                    key="wi_fin_rent",
                )

            with c2:
                wi_aov = st.number_input(
                    "Average Order Value (₹)",
                    min_value=0,
                    max_value=10000,
                    value=int(inputs.get("average_order_value", 400)),
                    step=25,
                    key="wi_fin_aov",
                )
                wi_staff = st.number_input(
                    "Staff Cost (₹)",
                    min_value=0,
                    max_value=2000000,
                    value=int(inputs.get("staff_cost", 50000)),
                    step=5000,
                    key="wi_fin_staff",
                )

            with c3:
                wi_fc_pct = st.slider(
                    "Food Cost (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(inputs.get("food_cost_percent", 32.0)),
                    step=0.5,
                    key="wi_fin_fc",
                )
                wi_util = st.number_input(
                    "Utilities (₹)",
                    min_value=0,
                    max_value=500000,
                    value=int(inputs.get("utilities", 15000)),
                    step=1000,
                    key="wi_fin_util",
                )

            c4, c5 = st.columns(2)
            with c4:
                wi_mkt = st.number_input(
                    "Marketing (₹)",
                    min_value=0,
                    max_value=500000,
                    value=int(inputs.get("marketing", 10000)),
                    step=1000,
                    key="wi_fin_mkt",
                )
            with c5:
                wi_other = st.number_input(
                    "Other Expenses (₹)",
                    min_value=0,
                    max_value=500000,
                    value=int(inputs.get("other_expenses", 5000)),
                    step=1000,
                    key="wi_fin_other",
                )

            fin_submitted = st.form_submit_button(
                "Run Financial Scenario",
                type="primary",
                use_container_width=True,
            )

        if fin_submitted:
            base_fin_inputs = {
                "customers_per_day": float(inputs.get("customers_per_day", 100)),
                "average_order_value": float(inputs.get("average_order_value", 400)),
                "rent": float(inputs.get("rent", 60000)),
                "staff_cost": float(inputs.get("staff_cost", 50000)),
                "food_cost_percent": float(inputs.get("food_cost_percent", 32.0)),
                "utilities": float(inputs.get("utilities", 15000)),
                "marketing": float(inputs.get("marketing", 10000)),
                "other_expenses": float(inputs.get("other_expenses", 5000)),
                "working_days": float(inputs.get("working_days", 30)),
            }

            scen_fin_inputs = {
                "customers_per_day": float(wi_cust),
                "average_order_value": float(wi_aov),
                "rent": float(wi_rent),
                "staff_cost": float(wi_staff),
                "food_cost_percent": float(wi_fc_pct),
                "utilities": float(wi_util),
                "marketing": float(wi_mkt),
                "other_expenses": float(wi_other),
                "working_days": float(inputs.get("working_days", 30)),
            }

            try:
                # Bug 1 Fix: call compare_financial_scenarios with positional arguments
                fin_comparison = compare_financial_scenarios(
                    base_fin_inputs,
                    scen_fin_inputs,
                )
                st.session_state.whatif_result = fin_comparison
                st.session_state.whatif_type = "financial"
            except Exception as e:
                st.error(f"Financial comparison failed: {e}")

        if (
            st.session_state.get("whatif_type") == "financial"
            and "whatif_result" in st.session_state
        ):
            _render_financial_comparison(st.session_state.whatif_result)

    # ── TAB 2: ML PERFORMANCE WHAT-IF ────────────────────────────────────────
    with tab_ml:
        st.markdown(
            '<div style="font-size:0.86rem;color:#4B5563;margin-bottom:1rem;">'
            'Modify business characteristics to see how the Random Forest classifier shifts predicted performance.'
            '</div>',
            unsafe_allow_html=True,
        )

        with st.form("whatif_ml_form"):
            m1, m2, m3 = st.columns(3)

            rest_types = [
                "Casual Dining", "Quick Bites", "Fine Dining", "Cafe",
                "Delivery", "Beverage Shop", "Food Court", "Bakery",
            ]
            current_type = inputs.get("primary_rest_type", "Casual Dining")
            type_idx = rest_types.index(current_type) if current_type in rest_types else 0

            with m1:
                wi_cuisine = st.text_input(
                    "Primary Cuisine",
                    value=inputs.get("primary_cuisine", "North Indian"),
                    key="wi_ml_cuisine",
                )
                wi_online = st.selectbox(
                    "Online Ordering",
                    [1, 0],
                    index=0 if inputs.get("online_order", 1) == 1 else 1,
                    format_func=lambda x: "Yes" if x else "No",
                    key="wi_ml_online",
                )

            with m2:
                wi_type = st.selectbox(
                    "Business Type",
                    rest_types,
                    index=type_idx,
                    key="wi_ml_type",
                )
                wi_table = st.selectbox(
                    "Table Booking",
                    [0, 1],
                    index=0 if inputs.get("book_table", 0) == 0 else 1,
                    format_func=lambda x: "Yes" if x else "No",
                    key="wi_ml_table",
                )

            with m3:
                wi_cost = st.number_input(
                    "Approx Cost for Two (₹)",
                    min_value=100,
                    max_value=10000,
                    value=int(inputs.get("approx_costfor_two_people", 800)),
                    step=50,
                    key="wi_ml_cost",
                )
                wi_cuisine_cnt = st.number_input(
                    "Cuisine Count",
                    min_value=1,
                    max_value=20,
                    value=int(inputs.get("cuisine_count", 2)),
                    step=1,
                    key="wi_ml_ccnt",
                )

            bands = ["Budget", "Low", "Medium", "High", "Premium"]
            current_band = inputs.get("cost_band", "Medium")
            band_idx = bands.index(current_band) if current_band in bands else 2

            m4, m5 = st.columns(2)
            with m4:
                wi_band = st.selectbox(
                    "Cost Band",
                    bands,
                    index=band_idx,
                    key="wi_ml_band",
                )
            with m5:
                wi_shap_toggle = st.checkbox(
                    "Compute SHAP Feature Attribution for Scenario",
                    value=False,
                    key="wi_ml_shap_toggle",
                    help="Calculates SHAP values for the What-If scenario. May take a few extra seconds.",
                )

            ml_submitted = st.form_submit_button(
                "Run ML Performance Scenario",
                type="primary",
                use_container_width=True,
            )

        if ml_submitted:
            res = st.session_state.get("analysis_result", {})
            loc_res = res.get("location_result", {})
            loc_keys = [
                "historical_restaurant_count",
                "location_median_cost",
                "location_online_order_rate",
                "location_book_table_rate",
                "location_cuisine_diversity",
                "location_business_type_diversity",
            ]
            loc_ctx = {}
            for k in loc_keys:
                if k in loc_res:
                    loc_ctx[k] = loc_res[k]
                elif k in inputs:
                    loc_ctx[k] = inputs[k]
            if len(loc_ctx) < len(loc_keys):
                from src.analysis.location_context import get_location_context
                fallback_loc = get_location_context(inputs.get("location", "Koramangala"))
                for k in loc_keys:
                    if k not in loc_ctx and k in fallback_loc:
                        loc_ctx[k] = fallback_loc[k]

            base_ml_inputs = {
                "location": inputs.get("location", "Koramangala"),
                "primary_cuisine": inputs.get("primary_cuisine", "North Indian"),
                "primary_rest_type": inputs.get("primary_rest_type", "Casual Dining"),
                "cuisine_count": int(inputs.get("cuisine_count", 2)),
                "approx_costfor_two_people": float(inputs.get("approx_costfor_two_people", 800)),
                "cost_band": inputs.get("cost_band", "Medium"),
                "online_order": int(inputs.get("online_order", 1)),
                "book_table": int(inputs.get("book_table", 0)),
                **loc_ctx,
            }

            scen_ml_inputs = {
                "location": inputs.get("location", "Koramangala"),
                "primary_cuisine": wi_cuisine.strip(),
                "primary_rest_type": wi_type,
                "cuisine_count": int(wi_cuisine_cnt),
                "approx_costfor_two_people": float(wi_cost),
                "cost_band": wi_band,
                "online_order": int(wi_online),
                "book_table": int(wi_table),
                **loc_ctx,
            }

            with st.spinner("Evaluating scenario against ML model..."):
                try:
                    # Bug 1 Fix: call compare_ml_scenarios with positional arguments
                    ml_comparison = compare_ml_scenarios(
                        base_ml_inputs,
                        scen_ml_inputs,
                        include_shap=wi_shap_toggle,
                    )
                    st.session_state.whatif_ml_result = ml_comparison
                    st.session_state.whatif_type = "ml"
                    st.session_state.whatif_include_shap = wi_shap_toggle
                except Exception as e:
                    st.error(f"ML scenario evaluation failed: {e}")

        if (
            st.session_state.get("whatif_type") == "ml"
            and "whatif_ml_result" in st.session_state
        ):
            _render_ml_comparison(
                st.session_state.whatif_ml_result,
                include_shap=st.session_state.get("whatif_include_shap", False),
            )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if "page" not in st.session_state:
        st.session_state.page = "landing"

    if "analysis_done" not in st.session_state:
        st.session_state.analysis_done = False

    page = st.session_state.page

    if page == "landing":
        page_landing()
        return

    sidebar()

    if not st.session_state.get("analysis_done", False):
        page_input()
        return

    if page == "overview":
        page_overview()
    elif page == "analysis":
        page_analysis()
    elif page == "competition":
        page_competition()
    elif page == "financials":
        page_financials()
    elif page == "whatif":
        page_whatif()
    elif page == "input":
        page_input()
    else:
        page_overview()


if __name__ == "__main__":
    main()
