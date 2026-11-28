from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pipeline import run_pipeline

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "cleaned_ventas.csv"

CONFIG_DIR = BASE_DIR / ".streamlit"
CONFIG_DIR.mkdir(exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "config.toml"
if not CONFIG_FILE.exists():
    CONFIG_FILE.write_text('[theme]\nbase="light"\nprimaryColor="#003366"\n', encoding="utf-8")

st.set_page_config(
    page_title="The SUV Takeover | Mexico Auto Retail (2016–2026)",
    page_icon="🚙",
    layout="wide",
)

st.markdown(
    """
    <style>
        html, body, [class*="css"] {
            font-size: 21px !important;
        }
        h1 {
            font-size: 2.75rem !important;
            font-weight: 800 !important;
            line-height: 1.15 !important;
            color: #0F172A !important;
        }
        h2, h3 {
            font-size: 1.95rem !important;
            font-weight: 700 !important;
            margin-top: 0.7rem !important;
            color: #0F172A !important;
        }
        .stCaption, [data-testid="stCaptionContainer"] p {
            font-size: 1.2rem !important;
            line-height: 1.45 !important;
            color: #334155 !important;
        }
        [data-testid="stMetricLabel"] p {
            font-size: 1.2rem !important;
            font-weight: 700 !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 2.55rem !important;
            font-weight: 800 !important;
        }
        [data-testid="stMetricDelta"] {
            font-size: 1.15rem !important;
            font-weight: 700 !important;
        }
        .kpi-label {
            font-size: 1.15rem;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 4px;
        }
        .kpi-number {
            font-size: 2.55rem;
            font-weight: 800;
            color: #0F172A;
            line-height: 1.1;
        }
        .kpi-unit {
            font-size: 1.25rem;
            font-weight: 600;
            color: #475569;
            margin-left: 4px;
        }
        .kpi-pill-pos {
            display: inline-block;
            margin-top: 8px;
            padding: 3px 10px;
            border-radius: 999px;
            background-color: #E6F4EA;
            color: #137333;
            font-size: 1.05rem;
            font-weight: 700;
        }
        .kpi-pill-neg {
            display: inline-block;
            margin-top: 8px;
            padding: 3px 10px;
            border-radius: 999px;
            background-color: #FCE8E6;
            color: #A61C1C;
            font-size: 1.05rem;
            font-weight: 700;
        }
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
            font-size: 1.12rem !important;
        }
        .exec-card {
            background-color: #F8FAFC;
            border-left: 6px solid #003366;
            padding: 20px 24px;
            border-radius: 8px;
            font-size: 1.14rem;
            line-height: 1.65;
            color: #0F172A;
        }
        .warn-card {
            background-color: #FFF7ED;
            border-left: 6px solid #B34700;
            padding: 20px 24px;
            border-radius: 8px;
            font-size: 1.14rem;
            line-height: 1.65;
            color: #0F172A;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

COLOR_NAVY = "#003366"      
COLOR_ORANGE = "#B34700"    
GRAY_DARK = "#5A6577"      
GRAY_LIGHT = "#CBD5E1"     


def style_plotly(fig: go.Figure, height: int = 520) -> go.Figure:
    """Applies large, legible typography across every chart element."""
    fig.update_layout(
        height=height,
        template="plotly_white",
        font=dict(size=19, color="#0F172A"),
        title=dict(font=dict(size=25, color="#0F172A")),
        legend=dict(font=dict(size=18), title_font=dict(size=19)),
        margin=dict(t=85, b=70, l=75, r=45),
    )
    fig.update_xaxes(
        title_font=dict(size=20, color="#0F172A"),
        tickfont=dict(size=18, color="#1E293B"),
        showgrid=False,
    )
    fig.update_yaxes(
        title_font=dict(size=20, color="#0F172A"),
        tickfont=dict(size=18, color="#1E293B"),
        gridcolor="#E2E8F0",
    )
    return fig


@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        run_pipeline()
    df = pd.read_csv(DATA_PATH)
    df["FECHA"] = pd.to_datetime(df["FECHA"])
    body_map = {
        "SUV's": "SUVs",
        "Subcompactos": "Traditional Cars",
        "Compactos": "Traditional Cars",
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
        ("2020-04-01", "Apr 2020: COVID Shock", COLOR_ORANGE, 0.98),
        ("2021-07-01", "2021–22: Chip Shortage", GRAY_DARK, 0.84),
        ("2024-01-01", "Jan 2024: GAC & Geely Join", COLOR_NAVY, 0.98),
        ("2026-01-01", "Jan 2026: Tariff Hike", COLOR_ORANGE, 0.82),
    ]
    for date_str, label, color, y_pos in events:
        fig.add_shape(
            type="line",
            x0=date_str,
            x1=date_str,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color=color, width=2.2, dash="dash"),
        )
        fig.add_annotation(
            x=date_str,
            y=y_pos,
            yref="paper",
            text=f"<b>{label}</b>",
            showarrow=False,
            xanchor="left",
            font=dict(size=15, color=color),
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor=color,
            borderwidth=1.2,
            borderpad=4,
        )
    return fig


@st.dialog("📋 Executive Brief & INEGI Data Coverage", width="large")
def show_project_brief():
    st.markdown(
        """
        ### 🎯 Strategic Context
        * **Role:** Inventory & Product Planning Analyst — Mexican Dealership Group
        * **Stakeholders:** Showroom Operations Directors & Franchise Investment Committee
        * **2027 Decision:** Reallocate floor space & capital from **Sedans** into **SUVs & Pick Ups**, and choose anchor brands.
        * **Data:** INEGI RAIAVL *Ventas al público* (`2016–2026`, *Cifras Revisadas* through Oct 2026).

        ---
        ### ⚠️ Registry Coverage Notice
        * **Missing Brands:** **BYD** does not report to INEGI RAIAVL; true SUV & EV share is higher than registry totals.
        * **Panel Shifts:** **GAC** joined retroactively in **Jan 2024**; **Chirey & Omoda** exited after **Mar 2025**; **MOTORNATION** exited in **late 2026**. Use the sidebar toggle for the **29 continuous brands**.
        * **Harmonization:** `JETOUR` & `Jetour Soueast` are unified as **Jetour**; corporate groups (**Stellantis**) are standardized.
        """
    )
    if st.button("Explore Dashboard →", type="primary", use_container_width=True):
        st.rerun()


if "brief_shown" not in st.session_state:
    st.session_state["brief_shown"] = True
    show_project_brief()

df = load_data()

head_col1, head_col2 = st.columns([4, 1.1])
with head_col1:
    st.title("🚙 The SUV Takeover: How Mexican Buyers Abandoned Traditional Sedans")
    st.caption(
        "2027 Dealership Portfolio Strategy | Reallocating Floor Space from Sedans to SUVs & Pick Ups"
    )
with head_col2:
    st.write("")
    if st.button("📋 Project Brief & Data Notes", use_container_width=True):
        show_project_brief()

st.sidebar.header("🎛️ Showroom Filters")

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

all_brands = sorted(df["MARCA_CLEAN"].unique())
selected_brands = st.sidebar.multiselect(
    "3. Brand (All if Empty)",
    options=all_brands,
    default=[],
    help="Leave blank for the full market, or select specific franchises.",
)

consistent_only = st.sidebar.checkbox(
    "Consistent 10-Year Panel (29 continuous brands)",
    value=False,
    help="Excludes mid-period registry entrants/exits (MG, Chirey, GAC, Geely, etc.).",
)

show_annotations = st.sidebar.checkbox("Show Event Markers", value=True)

mask = (df["ANIO"].between(year_range[0], year_range[1])) & (df["SEGMENTO"].isin(selected_segments))
if selected_brands:
    mask &= df["MARCA_CLEAN"].isin(selected_brands)
if consistent_only:
    mask &= df["PANEL_CONSISTENTE_10Y"]

filtered_df = df[mask].copy()

if filtered_df.empty:
    st.error("No vehicles match your current filter combination. Please widen your filters in the sidebar.")
    st.stop()

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

k1, k2, k3, k4 = st.columns([1.2, 1.1, 1, 1])

with k1:
    st.markdown(
        f"""
        <div class="kpi-label">Filtered Period Volume</div>
        <div><span class="kpi-number">{filtered_df['UNI_VEH'].sum():,.0f}</span><span class="kpi-unit">units</span></div>
        """,
        unsafe_allow_html=True,
    )

with k2:
    pill_cls = "kpi-pill-pos" if ytd_growth >= 0 else "kpi-pill-neg"
    arrow = "↑" if ytd_growth >= 0 else "↓"
    st.markdown(
        f"""
        <div class="kpi-label">Jan–Oct 2026 YTD Sales</div>
        <div><span class="kpi-number">{ytd_2026:,.0f}</span><span class="kpi-unit">units</span></div>
        <div class="{pill_cls}">{arrow} {ytd_growth:+.1f}% vs Jan–Oct 2025</div>
        """,
        unsafe_allow_html=True,
    )

with k3:
    suv_diff = suv_share_2026 - suv_share_2016
    k3.metric("SUV Market Share (2026 YTD)", f"{suv_share_2026:.1f}%", f"{suv_diff:+.1f} pts vs 2016")

with k4:
    k4.metric("Compact + Subcompact Share", f"{sedan_share_2026:.1f}%", f"{sedan_2026:,.0f} units in 2026 YTD")

st.divider()

st.subheader("1. The Big Picture: A Decade of Market Shocks & Full Recovery")
st.caption(
    "12-month rolling totals and Year-over-Year (YoY) % growth remove December seasonal spikes and show full post-pandemic recovery."
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
    fig_roll.update_traces(line=dict(color=COLOR_NAVY, width=4.5))
    fig_roll = add_event_markers(fig_roll, show_annotations)
    fig_roll = style_plotly(fig_roll, height=520)
    st.plotly_chart(fig_roll, use_container_width=True)

with col_c2:
    fig_yoy = px.bar(
        monthly_view.dropna(subset=["YOY_PCT"]),
        x="FECHA",
        y="YOY_PCT",
        title="Monthly Year-over-Year (YoY %) Growth",
        labels={"FECHA": "Month", "YOY_PCT": "YoY % Change"},
        color=monthly_view.dropna(subset=["YOY_PCT"])["YOY_PCT"] >= 0,
        color_discrete_map={True: COLOR_NAVY, False: COLOR_ORANGE},
    )
    fig_yoy.update_layout(showlegend=False)
    fig_yoy = add_event_markers(fig_yoy, show_annotations)
    fig_yoy = style_plotly(fig_yoy, height=520)
    st.plotly_chart(fig_yoy, use_container_width=True)

st.subheader("2. The Crossover Moment: Showroom Mix Shift (Cars vs. SUVs & Pick Ups)")
st.caption(
    "Direct-labeled share trajectory: SUVs climbed from 21% to 40% while Traditional Cars dropped from 60% to 39%."
)

slope_df = (
    filtered_df.groupby(["ANIO", "MACRO_CATEGORIA"], as_index=False)["UNI_VEH"]
    .sum()
    .sort_values("ANIO")
)
yr_tot = slope_df.groupby("ANIO")["UNI_VEH"].transform("sum")
slope_df["SHARE_PCT"] = (slope_df["UNI_VEH"] / yr_tot) * 100

min_yr = int(slope_df["ANIO"].min())
max_yr = int(slope_df["ANIO"].max())
span_yrs = max(max_yr - min_yr, 1)

cat_styles = {
    "SUVs": {"color": COLOR_ORANGE, "width": 8.0, "label": "SUVs"},
    "Traditional Cars": {"color": COLOR_NAVY, "width": 6.0, "label": "Traditional Cars"},
    "Pick Ups": {"color": GRAY_DARK, "width": 4.8, "label": "Pick Ups"},
    "Niche (Minivans, Luxury & Sports)": {"color": "#94A3B8", "width": 4.0, "label": "Niche"},
}

fig_mix = go.Figure()

draw_order = [
    "Niche (Minivans, Luxury & Sports)",
    "Pick Ups",
    "Traditional Cars",
    "SUVs",
]

end_vals = {}
for cat in draw_order:
    sub_tmp = slope_df[slope_df["MACRO_CATEGORIA"] == cat].sort_values("ANIO")
    if not sub_tmp.empty:
        end_vals[cat] = sub_tmp["SHARE_PCT"].iloc[-1]

right_yshifts = {cat: 0 for cat in draw_order}
if "SUVs" in end_vals and "Traditional Cars" in end_vals:
    if abs(end_vals["SUVs"] - end_vals["Traditional Cars"]) < 4.5:
        if end_vals["SUVs"] >= end_vals["Traditional Cars"]:
            right_yshifts["SUVs"] = 12
            right_yshifts["Traditional Cars"] = -12
        else:
            right_yshifts["Traditional Cars"] = 12
            right_yshifts["SUVs"] = -12

for cat in draw_order:
    sub = slope_df[slope_df["MACRO_CATEGORIA"] == cat].sort_values("ANIO")
    if sub.empty:
        continue
    style_cfg = cat_styles.get(cat, {"color": GRAY_DARK, "width": 4.5, "label": cat})
    color = style_cfg["color"]
    width = style_cfg["width"]
    short_label = style_cfg["label"]

    x_vals = sub["ANIO"].tolist()
    y_vals = sub["SHARE_PCT"].tolist()

    fig_mix.add_trace(
        go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines",
            line=dict(color=color, width=width),
            showlegend=False,
            hovertemplate=f"<b>{short_label}</b><br>Year: %{{x}}<br>Share: %{{y:.1f}}%<extra></extra>",
        )
    )

    fig_mix.add_trace(
        go.Scatter(
            x=[x_vals[0], x_vals[-1]],
            y=[y_vals[0], y_vals[-1]],
            mode="markers",
            marker=dict(color=color, size=16 if cat == "SUVs" else 13),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    fig_mix.add_annotation(
        x=x_vals[0],
        y=y_vals[0],
        text=f"<b>{short_label}   {y_vals[0]:.0f}%</b>" if cat == "SUVs" else f"{short_label}   {y_vals[0]:.0f}%",
        xanchor="right",
        xshift=-16,
        showarrow=False,
        font=dict(size=20 if cat == "SUVs" else 18, color=color),
    )

    if len(x_vals) > 1:
        fig_mix.add_annotation(
            x=x_vals[-1],
            y=y_vals[-1],
            text=f"<b>{y_vals[-1]:.0f}%</b>" if cat == "SUVs" else f"{y_vals[-1]:.0f}%",
            xanchor="left",
            xshift=16,
            yshift=right_yshifts.get(cat, 0),
            showarrow=False,
            font=dict(size=20 if cat == "SUVs" else 18, color=color),
        )

fig_mix = style_plotly(fig_mix, height=620)
fig_mix.update_layout(
    title=dict(
        text="Share of Mexican Retail Sales by Body Style (%)<br><span style='font-size:17px;color:#475569;'>Percentage of total passenger & light-truck retail units sold annually</span>",
        x=0.01,
        xanchor="left",
    ),
    showlegend=False,
    margin=dict(t=115, b=70, l=245, r=95),
    xaxis=dict(
        title="",
        range=[min_yr - span_yrs * 0.04, max_yr + span_yrs * 0.04],
        dtick=1 if span_yrs <= 11 else 2,
        showline=True,
        linecolor="#94A3B8",
        linewidth=1.5,
        ticks="outside",
        ticklen=6,
        tickcolor="#94A3B8",
        showgrid=False,
    ),
    yaxis=dict(
        visible=False,
        range=[-3, max(slope_df["SHARE_PCT"].max() * 1.15, 68)],
    ),
)
st.plotly_chart(fig_mix, use_container_width=True)

st.subheader("3. Brand Battleground: Who Won the SUV Boom?")
st.caption(
    "Select any segment below—the #1 volume leader is automatically highlighted in Burnt Orange while rivals are grayed out."
)

focus_seg = st.selectbox(
    "Select Segment to Inspect Top Brands:",
    options=["SUV's", "Subcompactos", "Compactos", "Pick Ups", "All Selected Segments"],
    index=0,
)
if focus_seg == "All Selected Segments":
    brand_slice = filtered_df
else:
    brand_slice = filtered_df[filtered_df["SEGMENTO"] == focus_seg]

col_b1, col_b2 = st.columns([1.15, 1])

with col_b1:
    top_brands = (
        brand_slice.groupby("MARCA_CLEAN", as_index=False)["UNI_VEH"]
        .sum()
        .sort_values("UNI_VEH", ascending=False)
        .head(10)
    )
    brand_order = top_brands["MARCA_CLEAN"].tolist()
    leader_brand = brand_order[0] if brand_order else ""

    bar_colors = [COLOR_ORANGE if b == leader_brand else COLOR_NAVY for b in brand_order]

    fig_top_brands = px.bar(
        top_brands,
        x="UNI_VEH",
        y="MARCA_CLEAN",
        orientation="h",
        title=f"Top 10 Brands in {focus_seg} ({year_range[0]}–{year_range[1]})",
        labels={"UNI_VEH": "Cumulative Units Sold", "MARCA_CLEAN": "Brand"},
        category_orders={"MARCA_CLEAN": brand_order},
        text=top_brands["UNI_VEH"].apply(lambda v: f" <b>{v:,.0f}</b>"),
    )
    fig_top_brands.update_traces(
        marker_color=bar_colors,
        textposition="outside",
        textfont=dict(size=17, color="#0F172A"),
        cliponaxis=False,
    )
    fig_top_brands = style_plotly(fig_top_brands, height=530)
    fig_top_brands.update_layout(margin=dict(r=125))
    st.plotly_chart(fig_top_brands, use_container_width=True)

with col_b2:
    top6_names = top_brands["MARCA_CLEAN"].head(6).tolist()
    brand_trend = (
        brand_slice[brand_slice["MARCA_CLEAN"].isin(top6_names)]
        .groupby(["ANIO", "MARCA_CLEAN"], as_index=False)["UNI_VEH"]
        .sum()
        .sort_values("ANIO")
    )

    fig_brand_trend = go.Figure()
    for brand in reversed(top6_names):
        if brand == leader_brand:
            continue
        sub = brand_trend[brand_trend["MARCA_CLEAN"] == brand]
        fig_brand_trend.add_trace(
            go.Scatter(
                x=sub["ANIO"],
                y=sub["UNI_VEH"],
                mode="lines+markers",
                name=brand,
                line=dict(color=GRAY_LIGHT, width=2.5),
                marker=dict(color=GRAY_LIGHT, size=6),
                hovertemplate=f"<b>{brand}</b><br>Year: %{{x}}<br>Units: %{{y:,.0f}}<extra></extra>",
            )
        )

    if leader_brand:
        sub_leader = brand_trend[brand_trend["MARCA_CLEAN"] == leader_brand]
        fig_brand_trend.add_trace(
            go.Scatter(
                x=sub_leader["ANIO"],
                y=sub_leader["UNI_VEH"],
                mode="lines+markers",
                name=f"★ {leader_brand} (#1)",
                line=dict(color=COLOR_ORANGE, width=5.5),
                marker=dict(color=COLOR_ORANGE, size=11),
                hovertemplate=f"<b>★ {leader_brand} (#1)</b><br>Year: %{{x}}<br>Units: %{{y:,.0f}}<extra></extra>",
            )
        )

    fig_brand_trend.update_layout(
        title=f"#1 Leader ({leader_brand}) vs. Top 5 Rivals ({focus_seg})",
        xaxis_title="Year",
        yaxis_title="Annual Units Sold",
    )
    fig_brand_trend = style_plotly(fig_brand_trend, height=530)
    st.plotly_chart(fig_brand_trend, use_container_width=True)

st.divider()
col_rec, col_lim = st.columns(2)

with col_rec:
    st.subheader("🎯 2027 Showroom Action Plan")
    st.markdown(
        """
        <div class="exec-card">
            <b>1. Reallocate Floor Space (~45% SUVs / ~15% Pick Ups):</b> Sedans dropped from <b>60% → 39%</b>; convert sedan bays into high-turn SUV displays.<br><br>
            <b>2. Pair #1 Leaders with Challengers:</b> Anchor inventory with volume leaders (<b>GM, Nissan, VW</b>) plus fast risers (<b>KIA, Mazda, MG</b>).<br><br>
            <b>3. Protect Pick Up Bays:</b> Pick Ups held a steady <b>13%–17%</b> share across every economic shock.
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_lim:
    st.subheader("🔍 INEGI RAIAVL Blind Spots")
    st.markdown(
        """
        <div class="warn-card">
            <b>• Unreported EV Entrants (BYD):</b> Non-reporting brands are excluded; real SUV & EV share is even higher.<br><br>
            <b>• Unit Volume Only:</b> Tracks retail units (<code>UNI_VEH</code>), not dealer gross margins, incentives, or days-on-lot.<br><br>
            <b>• Broad <code>SUV's</code> Bucket:</b> Groups subcompact through full-size SUVs; model-level drill-down is needed for trim orders.
        </div>
        """,
        unsafe_allow_html=True,
    )