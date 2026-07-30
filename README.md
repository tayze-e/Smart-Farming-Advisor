# 🌾 Smart Farming & Crop Planting Advisor

> A Python + Streamlit application that gives farmers AI-powered planting advice by combining live weather forecasts with baseline crop knowledge.

---

## 🚀 Features

- **Location-aware advice** — enter a place name (e.g. *Wuse, Abuja*) or raw GPS coordinates
- **Live 7-day weather forecasts** — rainfall, temperature, and soil moisture from the Open-Meteo API (free, no key needed)
- **AI-generated planting advice** — powered by Google Gemini, combining crop knowledge with live weather
- **Automatic rule-based fallback** — if Gemini is unavailable, the app silently switches to an offline rule engine so it always gives an answer
- **Season calendar** — automatically generates planting → weeding → harvest milestones based on the crop's growing period
- **Weather risk warnings** — alerts for heavy rain (>40 mm), dry spells (3+ consecutive dry days), and heatwaves (2+ days above crop's max temperature)
- **Activity logging** — log and review farm activities (watering, weeding, fertilising) per plot with timestamps
- **Persistent storage** — save and reload all farm plots and activity logs to a local JSON file

---

## 🏗️ Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Core language |
| Streamlit | Web UI — no HTML/CSS/JS needed |
| requests | HTTP calls to weather and geocoding APIs |
| google-genai | Official Google SDK for Gemini AI |
| python-dotenv | Loads `.env` secrets safely |
| Open-Meteo Forecast API | Free weather forecasts (no key required) |
| Open-Meteo Geocoding API | Converts place names to coordinates |
| OpenStreetMap Nominatim | Backup geocoder for local/rural locations |
| JSON files | Stores crop knowledge base and saved plot data |

---

## ⚙️ Setup

### 1. Clone the repository
```bash
git clone https://github.com/tayze-e/Smart-Farming-Advisor.git
cd Smart-Farming-Advisor
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure your API key
Copy the example env file and fill in your key:
```bash
cp .env.example .env
```
Then open `.env` and replace the placeholder:
```
GEMINI_API_KEY=your_actual_key_here
```
Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey).

> **No Gemini key?** The app still works — it automatically falls back to rule-based advice when the key is missing or invalid.

### 4. Run the app
```bash
python -m streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📂 Project Structure

```
Smart-Farming-Advisor/
│
├── app.py                     ← Streamlit UI — entry point
├── config.py                  ← Settings and API key loading
├── requirements.txt           ← Python dependencies
├── .env.example               ← Template for your API key
│
├── data/
│   └── crop_knowledge.json    ← Static crop facts (temperatures, water needs, pests)
│
├── models/
│   ├── crop.py                ← Crop class: loads and holds crop data
│   ├── farm_plot.py           ← FarmPlot class: one plot with its history
│   └── season_calendar.py     ← SeasonCalendar: milestones + weather warnings
│
├── services/
│   ├── weather_client.py      ← WeatherClient: fetches forecast with caching
│   ├── planting_advisor.py    ← PlantingAdvisor: Gemini AI + rule fallback
│   └── farm_log_store.py      ← FarmLogStore: JSON read/write for plot data
│
└── utils/
    ├── validators.py          ← Regex-based input validation
    └── logger_setup.py        ← Logging to console and file
```

---

## 🌱 Supported Crops

| Crop | Ideal Planting Months | Growing Period |
|---|---|---|
| Maize | March, April, May, August, September | 100 days |
| Cassava | March–June, September, October | 300 days |
| Tomato | January, February, September–November | 80 days |
| Rice | April, May, June, July | 120 days |

---

## 💡 Python Concepts Demonstrated

- **Object-Oriented Programming (OOP)** — six domain classes (`Crop`, `FarmPlot`, `SeasonCalendar`, `WeatherClient`, `PlantingAdvisor`, `FarmLogStore`) with `@classmethod` factory constructors and `__repr__`
- **Exception Handling** — structured try/except blocks translate API and network errors into clean user-facing messages; broad catch in the advisor ensures graceful fallback
- **File Handling** — JSON read/write for the crop knowledge base and saved plot data; `with open(...)` context managers throughout
- **Regular Expressions** — pre-compiled patterns (`re.compile`) validate coordinates, location names, and dates before any processing

---

## 📄 Documentation

A full technical report (`Full_Codebase_Exposition.pdf`) is included in this repository. It covers every file, every function, and every design decision in plain language — suitable for presentations and code reviews.
