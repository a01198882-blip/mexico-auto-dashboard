from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pipeline import run_pipeline

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "cleaned_ventas.csv"

st.set_page_config(
    page_title="Mexico Auto Market | Tariff & Supply Shift (2016–2026)",
    page_icon="🚗",
    layout="wide",
)


@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        run_pipeline()
    df = pd.read_csv(DATA_PATH)
    df["FECHA"] = pd.to_datetime(df["FECHA"])
    return df


def add_event_markers(fig: go.Figure, show_events: bool = True) -> go.Figure:
    if not show_events:
        return fig
    events = [
        ("2020-04-01", "Apr 2020: COVID-19<br>Lockdown Shock", "#d62728", 0.98),
        ("2021-07-01", "2021–22: Chip<br>Shortage", "#ff7f0e", 0.85),
        ("2024-01-01", "Jan 2024: GAC & Geely<br>Enter Registry", "#9467bd", 0.98),
        ("2026-01-01", "Jan 2026: Non-FTA<br>Tariff Hike (up to 50%)", "#1f77b4", 0.82),
    ]
    for date_str, label, color, y_pos in events:
        fig.add_shape(
            type="line",
            x0=date_str, x1=date_str,
            y0=0, y1=1,
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
st.title("🚗 Behind the Tariff Wall: How Chinese Manufacturing Reshaped Mexican Showrooms")
st.markdown(
    """
    **Role:** Market Intelligence Analyst — Multi-Brand Mexican Automotive Dealership Group  
    **Stakeholders:** Executive Investment Committee & Brand Portfolio Directors  
    **Strategic Decision:** Which franchises and vehicle segments warrant showroom expansion in **2027** following Mexico's **January 2026 tariff hike** on non-FTA vehicle imports?
    """
)

# --- ON-SCREEN HONESTY & COVERAGE DISCLOSURE ---
st.warning(
    """
    **⚠️ INEGI RAIAVL Registry Coverage & Methodological Notice (Data Vintage: Nov 2026, Revised through Oct 2026):**
    * **Non-Reporting Brands:** **BYD** does not report to INEGI RAIAVL; actual Chinese-brand retail market share is higher than registry totals indicate.
    * **Panel Entry & Exit Distortions:** **GAC** joined the registry with retroactive figures back to **January 2024**; **Chirey** and **Omoda** stopped reporting after **March 2025**; **MOTORNATION** exited reporting in **mid/late 2026**. Use the sidebar toggle below to isolate the **29 brands that reported continuously across 2016–2026**.
    * **Brand Harmonization & Status:** `JETOUR` and `Jetour Soueast` are unified as **Jetour**; corporate groups (e.g., **Stellantis**) are standardized. Figures from **Nov 2023–Oct 2026** carry INEGI's *Cifras Revisadas* status.
    """
)

# --- SIDEBAR FILTERS ---
st.sidebar.header("🎛️ Dashboard Controls")

year_range = st.sidebar.slider(
    "1. Select Year Window",
    min_value=int(df["ANIO"].min()),
    max_value=int(df["ANIO"].max()),
    value=(2016, 2026),
)

all_segments = sorted(df["SEGMENTO"].unique())
selected_segments = st.sidebar.multiselect(
    "2. Vehicle Segment",
    options=all_segments,
    default=all_segments,
)

all_regimes = sorted(df["REGIMEN_ARANCELARIO"].unique())
selected_regimes = st.sidebar.multiselect(
    "3. Trade / Tariff Regime",
    options=all_regimes,
    default=all_regimes,
)

all_origins = sorted(df["BLOQUE_ORIGEN"].unique())
selected_origins = st.sidebar.multiselect(
    "4. Manufacturing Origin Block",
    options=all_origins,
    default=all_origins,
)

consistent_only = st.sidebar.checkbox(
    "Isolate Consistent 10-Year Panel (29 continuous brands)",
    value=False,
    help="Removes mid-period entrants (MG, Chirey, GAC, Geely, etc.) to verify organic market trends.",
)

show_annotations = st.sidebar.checkbox("Show Historical Event Annotations", value=True)

# Apply filters
mask = (
    (df["ANIO"].between(year_range[0], year_range[1]))
    & (df["SEGMENTO"].isin(selected_segments))
    & (df["REGIMEN_ARANCELARIO"].isin(selected_regimes))
    & (df["BLOQUE_ORIGEN"].isin(selected_origins))
)
if consistent_only:
    mask &= df["PANEL_CONSISTENTE_10Y"]

filtered_df = df[mask].copy()

if filtered_df.empty:
    st.error("No data matches your current filter selection. Please widen your filters in the sidebar.")
    st.stop()

# --- KPI SUMMARY ROW (SEASONALLY ALIGNED JAN–OCT YTD) ---
ytd_2025 = filtered_df[(filtered_df["ANIO"] == 2025) & (filtered_df["ID_MES"] <= 10)]["UNI_VEH"].sum()
ytd_2026 = filtered_df[(filtered_df["ANIO"] == 2026) & (filtered_df["ID_MES"] <= 10)]["UNI_VEH"].sum()
ytd_growth = ((ytd_2026 - ytd_2025) / ytd_2025 * 100) if ytd_2025 > 0 else 0.0

china_2026 = filtered_df[
    (filtered_df["ANIO"] == 2026) & (filtered_df["ID_MES"] <= 10) & (filtered_df["DESC_PAIS_ORIGEN"] == "China")
]["UNI_VEH"].sum()
china_share_2026 = (china_2026 / ytd_2026 * 100) if ytd_2026 > 0 else 0.0

legacy_china_2026 = filtered_df[
    (filtered_df["ANIO"] == 2026)
    & (filtered_df["ID_MES"] <= 10)
    & (filtered_df["DESC_PAIS_ORIGEN"] == "China")
    & (filtered_df["TIPO_MARCA"] == "Legacy / Non-Chinese Brand")
]["UNI_VEH"].sum()
legacy_pct_of_china = (legacy_china_2026 / china_2026 * 100) if china_2026 > 0 else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Filtered Period Volume", f"{filtered_df['UNI_VEH'].sum():,.0f} units")
k2.metric("Jan–Oct 2026 YTD Sales", f"{ytd_2026:,.0f} units", f"{ytd_growth:+.1f}% vs Jan–Oct 2025")
k3.metric("Made-in-China Share (2026 YTD)", f"{china_share_2026:.1f}%", f"{china_2026:,.0f} vehicles")
k4.metric("Sold by Legacy Brands (of China-Made)", f"{legacy_pct_of_china:.1f}%", f"{legacy_china_2026:,.0f} captive imports")

st.divider()

# --- CHAPTER 1: 10-YEAR SEASONALLY ADJUSTED TRAJECTORY ---
st.subheader("1. A Decade of Shocks: 12-Month Rolling Sales & YoY Momentum")
st.caption(
    "Because Mexican auto retail spikes every December, 12-month rolling totals and Year-over-Year (YoY) % changes reveal true structural trends across the 2020 pandemic, the 2021–2022 chip shortage, and 2026 tariffs."
)

monthly = (
    df[(df["SEGMENTO"].isin(selected_segments)) & (df["REGIMEN_ARANCELARIO"].isin(selected_regimes)) & (df["BLOQUE_ORIGEN"].isin(selected_origins))]
    .groupby("FECHA", as_index=False)["UNI_VEH"]
    .sum()
    .sort_values("FECHA")
)
if consistent_only:
    monthly = (
        df[(df["SEGMENTO"].isin(selected_segments)) & (df["REGIMEN_ARANCELARIO"].isin(selected_regimes)) & (df["BLOQUE_ORIGEN"].isin(selected_origins)) & (df["PANEL_CONSISTENTE_10Y"])]
        .groupby("FECHA", as_index=False)["UNI_VEH"]
        .sum()
        .sort_values("FECHA")
    )

monthly["ROLLING_12M"] = monthly["UNI_VEH"].rolling(12).sum()
monthly["YOY_PCT"] = monthly["UNI_VEH"].pct_change(12) * 100
monthly_view = monthly[monthly["FECHA"].dt.year.between(year_range[0], year_range[1])]

col_c1, col_c2 = st.columns(2)
with col_c1:
    fig_roll = px.line(
        monthly_view.dropna(subset=["ROLLING_12M"]),
        x="FECHA",
        y="ROLLING_12M",
        title="12-Month Rolling Total Retail Sales (Units)",
        labels={"FECHA": "Month", "ROLLING_12M": "12-Month Rolling Units"},
    )
    fig_roll.update_traces(line=dict(color="#1f77b4", width=3))
    fig_roll = add_event_markers(fig_roll, show_annotations)
    st.plotly_chart(fig_roll, use_container_width=True)

with col_c2:
    fig_yoy = px.bar(
        monthly_view.dropna(subset=["YOY_PCT"]),
        x="FECHA",
        y="YOY_PCT",
        title="Monthly Year-over-Year (YoY %) Growth",
        labels={"FECHA": "Month", "YOY_PCT": "YoY % Change"},
        color=monthly_view.dropna(subset=["YOY_PCT"])["YOY_PCT"] >= 0,
        color_discrete_map={True: "#2ca02c", False: "#d62728"},
    )
    fig_yoy.update_layout(showlegend=False)
    fig_yoy = add_event_markers(fig_yoy, show_annotations)
    st.plotly_chart(fig_yoy, use_container_width=True)

# --- CHAPTER 2: TWO FACES OF MADE IN CHINA ---
st.subheader("2. The Hidden Story: Legacy Automakers Drive Over Half of Chinese Imports")
st.caption(
    "Crossing Brand (`MARCA`) with Country of Origin (`DESC_PAIS_ORIGEN`) reveals that traditional Western/Asian brands (led by General Motors, KIA, and Ford) account for more Made-in-China sales in Mexico than new Chinese brands."
)

col_c3, col_c4 = st.columns([1.2, 1])

with col_c3:
    china_df = filtered_df[filtered_df["DESC_PAIS_ORIGEN"] == "China"]
    china_by_yr = china_df.groupby(["ANIO", "TIPO_MARCA"], as_index=False)["UNI_VEH"].sum()
    fig_china_split = px.bar(
        china_by_yr,
        x="ANIO",
        y="UNI_VEH",
        color="TIPO_MARCA",
        title="Made-in-China Vehicles Sold in Mexico: Chinese Brands vs. Legacy Brands",
        labels={"ANIO": "Year", "UNI_VEH": "Units Sold", "TIPO_MARCA": "Brand Ownership"},
        color_discrete_map={
            "Legacy / Non-Chinese Brand": "#1f77b4",
            "Chinese Brand": "#ff7f0e",
        },
        barmode="stack",
    )
    st.plotly_chart(fig_china_split, use_container_width=True)

with col_c4:
    top_china_brands = (
        china_df.groupby(["MARCA_CLEAN", "TIPO_MARCA"], as_index=False)["UNI_VEH"]
        .sum()
        .sort_values("UNI_VEH", ascending=False)
        .head(10)
        .sort_values("UNI_VEH", ascending=True)
    )
    fig_top_brands = px.bar(
        top_china_brands,
        x="UNI_VEH",
        y="MARCA_CLEAN",
        color="TIPO_MARCA",
        orientation="h",
        title="Top 10 Brands Importing Made-in-China Vehicles (Selected Period)",
        labels={"UNI_VEH": "Units Sold", "MARCA_CLEAN": "Brand", "TIPO_MARCA": "Brand Type"},
        color_discrete_map={
            "Legacy / Non-Chinese Brand": "#1f77b4",
            "Chinese Brand": "#ff7f0e",
        },
    )
    st.plotly_chart(fig_top_brands, use_container_width=True)

# --- CHAPTER 3: STRESS-TESTING THE JANUARY 2026 TARIFF WALL ---
st.subheader("3. Stress-Testing the January 2026 Tariff Hike (FTA vs. Non-FTA Imports)")
st.caption(
    "Despite Mexico raising tariffs up to 50% on non-FTA countries on January 1, 2026, Non-FTA retail deliveries held strong through Oct 2026—indicating aggressive pre-tariff inventory stockpiling in late 2025."
)

regime_monthly = (
    filtered_df.groupby(["FECHA", "REGIMEN_ARANCELARIO"], as_index=False)["UNI_VEH"].sum()
)
fig_regime = px.line(
    regime_monthly,
    x="FECHA",
    y="UNI_VEH",
    color="REGIMEN_ARANCELARIO",
    title="Monthly Retail Sales by Trade & Tariff Regime",
    labels={"FECHA": "Month", "UNI_VEH": "Monthly Units Sold", "REGIMEN_ARANCELARIO": "Tariff Regime"},
    color_discrete_map={
        "Domestic (0% Tariff)": "#2ca02c",
        "FTA / ACE Preferential Import": "#1f77b4",
        "Non-FTA Import (2026 Tariff Target)": "#d62728",
    },
)
fig_regime = add_event_markers(fig_regime, show_annotations)
st.plotly_chart(fig_regime, use_container_width=True)

# --- CHAPTER 4: SEGMENT BATTLEGROUND ---
st.subheader("4. Segment Battleground: Where Imports Captured Market Share")
seg_origin = (
    filtered_df.groupby(["SEGMENTO", "BLOQUE_ORIGEN"], as_index=False)["UNI_VEH"].sum()
)
fig_seg = px.bar(
    seg_origin,
    x="SEGMENTO",
    y="UNI_VEH",
    color="BLOQUE_ORIGEN",
    title="Vehicle Sales Mix by Segment and Manufacturing Origin Block",
    labels={"SEGMENTO": "Vehicle Segment", "UNI_VEH": "Units Sold", "BLOQUE_ORIGEN": "Origin Block"},
    barmode="stack",
)
st.plotly_chart(fig_seg, use_container_width=True)

# --- STRATEGIC RECOMMENDATIONS & LIMITATIONS ---
st.divider()
col_rec, col_lim = st.columns(2)

with col_rec:
    st.subheader("🎯 Recommendations for the Dealership Committee")
    st.markdown(
        """
        1. **Hedge 2027 Tariff Exposure:** Prioritize capital allocation toward franchises with **USMCA, Japanese, or Brazilian (ACE 55)** supply chains, as pre-tariff inventory buffers for non-FTA imports will deplete heading into 2027.
        2. **Protect Entry-Level SUV & Subcompact Floorplans:** Over 75% of Chinese-built volume targets **SUVs** and **Subcompacts**—segments vacated by legacy brands' move upmarket.
        3. **Evaluate Captive-Import Risk at Legacy Franchises:** Even GM, Ford, and KIA dealerships carry substantial Chinese-origin exposure on entry models; audit model-level sourcing before expanding floorplan credit lines.
        """
    )

with col_lim:
    st.subheader("🔍 What INEGI RAIAVL Cannot See (Data Limitations)")
    st.markdown(
        """
        * **Unreported Brands (BYD):** Because RAIAVL relies on voluntary AMIA member reporting, **BYD** and smaller EV importers are invisible here—supplement with **AMDA / state registration** data.
        * **No Transaction Prices or Margins:** RAIAVL tracks physical unit volume (`UNI_VEH`), not dealer invoice prices, financing incentives, or tariff pass-through to consumers.
        * **No State-Level Retail Geography (in this table):** While the hybrid/EV table includes state breakdowns, total light-vehicle retail sales are reported only at the national level.
        """
    )