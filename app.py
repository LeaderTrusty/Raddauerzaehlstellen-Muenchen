import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium


# carto_key = st.secrets["CARTO_API_KEY"]
# m = folium.Map(
#       location=[48.141, 11.568],
#        zoom_start=12,
#       tiles=f"https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png?key={carto_key}",
#       attr="&copy; OpenStreetMap contributors &copy; CARTO",
#)

st.set_page_config(
    page_title="Munich Urban Mobility — Geospatial Dashboard",
    page_icon="🚲",
    layout="wide",
)

# Official Munich Raddauerzählstellen metadata & coordinates (GeoPortal München)
STATION_META = {
    "Arnulf": {
        "full_name": "Arnulfstraße",
        "address": "Arnulfstr. 9–11 (Südseite)",
        "lat": 48.14205,
        "lon": 11.55534,
        "note": "One-way cycle path near Hauptbahnhof; Direction 2 captures wrong-way cyclists.",
    },
    "Erhardt": {
        "full_name": "Erhardtstraße",
        "address": "Erhardtstr. (Deutsches Museum / Isar)",
        "lat": 48.13192,
        "lon": 11.58469,
        "note": "Major north-south Isar commuter spine right next to Deutsches Museum.",
    },
    "Hirsch": {
        "full_name": "Hirschgarten",
        "address": "Birketweg (Hirschgarten)",
        "lat": 48.14438,
        "lon": 11.51794,
        "note": "Key western corridor connecting Neuhausen-Nymphenburg and Laim.",
    },
    "Kreuther": {
        "full_name": "Bad-Kreuther-Straße",
        "address": "Bad-Kreuther-Str. / Joseph-Hörwick-Weg",
        "lat": 48.12194,
        "lon": 11.62417,
        "note": "Eastern suburban connector in Berg am Laim, active since 2008.",
    },
    "Margareten": {
        "full_name": "Margaretenstraße",
        "address": "Margaretenstr. (Harras / Sendling)",
        "lat": 48.12032,
        "lon": 11.53599,
        "note": "Southern commuter route passing through Sendling near Harras.",
    },
    "Olympia": {
        "full_name": "Olympiapark",
        "address": "Rudolf-Harbig-Weg (Olympiapark)",
        "lat": 48.16887,
        "lon": 11.55005,
        "note": "Northern route popular with both commuters and weekend park visitors.",
    },
}


@st.cache_data
def load_data():
    df = pd.read_csv("munich_bike_cleaned_2022_2026.csv", parse_dates=["date"])
    df["station"] = df["station"].astype(str).str.strip()
    return df


df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Dashboard Filters")

years = sorted(df["year"].dropna().unique().astype(int).tolist())
selected_years = st.sidebar.multiselect("Select Years", years, default=years)

all_stations = sorted(df["station"].dropna().unique().tolist())
selected_stations = st.sidebar.multiselect(
    "Active Counting Stations", all_stations, default=all_stations
)

exclude_outages = st.sidebar.checkbox("Exclude Sensor Outage Days", value=True)

# Filter dataframe
base_filtered = df[
    (df["year"].isin(selected_years)) & (df["station"].isin(selected_stations))
].copy()

filtered_df = (
    base_filtered[~base_filtered["is_outage"]].copy()
    if exclude_outages
    else base_filtered.copy()
)

# --- Header ---
st.title("🚲 Munich Urban Mobility — Interactive Geospatial Explorer")
st.markdown(
    "Click any counting station on the **Munich map** to inspect its commuter profile, "
    "peak records, and seasonal trends (2022–2026)."
)

if filtered_df.empty:
    st.warning("No data matches your current filter selection. Adjust the sidebar filters.")
    st.stop()

# --- Top City-Wide KPIs ---
total_trips = int(filtered_df["total_bikes"].sum())
avg_daily = int(filtered_df["total_bikes"].mean())
peak_row = filtered_df.loc[filtered_df["total_bikes"].idxmax()]
outage_days = int(base_filtered["is_outage"].sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Recorded Trips", f"{total_trips:,}")
c2.metric("City Avg. Daily Bikes / Station", f"{avg_daily:,}")
c3.metric(
    "All-Time Single-Day Peak",
    f"{int(peak_row['total_bikes']):,}",
    f"{peak_row['station']} ({peak_row['date'].strftime('%Y-%m-%d')})",
)
c4.metric("Sensor Outage Days Flagged", f"{outage_days:,}")

st.divider()

# --- Prepare Station Summary for Map ---
station_stats = (
    filtered_df.groupby("station")
    .agg(
        avg_daily=("total_bikes", "mean"),
        total_trips=("total_bikes", "sum"),
        max_day=("total_bikes", "max"),
    )
    .reset_index()
)

wd_we = (
    filtered_df.groupby(["station", "is_weekend"])["total_bikes"]
    .mean()
    .unstack()
    .rename(columns={False: "weekday_avg", True: "weekend_avg"})
)
station_stats = station_stats.merge(wd_we, on="station", how="left")
station_stats["commuter_ratio"] = (
    station_stats["weekday_avg"] / station_stats["weekend_avg"]
)

# Initialize session state for clicked station
available_stations = station_stats["station"].tolist()
if (
    "station_picker" not in st.session_state
    or st.session_state["station_picker"] not in available_stations
):
    st.session_state["station_picker"] = (
        "Erhardt" if "Erhardt" in available_stations else available_stations[0]
    )

# --- Main Section: Interactive Map + Clickable Station Deep Dive ---
col_map, col_detail = st.columns([1.35, 1], gap="large")

with col_map:
    st.subheader("🗺️ Munich Counting Stations Map")
    st.caption(
        "Circle size = Avg. daily ridership | Blue = Strong commuter corridor (Weekday > 1.2x Weekend) | Orange = Balanced / Leisure"
    )

    # Create minimalist Munich map
    m = folium.Map(
        location=[48.141, 11.568],
        zoom_start=12,
        tiles="OpenStreetMap",
    )

    max_avg = station_stats["avg_daily"].max()

    for _, row in station_stats.iterrows():
        st_name = row["station"]
        if st_name not in STATION_META:
            continue

        meta = STATION_META[st_name]
        ratio = row["commuter_ratio"] if pd.notna(row["commuter_ratio"]) else 1.0
        is_commuter = ratio >= 1.2
        color = "#1f4e79" if is_commuter else "#f28e2b"
        is_selected = st_name == st.session_state["station_picker"]

        # Scale radius proportionally between 10 and 24 px
        radius = 10 + (row["avg_daily"] / max_avg) * 14

        popup_html = f"""
        <div style="font-family: sans-serif; width: 210px;">
            <h4 style="margin: 0 0 4px 0; color: {color};">{meta['full_name']}</h4>
            <p style="margin: 0 0 6px 0; font-size: 12px; color: #555;">{meta['address']}</p>
            <hr style="margin: 4px 0;">
            <b>Avg. Daily:</b> {row['avg_daily']:,.0f} bikes<br>
            <b>Weekday Avg:</b> {row['weekday_avg']:,.0f}<br>
            <b>Weekend Avg:</b> {row['weekend_avg']:,.0f}<br>
            <b>Peak Day:</b> {row['max_day']:,.0f}
        </div>
        """

        folium.CircleMarker(
            location=[meta["lat"], meta["lon"]],
            radius=radius,
            color="#d62728" if is_selected else color,
            weight=3.5 if is_selected else 2,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            tooltip=f"{st_name} — {row['avg_daily']:,.0f} bikes/day (click to inspect)",
            popup=folium.Popup(popup_html, max_width=250),
        ).add_to(m)

    # Render map and listen ONLY to marker clicks (prevents flicker on zoom/pan)
    map_data = st_folium(
        m,
        use_container_width=True,
        height=490,
        returned_objects=["last_object_clicked_tooltip"],
    )

    # Update selected station if a marker was clicked
    clicked_tooltip = map_data.get("last_object_clicked_tooltip") if map_data else None
    if clicked_tooltip and clicked_tooltip != st.session_state.get("last_map_click"):
        for st_name in available_stations:
            if clicked_tooltip.startswith(st_name):
                st.session_state["last_map_click"] = clicked_tooltip
                st.session_state["station_picker"] = st_name
                st.rerun()

with col_detail:
    st.subheader("📍 Station Deep Dive")
    active_station = st.selectbox(
        "Active Station (click any dot on the map or pick here):",
        options=available_stations,
        key="station_picker",
    )

    meta = STATION_META.get(active_station, {})
    st_df = filtered_df[filtered_df["station"] == active_station]
    st_raw = base_filtered[base_filtered["station"] == active_station]
    st_row = station_stats[station_stats["station"] == active_station].iloc[0]

    # Station Info Card
    ratio = st_row["commuter_ratio"]
    corridor_badge = (
        "💼 Commuter Corridor" if pd.notna(ratio) and ratio >= 1.2 else "🌳 Balanced / Leisure Route"
    )
    st.markdown(f"**{meta.get('full_name', active_station)}** — {corridor_badge}")
    if meta:
        st.caption(f"📌 {meta['address']}  |  ℹ️ {meta['note']}")

    m1, m2, m3 = st.columns(3)
    m1.metric("Weekday Avg", f"{st_row['weekday_avg']:,.0f}")
    m2.metric("Weekend Avg", f"{st_row['weekend_avg']:,.0f}")
    m3.metric("Outage Days", f"{int(st_raw['is_outage'].sum()):,}")

    # Day-of-Week Bar Chart for the Clicked Station
    day_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]
    dow_df = (
        st_df.groupby("day_of_week")["total_bikes"]
        .mean()
        .reindex(day_order)
        .reset_index()
    )
    dow_df["Type"] = dow_df["day_of_week"].apply(
        lambda d: "Weekend" if d in ["Saturday", "Sunday"] else "Weekday"
    )

    fig_dow = px.bar(
        dow_df,
        x="day_of_week",
        y="total_bikes",
        color="Type",
        color_discrete_map={"Weekday": "#1f4e79", "Weekend": "#f28e2b"},
        title=f"Weekly Rhythm: {meta.get('full_name', active_station)}",
        labels={"day_of_week": "", "total_bikes": "Avg. Daily Bikes"},
        text_auto=",.0f",
    )
    fig_dow.update_layout(
        height=310,
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=False,
        xaxis_tickangle=-25,
    )
    st.plotly_chart(fig_dow, use_container_width=True)

st.divider()

# --- Row 2: Interactive Seasonality Heatmap & Weather Elasticity ---
tab1, tab2, tab3 = st.tabs(
    ["🔥 Seasonality Heatmap", "🌦️ Weather Elasticity", "🛠️ Data Quality Audit"]
)

with tab1:
    scope = st.radio(
        "Heatmap Scope:",
        [f"Selected Station ({active_station})", "All Active Stations (Average)"],
        horizontal=True,
    )
    heat_source = st_df if scope.startswith("Selected") else filtered_df

    month_names = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    heat_pivot = (
        heat_source.groupby(["year", "month"])["total_bikes"]
        .mean()
        .unstack()
        .reindex(columns=range(1, 13))
    )
    heat_pivot.columns = month_names

    fig_heat = px.imshow(
        heat_pivot,
        text_auto=",.0f",
        aspect="auto",
        color_continuous_scale="YlGnBu",
        labels=dict(x="Month", y="Year", color="Avg Bikes/Day"),
        title=f"Monthly Cycling Intensity — {scope}",
    )
    fig_heat.update_yaxes(type="category")
    fig_heat.update_layout(height=380)
    st.plotly_chart(fig_heat, use_container_width=True)

with tab2:
    weather_df = (
        filtered_df.groupby("date")
        .agg(
            avg_bikes=("total_bikes", "mean"),
            max_temp_c=("max_temp_c", "first"),
            precipitation_mm=("precipitation_mm", "first"),
        )
        .dropna()
        .reset_index()
    )

    bins = [-0.1, 0.0, 5.0, 15.0, float("inf")]
    labels = ["Dry (0 mm)", "Light Rain (0.1–5 mm)", "Moderate (5–15 mm)", "Heavy Rain (15+ mm)"]
    weather_df["rain_category"] = pd.cut(
        weather_df["precipitation_mm"], bins=bins, labels=labels
    )

    w_left, w_right = st.columns([1.4, 1])

    with w_left:
        fig_scatter = px.scatter(
            weather_df,
            x="max_temp_c",
            y="avg_bikes",
            color="rain_category",
            hover_data={"date": "|%Y-%m-%d", "precipitation_mm": ":.1f"},
            color_discrete_sequence=["#2a9d8f", "#4e79a7", "#f28e2b", "#e15759"],
            opacity=0.65,
            title="Temperature vs. Daily Ridership (Hover for Exact Dates)",
            labels={
                "max_temp_c": "Max Daily Temperature (°C)",
                "avg_bikes": "Avg. Daily Bikes / Station",
                "rain_category": "Rain Level",
            },
        )
        fig_scatter.update_layout(height=420)
        st.plotly_chart(fig_scatter, use_container_width=True)

    with w_right:
        rain_bar = (
            weather_df.groupby("rain_category", observed=False)["avg_bikes"]
            .mean()
            .reset_index()
        )
        fig_rain = px.bar(
            rain_bar,
            x="rain_category",
            y="avg_bikes",
            color="rain_category",
            color_discrete_sequence=["#2a9d8f", "#4e79a7", "#f28e2b", "#e15759"],
            text_auto=",.0f",
            title="Average Ridership by Rain Intensity",
            labels={"rain_category": "", "avg_bikes": "Avg. Daily Bikes / Station"},
        )
        fig_rain.update_layout(height=420, showlegend=False, xaxis_tickangle=-15)
        st.plotly_chart(fig_rain, use_container_width=True)

with tab3:
    audit_df = (
        base_filtered.groupby("station")
        .agg(
            total_days=("date", "count"),
            outage_days=("is_outage", "sum"),
            outage_pct=("is_outage", lambda x: round(x.mean() * 100, 2)),
        )
        .sort_values("outage_days", ascending=False)
    )
    st.dataframe(audit_df, use_container_width=True)
