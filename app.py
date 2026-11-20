import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Munich Urban Mobility Dashboard",
    page_icon="🚲",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv("munich_bike_cleaned_2022_2026.csv", parse_dates=["date"])
    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filter Controls")

years = sorted(df["year"].dropna().unique().astype(int).tolist())
selected_years = st.sidebar.multiselect("Select Years", years, default=years)

stations = sorted(df["station"].dropna().unique().tolist())
selected_stations = st.sidebar.multiselect("Select Counting Stations", stations, default=stations)

exclude_outages = st.sidebar.checkbox("Exclude Sensor Outage Days", value=True)

# Apply filters
filtered_df = df[
    (df["year"].isin(selected_years)) &
    (df["station"].isin(selected_stations))
]

if exclude_outages:
    filtered_df = filtered_df[~filtered_df["is_outage"]]

# --- Header ---
st.title("🚲 Munich Urban Mobility & Cycling Analysis (2022–2026)")
st.markdown(
    "Interactive exploration of bicycle traffic across Munich's 6 permanent counting stations, "
    "combining ridership volume with local weather conditions from the Munich Open Data Portal."
)

if filtered_df.empty:
    st.warning("No data matches your current filter selection. Please adjust the sidebar filters.")
    st.stop()

# --- Top KPI Metrics ---
total_trips = int(filtered_df["total_bikes"].sum())
avg_daily = int(filtered_df["total_bikes"].mean())
peak_row = filtered_df.loc[filtered_df["total_bikes"].idxmax()]
outage_days = int(df[df["year"].isin(selected_years) & df["station"].isin(selected_stations)]["is_outage"].sum())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Recorded Trips", f"{total_trips:,}")
col2.metric("Avg. Daily Bikes / Station", f"{avg_daily:,}")
col3.metric("Single-Day Station Peak", f"{int(peak_row['total_bikes']):,}", f"{peak_row['station']} ({peak_row['date'].strftime('%Y-%m-%d')})")
col4.metric("Sensor Outage Days Flagged", f"{outage_days:,}")

st.divider()

# --- Row 1: Commuter vs. Leisure & Monthly Trend ---
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Weekday vs. Weekend Ridership by Station")
    daytype_df = (
        filtered_df.groupby(["station", "is_weekend"])["total_bikes"]
        .mean()
        .unstack()
        .rename(columns={False: "Weekday", True: "Weekend"})
        .round(0)
    )
    st.bar_chart(daytype_df)

with right_col:
    st.subheader("Monthly Cycling Volume Trend")
    monthly_df = (
        filtered_df.set_index("date")
        .resample("ME")["total_bikes"]
        .mean()
        .rename("Avg Daily Bikes per Station")
    )
    st.line_chart(monthly_df)

st.divider()

# --- Row 2: Weather Elasticity ---
st.subheader("Weather Impact: Temperature vs. Daily Ridership")
weather_df = (
    filtered_df.groupby("date")
    .agg(
        avg_bikes=("total_bikes", "mean"),
        max_temp_c=("max_temp_c", "first"),
        precipitation_mm=("precipitation_mm", "first")
    )
    .dropna()
)

st.scatter_chart(
    weather_df,
    x="max_temp_c",
    y="avg_bikes",
    color="precipitation_mm",
    x_label="Max Daily Temperature (°C)",
    y_label="Avg. Daily Bikes per Station"
)

# --- Data Quality Audit Expander ---
with st.expander("View Data Quality Audit (Sensor Outages by Station)"):
    raw_filtered = df[df["year"].isin(selected_years) & df["station"].isin(selected_stations)]
    audit_df = raw_filtered.groupby("station").agg(
        total_days=("date", "count"),
        outage_days=("is_outage", "sum"),
        outage_pct=("is_outage", lambda x: round(x.mean() * 100, 2))
    ).sort_values("outage_days", ascending=False)
    st.dataframe(audit_df, use_container_width=True)
