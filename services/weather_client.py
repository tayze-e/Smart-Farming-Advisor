"""
services/weather_client.py

Purpose:
Wraps calls to the Open-Meteo Forecast API (free, no API key needed)
to fetch rainfall, temperature, and soil moisture forecasts for a
given location. Handles caching (so we don't call the API more than
necessary) and network-related exceptions.

Why this matters:
- Isolates all "talking to the internet" logic in one place. If
  Open-Meteo ever changes its API, only this file needs to change.
- Caching avoids hitting the API repeatedly for the same location
  within a short time window -- faster for the user, and respectful
  of Open-Meteo's free service.
- Handles the required "network errors" and "failed API requests"
  exception cases from the spec, using exception types that match
  what actually went wrong (timeout, connection, bad response, or
  missing data).
"""

import requests
from datetime import datetime
from utils.logger_setup import setup_logger
from config import WEATHER_CACHE_MINUTES

logger = setup_logger(__name__)

BASE_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherClient:
    """
    Fetches and caches weather/agricultural forecast data from
    Open-Meteo for a given latitude/longitude.

    Assumes the caller has already validated the coordinates (via
    validators.validate_coordinates) -- this class focuses purely on
    talking to the weather API and caching results, not on checking
    whether input is well-formed.
    """

    def __init__(self):
        # In-memory cache: keys are (lat, lon, forecast_days),
        # values are (fetched_at, data) tuples.
        self._cache = {}

    def get_forecast(self, latitude: float, longitude: float,
                      forecast_days: int = 7) -> dict:
        """
        Returns a forecast dict for the given coordinates:
            {
                "dates": [...],          # list of "YYYY-MM-DD" strings
                "temp_max": [...],       # daily high, deg C
                "temp_min": [...],       # daily low, deg C
                "rainfall_mm": [...],    # daily rainfall total, mm
                "soil_moisture": float or None  # current topsoil moisture
            }

        Uses a cached result if one exists and is still fresh (see
        config.WEATHER_CACHE_MINUTES).

        Raises:
            TimeoutError: if Open-Meteo doesn't respond in time.
            ConnectionError: if the network request fails outright
                              (no internet, DNS failure, etc.)
            ValueError: if Open-Meteo rejects the request, or returns
                        data in a shape we don't recognize.
        """
        cache_key = (round(latitude, 2), round(longitude, 2), forecast_days)

        cached = self._cache.get(cache_key)
        if cached:
            fetched_at, data = cached
            age_minutes = (datetime.now() - fetched_at).total_seconds() / 60
            if age_minutes < WEATHER_CACHE_MINUTES:
                logger.info(
                    f"Using cached weather data for {cache_key} "
                    f"({age_minutes:.1f} min old)"
                )
                return data

        logger.info(f"Fetching fresh weather data for {latitude}, {longitude}")

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "hourly": "soil_moisture_0_1cm",
            "forecast_days": forecast_days,
            "timezone": "auto",
        }

        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.error("Open-Meteo request timed out")
            raise TimeoutError(
                "The weather service took too long to respond. Please try again."
            )
        except requests.exceptions.ConnectionError:
            logger.error("Could not connect to Open-Meteo (network issue)")
            raise ConnectionError(
                "Could not reach the weather service. Check your internet connection."
            )
        except requests.exceptions.HTTPError:
            logger.error(f"Open-Meteo returned an error for {latitude}, {longitude}")
            raise ValueError(
                f"The weather service rejected the request (coordinates "
                f"{latitude}, {longitude} may be invalid)."
            )

        data = self._parse_response(response.json())
        self._cache[cache_key] = (datetime.now(), data)
        return data

    def _parse_response(self, raw: dict) -> dict:
        """
        Converts a raw Open-Meteo JSON response into this app's
        simpler format. Kept separate from get_forecast so this
        parsing logic can be tested with a sample response, without
        needing a live internet connection.

        Raises:
            ValueError: if expected fields are missing from the
                        response (handles the "missing forecast
                        data" requirement from the spec).
        """
        try:
            daily = raw["daily"]
        except KeyError:
            raise ValueError("Response is missing daily forecast data.")

        hourly = raw.get("hourly", {})
        soil_moisture_list = hourly.get("soil_moisture_0_1cm", [])
        if soil_moisture_list:
            current_soil_moisture = soil_moisture_list[0]
        else:
            logger.warning("Soil moisture data not available for this location")
            current_soil_moisture = None

        try:
            return {
                "dates": daily["time"],
                "temp_max": daily["temperature_2m_max"],
                "temp_min": daily["temperature_2m_min"],
                "rainfall_mm": daily["precipitation_sum"],
                "soil_moisture": current_soil_moisture,
            }
        except KeyError as e:
            raise ValueError(f"Response is missing expected field: {e}.")