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

filtered_df = df[mask].copy()

if filtered_df.empty:
    st.error("No vehicles match your current filter combination. Please widen your filters in the sidebar.")
    st.stop()

# --- KPI SUMMARY ROW (SEASONALLY ALIGNED JAN–OCT YTD + SEGMENT SHIFT) ---
ytd_2025 = filtered_df[(filtered_df["ANIO"] == 2025) & (filtered_df["ID_MES"] <= 10)]["UNI_VEH"].sum()
ytd_2026 = filtered_df[(filtered_df["ANIO"] == 2026) & (filtered_df["ID_MES"] <= 10)]["UNI_VEH"].sum()
ytd_growth = ((ytd_2026 - ytd_2025) / ytd_2025 * 100) if ytd_2025 > 0 else 0.0

base_kpi_mask = pd.Series(True, index=df.index)
if selected_brands:
    base_kpi_mask &= df["MARCA_CLEAN"].isin(selected_brands)
if consistent_only:
    base_kpi_mask &= df["PANEL_CONSISTENTE_10Y"]
kpi_base = df[base_kpi_mask]

tot_2016 = kpi_base[(kpi_base["ANIO"] == 2016) & (kpi_base["ID_MES"] <= 10)]["UNI_VEH"].sum()
suv_2016 = kpi_base[(kpi_base["ANIO"] == 2016) & (kpi_base["ID_MES"] <= 10) & (kpi_base["SEGMENTO"] == "SUV's")]["UNI_VEH"].sum()
suv_share_2016 = (suv_2016 / tot_2016 * 100) if tot_2016 > 0 else 0.0

tot_2026_all = kpi_base[(kpi_base["ANIO"] == 2026) & (kpi_base["ID_MES"] <= 10)]["UNI_VEH"].sum()
suv_2026 = kpi_base[(kpi_base["ANIO"] == 2026) & (kpi_base["ID_MES"] <= 10) & (kpi_base["SEGMENTO"] == "SUV's")]["UNI_VEH"].sum()
suv_share_2026 = (suv_2026 / tot_2026_all * 100) if tot_2026_all > 0 else 0.0

sedan_2026 = kpi_base[
    (kpi_base["ANIO"] == 2026)
    & (kpi_base["ID_MES"] <= 10)
    & (kpi_base["SEGMENTO"].isin(["Subcompactos", "Compactos"]))
]["UNI_VEH"].sum()
sedan_share_2026 = (sedan_2026 / tot_2026_all * 100) if tot_2026_all > 0 else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Filtered Period Volume", f"{filtered_df['UNI_VEH'].sum():,.0f} units")
k2.metric("Jan–Oct 2026 YTD Sales", f"{ytd_2026:,.0f} units", f"{ytd_growth:+.1f}% vs Jan–Oct 2025")
k3.metric("SUV Market Share (2026 YTD)", f"{suv_share_2026:.1f}%", f"{suv_share_2026 - suv_share_2016:+.1f} pts vs 2016")
k4.metric("Compact + Subcompact Share", f"{sedan_share_2026:.1f}%", f"{sedan_2026:,.0f} units in 2026 YTD")

st.divider()

# --- CHAPTER 1: MARKET RECOVERY & 10-YEAR CYCLE ---
st.subheader("1. The Big Picture: A Decade of Market Shocks & Full Recovery")
st.caption(
    "Using 12-month rolling totals and Year-over-Year (YoY) % growth removes December seasonal spikes and shows how retail volume recovered past pre-pandemic levels after the 2020 lockdown and 2021–2022 chip shortage."
)

base_monthly_mask = df["SEGMENTO"].isin(selected_segments)
if selected_brands:
    base_monthly_mask &= df["MARCA_CLEAN"].isin(selected_brands)
if consistent_only:
    base_monthly_mask &= df["PANEL_CONSISTENTE_10Y"]

monthly = (
    df[base_monthly_mask]
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

# --- CHAPTER 2: THE CROSSOVER MOMENT (SUVs vs SEDANS) ---
st.subheader("2. The Crossover Moment: How SUVs Overtook Traditional Sedans")
st.caption(
    "Tracking annual market share (%) by segment reveals the structural shift in Mexican consumer demand: Subcompacts and Compacts steadily lost ground while SUVs climbed from ~20% to ~40% of the entire market."
)

col_s1, col_s2 = st.columns([1.25, 1])

with col_s1:
    seg_yr = (
        filtered_df.groupby(["ANIO", "SEGMENTO"], as_index=False)["UNI_VEH"]
        .sum()
    )
    yr_tot = seg_yr.groupby("ANIO")["UNI_VEH"].transform("sum")
    seg_yr["SHARE_PCT"] = (seg_yr["UNI_VEH"] / yr_tot) * 100

    seg_colors = {
        "SUV's": "#d62728",
        "Subcompactos": "#1f77b4",
        "Compactos": "#17becf",
        "Pick Ups": "#2ca02c",
        "De Lujo": "#9467bd",
        "Minivans": "#8c564b",
        "Deportivos": "#e377c2",
    }

    fig_crossover = px.line(
        seg_yr,
        x="ANIO",
        y="SHARE_PCT",
        color="SEGMENTO",
        markers=True,
        title="Market Share (%) Trajectory by Vehicle Segment",
        labels={"ANIO": "Year", "SHARE_PCT": "Share of Retail Sales (%)", "SEGMENTO": "Segment"},
        color_discrete_map=seg_colors,
    )
    fig_crossover.update_traces(line=dict(width=2))
    fig_crossover.for_traces(
        lambda t: t.update(line=dict(width=4.5)) if t.name in {"SUV's", "Subcompactos", "Compactos"} else None
    )
    fig_crossover.update_layout(yaxis=dict(ticksuffix="%"))
    st.plotly_chart(fig_crossover, use_container_width=True)

with col_s2:
    milestone_years = [y for y in [2016, 2021, 2026] if y in filtered_df["ANIO"].unique()]
    if len(milestone_years) < 2:
        milestone_years = sorted(filtered_df["ANIO"].unique())

    mix_df = (
        filtered_df[filtered_df["ANIO"].isin(milestone_years)]
        .groupby(["ANIO", "MACRO_CATEGORIA"], as_index=False)["UNI_VEH"]
        .sum()
    )
    mix_tot = mix_df.groupby("ANIO")["UNI_VEH"].transform("sum")
    mix_df["SHARE_PCT"] = (mix_df["UNI_VEH"] / mix_tot) * 100
    mix_df["ANIO_STR"] = mix_df["ANIO"].astype(str)

    fig_mix = px.bar(
        mix_df,
        x="ANIO_STR",
        y="SHARE_PCT",
        color="MACRO_CATEGORIA",
        title="Showroom Mix Shift: Cars vs. SUVs & Pick Ups",
        labels={"ANIO_STR": "Year", "SHARE_PCT": "Share of Total Sales (%)", "MACRO_CATEGORIA": "Body Style"},
        color_discrete_map={
            "SUVs": "#d62728",
            "Traditional Cars (Subcompact & Compact)": "#1f77b4",
            "Pick Ups": "#2ca02c",
            "Niche (Minivans, Luxury & Sports)": "#7f7f7f",
        },
        text=mix_df["SHARE_PCT"].apply(lambda v: f"{v:.0f}%" if v >= 6 else ""),
    )
    fig_mix.update_layout(
        barmode="stack",
        yaxis=dict(range=[0, 100], ticksuffix="%"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="left", x=0),
    )
    fig_mix.update_traces(textposition="inside", insidetextanchor="middle")
    st.plotly_chart(fig_mix, use_container_width=True)

# --- CHAPTER 3: WHO WON THE SUV BOOM? ---
st.subheader("3. Brand Battleground: Who Won the SUV Boom?")
st.caption(
    "Comparing top brands in the selected segment(s) reveals both the entrenched leaders (General Motors, Nissan, Volkswagen) and the fast-growing challengers (KIA, Mazda, MG Motor) capturing showroom demand."
)

col_b1, col_b2 = st.columns([1.15, 1])

with col_b1:
    focus_seg = st.selectbox(
        "Inspect Top 10 Brands Inside Specific Segment:",
        options=["SUV's", "Subcompactos", "Compactos", "Pick Ups", "All Selected Segments"],
        index=0,
    )
    if focus_seg == "All Selected Segments":
        brand_slice = filtered_df
    else:
        brand_slice = filtered_df[filtered_df["SEGMENTO"] == focus_seg]

    top_brands = (
        brand_slice.groupby("MARCA_CLEAN", as_index=False)["UNI_VEH"]
        .sum()
        .sort_values("UNI_VEH", ascending=False)
        .head(10)
    )
    brand_order = top_brands["MARCA_CLEAN"].tolist()

    fig_top_brands = px.bar(
        top_brands,
        x="UNI_VEH",
        y="MARCA_CLEAN",
        orientation="h",
        title=f"Top 10 Brands in {focus_seg} ({year_range[0]}–{year_range[1]})",
        labels={"UNI_VEH": "Cumulative Units Sold", "MARCA_CLEAN": "Brand"},
        category_orders={"MARCA_CLEAN": brand_order},
        color="UNI_VEH",
        color_continuous_scale="Blues",
    )
    fig_top_brands.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_top_brands, use_container_width=True)

with col_b2:
    top6_names = top_brands["MARCA_CLEAN"].head(6).tolist()
    brand_trend = (
        brand_slice[brand_slice["MARCA_CLEAN"].isin(top6_names)]
        .groupby(["ANIO", "MARCA_CLEAN"], as_index=False)["UNI_VEH"]
        .sum()
    )
    fig_brand_trend = px.line(
        brand_trend,
        x="ANIO",
        y="UNI_VEH",
        color="MARCA_CLEAN",
        markers=True,
        title=f"Annual Sales Trajectory of Top 6 Brands ({focus_seg})",
        labels={"ANIO": "Year", "UNI_VEH": "Annual Units Sold", "MARCA_CLEAN": "Brand"},
    )
    st.plotly_chart(fig_brand_trend, use_container_width=True)

# --- CHAPTER 4: SEASONALITY & INVENTORY TIMING ---
st.subheader("4. Inventory Timing: The Predictable December Showroom Surge")
st.caption(
    "Mexican retail sales follow a sharp seasonal rhythm—dipping in Q1 and spiking every December during year-end clearance. Inventory managers must build stock in October–November ahead of peak foot traffic."
)

month_names = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}
season_df = (
    filtered_df.groupby(["ANIO", "ID_MES"], as_index=False)["UNI_VEH"]
    .sum()
)
piv_heat = (
    season_df.pivot(index="ANIO", columns="ID_MES", values="UNI_VEH")
    .rename(columns=month_names)
)

fig_heat = px.imshow(
    piv_heat,
    labels=dict(x="Month", y="Year", color="Units Sold"),
    x=piv_heat.columns,
    y=piv_heat.index,
    aspect="auto",
    color_continuous_scale="YlOrRd",
    title="Monthly Retail Sales Heatmap (Units Sold by Month & Year)",
)
fig_heat.update_yaxes(dtick=1)
st.plotly_chart(fig_heat, use_container_width=True)

# --- STRATEGIC RECOMMENDATIONS & LIMITATIONS ---
st.divider()
col_rec, col_lim = st.columns(2)

with col_rec:
    st.subheader("🎯 Recommendations for Showroom & Inventory Planning")
    st.markdown(
        """
        1. **Reallocate Floor Space to ~45% SUVs / ~15% Pick Ups:** Traditional sedans (`Compactos` + `Subcompactos`) have lost nearly 20 percentage points of market share since 2016; downsizing sedan display bays frees prime floor space for high-turn compact and subcompact SUVs.
        2. **Anchor Franchise Mix with Proven SUV Leaders:** Balance high-volume legacy franchises (**General Motors, Nissan, Volkswagen**) with fast-growing SUV challengers (**KIA, Mazda, MG Motor**) to capture both repeat buyers and first-time SUV upgraders.
        3. **Stage Floorplan Credit for Q4 Peak:** Use the seasonal heatmap to expand credit lines in **October–November** ahead of the recurring **December sales spike**, then trim inventory in **January–February** to avoid carrying costs.
        """
    )

with col_lim:
    st.subheader("🔍 What INEGI RAIAVL Cannot See (Data Limitations)")
    st.markdown(
        """
        * **Unreported Brands (BYD):** Because RAIAVL relies on voluntary AMIA member reporting, **BYD** and smaller EV entrants do not appear here—meaning actual SUV and electrified demand is even larger than registry totals show.
        * **No Dealer Margins or Transaction Prices:** RAIAVL tracks physical unit volume (`UNI_VEH`), not gross profit per vehicle, financing incentives, or days-on-lot inventory aging.
        * **No Model-Size Split Inside `SUV's`:** INEGI groups subcompact, compact, mid-size, and full-size crossovers into a single `SUV's` label, requiring model-level (`MODELO`) drill-downs for exact trim ordering.
        """
    )