# Raddauerzaehlstellen-Muenchen
Daten der Raddauerzählstellen München - Jahreszahlen

# 🚲 Munich Urban Mobility & Cycling Analysis (2022–2026)

An end-to-end data analysis and interactive dashboard exploring bicycle traffic patterns, weather elasticity, and sensor data quality across Munich's six permanent counting stations.

🔗 **https://raddauerzaehlstellen-muenchen-gfufq3wqxcvv3vpaywtcjt.streamlit.app/**

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



## 📂 Data Source

Data provided by **Landeshauptstadt München** via [opendata.muenchen.de](https://opendata.muenchen.de/) under the *dl-by-de/2-0* license.

```

---


