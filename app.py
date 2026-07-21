"""
app.py

Purpose:
The Streamlit user interface that ties every other piece of this
project together: it collects the user's location and crop, fetches
weather data, gets AI (or fallback) planting advice, lets the user
create farm plots and log activities, generates a season calendar,
shows weather warnings, and saves/loads everything to a local file.

Why this matters:
- This is the only file the user actually interacts with directly.
  Every other file (Crop, WeatherClient, PlantingAdvisor, FarmPlot,
  SeasonCalendar, FarmLogStore, validators) is a building block;
  this file wires them together into a working application.
"""

import streamlit as st
from datetime import datetime
import requests

from config import validate_config, SUPPORTED_CROPS
from models.crop import Crop
from models.farm_plot import FarmPlot
from models.season_calendar import SeasonCalendar
from services.weather_client import WeatherClient
from services.planting_advisor import PlantingAdvisor
from services.farm_log_store import FarmLogStore
from utils.validators import validate_location_name
from utils.logger_setup import setup_logger

logger = setup_logger(__name__)

st.set_page_config(page_title="Smart Farming & Crop Planting Advisor", page_icon="🌾")


def geocode_location(location_name: str) -> tuple:
    """
    Converts a place name (e.g. "Abuja") into (latitude, longitude)
    using Open-Meteo's free Geocoding API -- a different endpoint
    from the forecast API used in WeatherClient.

    Exceptions are translated into the same built-in types
    WeatherClient uses (ConnectionError, TimeoutError, ValueError),
    so the rest of the app never needs to know the "requests"
    library's specific exception types exist -- one consistent set
    of exceptions to handle everywhere, regardless of which service
    raised the problem.
    """
    try:
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location_name, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise TimeoutError("The location lookup service took too long to respond.")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Could not reach the location lookup service.")
    except requests.exceptions.HTTPError:
        raise ValueError(f"The location lookup service rejected '{location_name}'.")

    results = response.json().get("results")
    if not results:
        raise ValueError(f"Could not find a location matching '{location_name}'.")
    return results[0]["latitude"], results[0]["longitude"]


# --- Startup check: fail fast with a friendly message if the API key is missing ---
try:
    validate_config()
except ValueError as e:
    st.error(f"Configuration error: {e}")
    st.stop()

# --- Session state: create these ONCE per session, not on every rerun ---
# Streamlit reruns this entire script top-to-bottom on every button
# click or input change. Without session_state, we'd lose the
# WeatherClient's cache and reload plots from disk on every single
# click. Storing these objects here makes them persist across
# reruns within one browser session.
if "weather_client" not in st.session_state:
    st.session_state.weather_client = WeatherClient()
if "advisor" not in st.session_state:
    st.session_state.advisor = PlantingAdvisor()
if "store" not in st.session_state:
    st.session_state.store = FarmLogStore()
if "plots" not in st.session_state:
    st.session_state.plots = st.session_state.store.load()

st.title("🌾 Smart Farming & Crop Planting Advisor")
st.caption("Enter your location and crop to get AI-powered planting advice.")

# --- Section 1: Add a new farm plot ---
st.header("Add a Farm Plot")

with st.form("new_plot_form"):
    plot_name = st.text_input("Plot name", placeholder="e.g. North Field")
    location_input = st.text_input("Location", placeholder="e.g. Abuja")
    crop_choice = st.selectbox("Crop", SUPPORTED_CROPS)
    planting_date_input = st.date_input("Planting date", value=datetime.now())
    submitted = st.form_submit_button("Add Plot")

if submitted:
    try:
        if not plot_name or not plot_name.strip():
            raise ValueError("Plot name cannot be empty.")
        clean_location = validate_location_name(location_input)
        lat, lon = geocode_location(clean_location)

        new_plot = FarmPlot(
            plot_name=plot_name.strip(),
            latitude=lat,
            longitude=lon,
            crop_name=crop_choice,
        )
        new_plot.set_planting_date(
            datetime.combine(planting_date_input, datetime.min.time())
        )

        st.session_state.plots.append(new_plot)
        st.success(f"Added '{plot_name.strip()}' growing {crop_choice} at {clean_location}.")
        logger.info(f"Added new plot: {plot_name.strip()} ({crop_choice})")

    except ValueError as e:
        st.error(f"Could not add plot: {e}")
    except (ConnectionError, TimeoutError) as e:
        st.error(f"Network problem: {e}")

# --- Section 2: Show existing plots ---
st.header("Your Farm Plots")

if not st.session_state.plots:
    st.info("No farm plots yet. Add one above to get started.")

for i, plot in enumerate(st.session_state.plots):
    with st.expander(f"{plot.plot_name} — {plot.crop_name.title()}"):
        st.write(f"**Location:** {plot.latitude:.4f}, {plot.longitude:.4f}")
        st.write(
            f"**Planting date:** "
            f"{plot.planting_date.strftime('%Y-%m-%d') if plot.planting_date else 'Not set'}"
        )

        # Unique session_state keys per plot, so fetched weather/advice
        # persist across reruns -- e.g. if the user then interacts
        # with a DIFFERENT plot, this one's results don't vanish.
        weather_key = f"weather_{i}"
        advice_key = f"advice_{i}"

        if st.button("Get weather & advice", key=f"fetch_btn_{i}"):
            try:
                crop = Crop.load(plot.crop_name)
                weather = st.session_state.weather_client.get_forecast(
                    plot.latitude, plot.longitude
                )
                current_month = datetime.now().month
                advice = st.session_state.advisor.get_advice(crop, weather, current_month)
                st.session_state[weather_key] = weather
                st.session_state[advice_key] = advice
            except ValueError as e:
                st.error(f"Could not get advice: {e}")
            except (ConnectionError, TimeoutError) as e:
                st.error(f"Weather service problem: {e}")

        if weather_key in st.session_state:
            weather = st.session_state[weather_key]
            advice = st.session_state[advice_key]
            crop = Crop.load(plot.crop_name)

            st.subheader("Weather Forecast")
            avg_rain = sum(weather["rainfall_mm"]) / len(weather["rainfall_mm"])
            st.write(f"Average rainfall: {avg_rain:.1f} mm/day")
            st.write(
                f"Temperature range: {min(weather['temp_min'])}"
                f"-{max(weather['temp_max'])}C"
            )
            if weather["soil_moisture"] is not None:
                st.write(f"Soil moisture: {weather['soil_moisture']:.2f}")

            st.subheader(f"Advice ({advice['source']})")
            if advice["should_plant_now"]:
                st.success("Good time to plant")
            else:
                st.warning("Not the ideal planting window")
            st.write(advice["advice_text"])

            if plot.planting_date:
                calendar = SeasonCalendar(plot, crop)
                st.subheader("Season Calendar")
                for m in calendar.generate_milestones():
                    st.write(f"- {m['date'].strftime('%Y-%m-%d')}: {m['milestone']}")

                warnings = calendar.check_weather_warnings(weather)
                if warnings:
                    st.subheader("Weather Warnings")
                    for w in warnings:
                        st.warning(w)

        st.write("**Log an activity**")
        activity_text = st.text_input(
            "Activity", key=f"activity_input_{i}", placeholder="e.g. watered, weeded"
        )
        if st.button("Log activity", key=f"log_btn_{i}"):
            if activity_text:
                plot.log_activity(activity_text)
                st.success(f"Logged: {activity_text}")
            else:
                st.error("Enter an activity first.")

        if plot.activity_log:
            st.write("**Activity history:**")
            for entry in plot.activity_log:
                st.write(f"- {entry['date'].strftime('%Y-%m-%d')}: {entry['activity']}")

# --- Section 3: Save everything to a local file ---
st.header("Save Your Data")
if st.button("Save all plots to file"):
    try:
        st.session_state.store.save(st.session_state.plots)
        st.success(f"Saved {len(st.session_state.plots)} plot(s) to file.")
    except OSError as e:
        st.error(f"Could not save: {e}")