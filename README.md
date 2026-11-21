# Raddauerzaehlstellen-Muenchen
Daten der Raddauerzählstellen München - Jahreszahlen

# 🚲 Munich Urban Mobility & Cycling Analysis (2022–2026)

An end-to-end data analysis and interactive dashboard exploring bicycle traffic patterns, weather elasticity, and sensor data quality across Munich's six permanent counting stations.

🔗 **https://raddauerzaehlstellen-muenchen-gfufq3wqxcvv3vpaywtcjt.streamlit.app/** *(Add your link after deploying)*

---

## 📌 Project Overview
Urban planners need reliable data to prioritize bike lane expansion, winter maintenance, and commuter infrastructure. Using official daily ridership and weather data from the **Munich Open Data Portal** (*Daten der Raddauerzählstellen*), this project answers three core questions:
1. **Commuter vs. Leisure Corridors:** Which routes serve daily weekday commuters versus weekend recreational riders?
2. **Weather Elasticity:** How strongly do temperature and precipitation reduce cycling volume?
3. **Data Reliability:** Where do sensor outages occur, and how can analysts prevent them from skewing city-wide metrics?

---

## 🔍 Key Findings
* **Clear Commuter Corridors:** Stations such as **Erhardt** show significantly higher weekday averages (**8,159** bikes/day) than weekends, confirming heavy commuter reliance.
* **Weather Resilience:** Ridership climbs steadily with temperature up to ~25°C, while heavy rain (15+ mm) reduces average daily cycling volume by approximately **33%** compared to dry days.
* **Data Quality Impact:** Across 2022–2026, **135** station-days recorded zero or missing counts due to sensor outages. Flagging and excluding these days prevented artificial dips in monthly and weather-based averages.

---

## 📊 Visual Highlights

### Commuter vs. Leisure Patterns
![Commuter vs Leisure](images/01_commuter_vs_leisure.png)

### Weather Elasticity
![Weather Impact](images/02_weather_impact.png)

---

## 🛠️ Methodology & Tech Stack
* **Data Ingestion:** Automated retrieval of monthly CSV files (2022–2026) via the Munich Open Data CKAN API (`requests`, `pandas`).
* **Data Cleaning:** Standardized German headers to `snake_case`, parsed mixed date formats, coerced numeric weather fields, and engineered an `is_outage` flag instead of destructively dropping rows.
* **Visualization & Deployment:** Publication-ready static charts (`matplotlib`) and a live, filterable web app (`streamlit`).

---

## 🚀 How to Run Locally
```bash
git clone [https://github.com/your-username/munich-bike-mobility.git](https://github.com/your-username/munich-bike-mobility.git)
cd munich-bike-mobility
pip install -r requirements.txt
streamlit run app.py


Below are the complete files to publish your project: **`app.py`** for the interactive Streamlit dashboard, **`requirements.txt`** for deployment, and **`README.md`** for your GitHub repository.

---

## 1. Interactive Dashboard (`app.py`)

Save this file in the root folder of your GitHub repository alongside `munich_bike_cleaned_2022_2026.csv` (or update the path to `data/processed/munich_bike_cleaned_2022_2026.csv` if you use folders).

```python
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

```

### Dependencies (`requirements.txt`)

Create a `requirements.txt` file in the same root folder so Streamlit Community Cloud installs the exact libraries needed:

```text
streamlit>=1.35.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.8.0

```

---

## 2. GitHub Repository `README.md`

Copy this into your `README.md` and replace the bracketed `[...]` placeholders with the exact numbers from your Colab output.

```markdown
# 🚲 Munich Urban Mobility & Cycling Analysis (2022–2026)

An end-to-end data analysis and interactive dashboard exploring bicycle traffic patterns, weather elasticity, and sensor data quality across Munich's six permanent counting stations.

🔗 **[Live Interactive Dashboard (Streamlit)](https://your-app-name.streamlit.app)** *(Add your link after deploying)*

---

## 📌 Project Overview
Urban planners need reliable data to prioritize bike lane expansion, winter maintenance, and commuter infrastructure. Using official daily ridership and weather data from the **Munich Open Data Portal** (*Daten der Raddauerzählstellen*), this project answers three core questions:
1. **Commuter vs. Leisure Corridors:** Which routes serve daily weekday commuters versus weekend recreational riders?
2. **Weather Elasticity:** How strongly do temperature and precipitation reduce cycling volume?
3. **Data Reliability:** Where do sensor outages occur, and how can analysts prevent them from skewing city-wide metrics?

---

## 🔍 Key Findings
* **Clear Commuter Corridors:** Stations such as **[Top Weekday Station, e.g., Erhardtstraße]** show significantly higher weekday averages (**[X,XXX]** bikes/day) than weekends, confirming heavy commuter reliance.
* **Weather Resilience:** Ridership climbs steadily with temperature up to ~25°C, while heavy rain (15+ mm) reduces average daily cycling volume by approximately **[XX]%** compared to dry days.
* **Data Quality Impact:** Across 2022–2026, **[XXX]** station-days recorded zero or missing counts due to sensor outages. Flagging and excluding these days prevented artificial dips in monthly and weather-based averages.

---

## 📊 Visual Highlights

### Commuter vs. Leisure Patterns
![Commuter vs Leisure](images/01_commuter_vs_leisure.png)

### Weather Elasticity
![Weather Impact](images/02_weather_impact.png)

---

## 🛠️ Methodology & Tech Stack
* **Data Ingestion:** Automated retrieval of monthly CSV files (2022–2026) via the Munich Open Data CKAN API (`requests`, `pandas`).
* **Data Cleaning:** Standardized German headers to `snake_case`, parsed mixed date formats, coerced numeric weather fields, and engineered an `is_outage` flag instead of destructively dropping rows.
* **Visualization & Deployment:** Publication-ready static charts (`matplotlib`) and a live, filterable web app (`streamlit`).

---

## 🚀 How to Run Locally
```bash
git clone [https://github.com/your-username/munich-bike-mobility.git](https://github.com/your-username/munich-bike-mobility.git)
cd munich-bike-mobility
pip install -r requirements.txt
streamlit run app.py

```

---

## 📂 Data Source

Data provided by **Landeshauptstadt München** via [opendata.muenchen.de](https://opendata.muenchen.de/) under the *dl-by-de/2-0* license.

```

---

## 3. Publish in 5 Minutes
1. Create a new public repository on GitHub named `munich-bike-mobility`.
2. Upload `app.py`, `requirements.txt`, `README.md`, `munich_bike_cleaned_2022_2026.csv`, and an `images/` folder containing `01_commuter_vs_leisure.png` and `02_weather_impact.png`.
3. Go to [share.streamlit.io](https://share.streamlit.io/), sign in with GitHub, select your repository and `app.py`, and click **Deploy**.
4. Copy your new live URL back into the top of your `README.md`.

<FollowUp label="Want help setting up your GitHub repo or planning Project 2 (Data Science) next?" query="Help me plan Project 2 (Data Science) for my portfolio now that my Munich Urban Mobility project is ready to publish."/>

```
