"""VUB AI Research Group branding: palette, shared CSS and page header.

Used by all tabs so the look-and-feel is consistent. Drop a replacement logo
at ``assets/vub-ai_logo.png`` to update the brand mark everywhere.
"""

import base64
from pathlib import Path

import streamlit as st

# --- VUB AI palette ------------------------------------------------------- #
VUB_BLUE = "#003399"        # primary
VUB_BLUE_DARK = "#002673"
VUB_ORANGE = "#FF6600"      # accent
VUB_ORANGE_SOFT = "rgba(255,102,0,0.14)"
INK = "#1f2937"
MUTED = "#6b7280"
GRID = "rgba(0,51,153,0.12)"

_LOGO = Path(__file__).parent / "assets" / "vub-ai_logo.png"


def _logo_b64():
    try:
        return base64.b64encode(_LOGO.read_bytes()).decode()
    except Exception:
        return None


def inject_css():
    """Global CSS — call once near the top of the app."""
    st.markdown(f"""
    <style>
    .block-container {{padding-top: 1.1rem; padding-bottom: 1.5rem; max-width: 1400px;}}

    /* header */
    .vub-header {{
        display: flex; align-items: center; gap: 20px;
        border-bottom: 4px solid {VUB_ORANGE}; padding: 6px 4px 14px 4px; margin-bottom: 6px;
    }}
    .vub-header img {{height: 60px;}}
    .vub-header .titles h1 {{
        margin: 0; font-size: 1.5rem; font-weight: 800; color: {VUB_BLUE}; line-height: 1.1;
    }}
    .vub-header .titles p {{margin: 2px 0 0 0; color: {MUTED}; font-size: 0.9rem;}}

    /* tabs */
    .stTabs [data-baseweb="tab-list"] {{gap: 6px;}}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px 10px 0 0; padding: 8px 18px; font-weight: 600; color: {VUB_BLUE};
    }}
    .stTabs [aria-selected="true"] {{
        background: {VUB_BLUE}; color: #fff !important;
    }}

    /* hero banner inside a tab */
    .hero {{
        background: linear-gradient(110deg, {VUB_BLUE} 0%, {VUB_BLUE_DARK} 60%, #001a4d 100%);
        border-radius: 16px; padding: 20px 26px; color: #fff; margin-bottom: 16px;
        box-shadow: 0 10px 28px rgba(0,51,153,0.22);
        border-left: 6px solid {VUB_ORANGE};
    }}
    .hero h2 {{font-size: 1.3rem; margin: 0 0 4px 0; font-weight: 700;}}
    .hero p {{margin: 0; opacity: 0.93; font-size: 0.93rem;}}

    /* metric cards */
    .cards {{display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin: 6px 0;}}
    .card {{
        background: #fff; border: 1px solid #e8ecf3; border-radius: 14px; padding: 14px 16px;
        box-shadow: 0 2px 10px rgba(0,51,153,0.05);
    }}
    .card .label {{color: {MUTED}; font-size: 0.7rem; text-transform: uppercase; letter-spacing: .04em;}}
    .card .value {{color: {VUB_BLUE}; font-size: 1.5rem; font-weight: 800; line-height: 1.1;}}
    .card .unit {{color: {MUTED}; font-size: 0.8rem; font-weight: 500;}}

    .panel-title {{font-weight: 700; color: {VUB_BLUE}; margin: 6px 0 2px 2px;}}
    .badge {{
        display: inline-block; background: {VUB_ORANGE_SOFT}; color: {VUB_ORANGE};
        border-radius: 999px; padding: 2px 10px; font-size: 0.75rem; font-weight: 700; margin-left: 6px;
    }}
    .step {{
        background: {VUB_ORANGE}; color: #fff; border-radius: 999px; width: 26px; height: 26px;
        display: inline-flex; align-items: center; justify-content: center; font-weight: 800;
        margin-right: 8px; font-size: 0.85rem;
    }}
    .note {{
        background: #f5f8ff; border-left: 4px solid {VUB_BLUE}; border-radius: 8px;
        padding: 10px 14px; color: {INK}; font-size: 0.95rem; line-height: 1.5;
    }}

    /* concept "tiles" (the pop-up hint triggers) — bigger, card-like */
    div[data-testid="stPopover"] button {{
        font-size: 1.05rem !important; font-weight: 700 !important;
        color: {VUB_BLUE} !important;
        border: 1.5px solid {VUB_BLUE} !important; border-radius: 12px !important;
        background: #f5f8ff !important; padding: 10px 6px !important; width: 100%;
    }}
    div[data-testid="stPopover"] button:hover {{
        background: {VUB_ORANGE} !important; color: #fff !important;
        border-color: {VUB_ORANGE} !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def header(title, subtitle):
    """Render the VUB AI logo header."""
    b64 = _logo_b64()
    img = (f'<img src="data:image/png;base64,{b64}"/>' if b64 else "")
    st.markdown(f"""
    <div class="vub-header">
        {img}
        <div class="titles">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
