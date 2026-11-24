from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pipeline import run_pipeline

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "cleaned_ventas.csv"

st.set_page_config(
    page_title="The SUV Takeover | Mexico Auto Retail (2016–2026)",
    page_icon="🚙",
    layout="wide",
)


@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        run_pipeline()
    df = pd.read_csv(DATA_PATH)
    df["FECHA"] = pd.to_datetime(df["FECHA"])
    # Create clean Body-Style Macro Category so stakeholders see Sedans vs. SUVs immediately
    body_map = {
        "SUV's": "SUVs",
        "Subcompactos": "Traditional Cars (Subcompact & Compact)",
        "Compactos": "Traditional Cars (Subcompact & Compact)",
        "Pick Ups": "Pick Ups",
        "Minivans": "Niche (Minivans, Luxury & Sports)",
        "De Lujo": "Niche (Minivans, Luxury & Sports)",
        "Deportivos": "Niche (Minivans, Luxury & Sports)",
    }
    df["MACRO_CATEGORIA"] = df["SEGMENTO"].map(body_map).fillna("Other")
    return df


def add_event_markers(fig: go.Figure, show_events: bool = True) -> go.Figure:
    if not show_events:
        return fig
    events = [
        ("2020-04-01", "Apr 2020: COVID-19<br>Lockdown Shock", "#d62728", 0.98),
        ("2021-07-01", "2021–22: Chip<br>Shortage", "#ff7f0e", 0.84),
        ("2024-01-01", "Jan 2024: GAC & Geely<br>Enter Registry", "#9467bd", 0.98),
        ("2026-01-01", "Jan 2026: Non-FTA<br>Tariff Hike", "#1f77b4", 0.82),
    ]
    for date_str, label, color, y_pos in events:
        fig.add_shape(
            type="line",
            x0=date_str,
            x1=date_str,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color=color, width=1.5, dash="dash"),
        )
        fig.add_annotation(
            x=date_str,
            y=y_pos,
            yref="paper",
            text=label,
            showarrow=False,
            xanchor="left",
            font=dict(size=10, color=color),
            bgcolor="rgba(255,255,255,0.85)",
        )
    return fig


df = load_data()

# --- HEADER & STAKEHOLDER CONTEXT ---
st.title("🚙 The SUV Takeover: How Mexican Buyers Abandoned Traditional Sedans")
st.markdown(
    """
    **Role:** Inventory & Product Planning Analyst — Multi-Brand Mexican Automotive Dealership Group  
    **Stakeholders:** Showroom Operations Directors & Floorplan Finance Committee  
    **Strategic Decision:** How much showroom floor space and working capital should we reallocate out of **Compact & Subcompact sedans** into **SUVs and Pick Ups** for **2027**?  
    **Table Used:** INEGI RAIAVL *Ventas al público* (`2016–2026`), crossing **Segment (`SEGMENTO`)**, **Brand (`MARCA`)**, and **Monthly Seasonality (`ANIO` / `ID_MES`)**.
    """
)

# --- ON-SCREEN HONESTY & COVERAGE DISCLOSURE ---
st.warning(
    """
    **⚠️ INEGI RAIAVL Registry Coverage & Methodological Notice (Data Vintage: Nov 2026, Revised through Oct 2026):**
    * **Non-Reporting Brands:** **BYD** does not report to INEGI RAIAVL; because BYD sells heavily in SUVs and compact EVs, true SUV retail share is even higher than registry totals show.
    * **Panel Entry & Exit Distortions:** **GAC** joined the registry with retroactive figures back to **January 2024**; **Chirey** and **Omoda** stopped reporting after **March 2025**; **MOTORNATION** exited reporting in **mid/late 2026**. Use the sidebar toggle below to isolate the **29 continuous brands** across 2016–2026.
    * **Harmonization & Vintage:** `JETOUR` and `Jetour Soueast` are standardized as **Jetour**; corporate groups (e.g., **Stellantis**) are unified. Sales from **Nov 2023–Oct 2026** reflect INEGI's *Cifras Revisadas*.
    """
)

# --- SIDEBAR FILTERS ---
st.sidebar.header("🎛️ Interactive Showroom Filters")

year_range = st.sidebar.slider(
    "1. Select Year Window",
    min_value=int(df["ANIO"].min()),
    max_value=int(df["ANIO"].max()),
    value=(2016, 2026),
)

all_segments = sorted(df["SEGMENTO"].unique())
selected_segments = st.sidebar.multiselect(
    "2. Filter by Vehicle Segment",
    options=all_segments,
    default=all_segments,
)

all_brands = sorted(df["MARCA_CLEAN"].unique())
selected_brands = st.sidebar.multiselect(
    "3. Filter by Brand (Optional — All Brands if Empty)",
    options=all_brands,
    default=[],
    help="Leave blank to analyze the entire national market, or select specific franchises (e.g., Nissan, General Motors, Toyota, KIA, MG Motor).",
)

consistent_only = st.sidebar.checkbox(
    "Isolate Consistent 10-Year Panel (29 continuous brands)",
    value=False,
    help="Excludes mid-period registry entrants/exits (MG, Chirey, GAC, Geely, etc.) to verify organic consumer demand.",
)

show_annotations = st.sidebar.checkbox("Show Historical Event Annotations", value=True)

# Apply filters
mask = (df["ANIO"].between(year_range[0], year_range[1])) & (df["SEGMENTO"].isin(selected_segments))
if selected_brands:
    mask &= df["MARCA_CLEAN"].isin(selected_brands)
if consistent_only:
    mask &= df["PANEL_CONSISTENTE_10Y"]

filtered_df = df[mask].copy