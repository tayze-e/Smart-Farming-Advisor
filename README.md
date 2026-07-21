# Smart Farming & Crop Planting Advisor

A Python + Streamlit application that gives farmers AI-powered planting advice by combining live weather forecasts with baseline crop knowledge.

## Features

- Enter a location and crop (maize, cassava, tomato, or rice) to get planting advice
- Fetches live weather forecasts (rainfall, temperature, soil moisture) from the Open-Meteo API
- AI-generated planting advice via the Gemini API, combining crop knowledge with live weather
- Automatic rule-based fallback advice if the Gemini API is unavailable
- Generates a season calendar (planting -> weeding -> harvest) for each farm plot
- Warns about heavy rain, heatwaves, or dry spells that could threaten the crop
- Lets users log planting dates and activities (watering, weeding, etc.) per farm plot
- Saves and loads farm plots to a local JSON file

## Tech Stack

- Python
- Streamlit (UI)
- Requests (HTTP calls)
- Open-Meteo Forecast API (weather + soil moisture, free, no key required)
- Open-Meteo Geocoding API (converts location names to coordinates)
- Gemini API (AI planting advice)
- JSON (data persistence)

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file in the project root with your Gemini API key: `GEMINI_API_KEY=your_key_here` (get a free key from Google AI Studio)
4. Run the app: `python -m streamlit run app.py`

## Python Concepts Demonstrated

- **File handling**: farm plots, season calendars, and crop knowledge are saved/loaded as JSON
- **Exception handling**: invalid locations, missing forecast data, unsupported crops, network errors, and failed API requests are all caught and handled gracefully
- **Regular expressions**: validating coordinates, location names, and dates; extracting numeric values from data
- **Object-oriented programming**: Crop, WeatherClient, PlantingAdvisor, FarmPlot, SeasonCalendar, and FarmLogStore classes