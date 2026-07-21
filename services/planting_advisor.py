"""
services/planting_advisor.py

Purpose:
Combines a Crop object (baseline knowledge) with a live weather
forecast (from WeatherClient) to produce planting advice using the
Gemini API. Falls back to a simple rule-based advisory if the Gemini
API is unavailable or fails for any reason.

Why this matters:
- This is where the two independent data sources -- baseline crop
  knowledge and live weather -- actually get combined into a useful
  recommendation.
- If the Gemini API key is missing, the network is down, or Google's
  service has an outage, the app should still give the user SOME
  useful advice rather than crashing or showing a blank screen. The
  rule-based fallback exists for exactly that reason.
"""

from google import genai

from models.crop import Crop
from utils.logger_setup import setup_logger
from config import GEMINI_API_KEY

logger = setup_logger(__name__)

MODEL_NAME = "gemini-3.5-flash"


class PlantingAdvisor:
    """
    Generates planting advice by combining crop knowledge and weather
    data, using Gemini AI with a rule-based fallback.
    """

    def __init__(self):
        self._client = genai.Client(api_key=GEMINI_API_KEY)

    def get_advice(self, crop: Crop, weather: dict, current_month: int) -> dict:
        """
        Returns a dict of advice:
            {
                "source": "gemini" or "rule-based fallback",
                "should_plant_now": bool,
                "advice_text": str,
            }

        Tries Gemini first. If that fails for ANY reason, falls back
        to _rule_based_advice() so the user still gets something
        useful.
        """
        try:
            advice_text = self._ask_gemini(crop, weather, current_month)
            return {
                "source": "gemini",
                "should_plant_now": crop.is_in_planting_season(current_month),
                "advice_text": advice_text,
            }
        except Exception as e:
            # A broad "except Exception" is intentional here, and it's
            # one of the only places in this app where that's the right
            # call. Whatever went wrong with Gemini -- bad API key, no
            # internet, rate limit, a Google service outage -- the
            # recovery action is exactly the same either way: fall
            # back to simple rule-based advice. Because the response
            # to every failure is identical, there's no benefit to
            # telling the exception types apart here.
            logger.warning(f"Gemini request failed, using fallback advice: {e}")
            return self._rule_based_advice(crop, weather, current_month)

    def _ask_gemini(self, crop: Crop, weather: dict, current_month: int) -> str:
        """
        Builds a prompt from the crop and weather data and sends it
        to Gemini. Returns the raw advice text.
        """
        prompt = self._build_prompt(crop, weather, current_month)
        response = self._client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        return response.text

    def _build_prompt(self, crop: Crop, weather: dict, current_month: int) -> str:
        """
        Turns crop + weather data into a clear text prompt for
        Gemini. Kept as its own method so the prompt itself can be
        tested and tweaked independently of the actual API call.
        """
        avg_rainfall = sum(weather["rainfall_mm"]) / len(weather["rainfall_mm"])
        max_temp = max(weather["temp_max"])
        min_temp = min(weather["temp_min"])
        soil = weather["soil_moisture"]

        return (
            f"You are an agricultural advisor. A farmer wants to grow "
            f"{crop.display_name} this month (month {current_month}).\n\n"
            f"Crop baseline data:\n"
            f"- Ideal planting months: {crop.planting_months}\n"
            f"- Water needs: {crop.water_needs_mm_per_week} mm/week\n"
            f"- Ideal temperature range: {crop.ideal_temp_min_c}-{crop.ideal_temp_max_c} C\n"
            f"- Common pests: {', '.join(crop.common_pests)}\n"
            f"- Common diseases: {', '.join(crop.common_diseases)}\n\n"
            f"Upcoming weather forecast:\n"
            f"- Average daily rainfall: {avg_rainfall:.1f} mm\n"
            f"- Temperature range: {min_temp}-{max_temp} C\n"
            f"- Current topsoil moisture: {soil if soil is not None else 'unknown'}\n\n"
            f"In 3-4 short sentences, advise the farmer: is now a good time "
            f"to plant, what irrigation is needed, and what pest/disease "
            f"risks to watch for given this weather."
        )

    def _rule_based_advice(self, crop: Crop, weather: dict, current_month: int) -> dict:
        """
        Simple, deterministic backup advice used when Gemini is
        unavailable. Uses plain comparisons against the crop's
        baseline data instead of AI -- less nuanced, but keeps the
        app useful during an outage.
        """
        avg_rainfall = sum(weather["rainfall_mm"]) / len(weather["rainfall_mm"])
        max_temp = max(weather["temp_max"])
        in_season = crop.is_in_planting_season(current_month)

        notes = []
        if not in_season:
            notes.append(
                f"This month is outside {crop.display_name}'s typical planting "
                f"window (months {crop.planting_months})."
            )
        if crop.heat_sensitive and max_temp > crop.ideal_temp_max_c:
            notes.append(
                f"Forecast highs of {max_temp}C exceed this crop's heat "
                f"tolerance ({crop.ideal_temp_max_c}C) -- consider shade or delay."
            )
        if crop.drought_sensitive and avg_rainfall < 5:
            notes.append(
                "Low forecast rainfall for a drought-sensitive crop -- "
                "irrigation will likely be necessary."
            )
        if not notes:
            notes.append(
                f"Conditions look reasonable for {crop.display_name} based "
                f"on baseline data. Monitor rainfall and watch for "
                f"{', '.join(crop.common_pests)}."
            )

        return {
            "source": "rule-based fallback",
            "should_plant_now": in_season,
            "advice_text": " ".join(notes),
        }