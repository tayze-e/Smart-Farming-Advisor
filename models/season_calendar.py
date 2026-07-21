"""
models/season_calendar.py

Purpose:
Generates a season calendar (planting -> weeding -> harvest
milestones) for a FarmPlot, and scans a weather forecast for
conditions that could threaten the crop (heavy rain, heatwave, dry
spell).

Why this matters:
- Turns raw crop + weather data into something directly useful for
  the user: a timeline of what to do and when, plus early warnings
  about risky weather ahead.
- Kept separate from FarmPlot (which just stores data) and
  WeatherClient (which just fetches data) -- this class is where
  that data gets turned into an actual plan.
"""

from datetime import timedelta

from models.crop import Crop
from models.farm_plot import FarmPlot
from utils.logger_setup import setup_logger

logger = setup_logger(__name__)

# Thresholds used to decide when a weather warning is worth raising.
HEAVY_RAIN_MM = 40           # single-day rainfall above this = heavy rain warning
DRY_SPELL_DAYS = 3           # this many consecutive near-zero-rain days = dry spell
DRY_SPELL_THRESHOLD_MM = 1   # rainfall below this counts as "no rain" for a dry spell
HEATWAVE_DAYS = 2            # this many days above the crop's ideal max temp = heatwave


class SeasonCalendar:
    """
    Builds a milestone timeline and weather warnings for a FarmPlot.
    """

    def __init__(self, farm_plot: FarmPlot, crop: Crop):
        if farm_plot.planting_date is None:
            raise ValueError(
                "Cannot build a season calendar without a planting date. "
                "Set one with farm_plot.set_planting_date() first."
            )
        self.farm_plot = farm_plot
        self.crop = crop

    def generate_milestones(self) -> list:
        """
        Returns a list of milestone dicts (date, milestone label,
        type), spanning from planting to expected harvest.
        """
        planting_date = self.farm_plot.planting_date

        return [
            {"date": planting_date, "milestone": "Planting", "type": "planting"},
            {
                "date": planting_date + timedelta(days=14),
                "milestone": "First weeding",
                "type": "weeding",
            },
            {
                "date": planting_date + timedelta(days=28),
                "milestone": "Second weeding",
                "type": "weeding",
            },
            {
                "date": planting_date + timedelta(days=self.crop.growing_period_days),
                "milestone": f"Expected harvest ({self.crop.display_name})",
                "type": "harvest",
            },
        ]

    def check_weather_warnings(self, weather: dict) -> list:
        """
        Scans a forecast (from WeatherClient.get_forecast) for
        conditions that could threaten this crop: heavy single-day
        rain, an extended dry spell, or a heatwave relative to the
        crop's ideal temperature range.

        Returns a list of warning strings (empty list if nothing to
        flag).
        """
        warnings = []
        dates = weather["dates"]
        rainfall = weather["rainfall_mm"]
        temp_max = weather["temp_max"]

        # --- Heavy rain: any single day above the threshold ---
        for date, rain in zip(dates, rainfall):
            if rain > HEAVY_RAIN_MM:
                warnings.append(
                    f"Heavy rain warning: {rain}mm forecast on {date} "
                    f"(above {HEAVY_RAIN_MM}mm)."
                )

        # --- Dry spell: N consecutive days with near-zero rain ---
        # The streak counter resets every time a wet-enough day breaks
        # it, and fires exactly once -- the moment the streak FIRST
        # reaches the threshold -- rather than repeating on every
        # additional dry day after that.
        dry_streak = 0
        for date, rain in zip(dates, rainfall):
            if rain < DRY_SPELL_THRESHOLD_MM:
                dry_streak += 1
                if dry_streak == DRY_SPELL_DAYS:
                    warnings.append(
                        f"Dry spell warning: {DRY_SPELL_DAYS}+ consecutive "
                        f"days with little to no rain, ending {date}."
                    )
            else:
                dry_streak = 0

        # --- Heatwave: N days above this crop's ideal max temperature ---
        hot_streak = 0
        for date, high in zip(dates, temp_max):
            if high > self.crop.ideal_temp_max_c:
                hot_streak += 1
                if hot_streak == HEATWAVE_DAYS:
                    warnings.append(
                        f"Heatwave warning: temperatures above "
                        f"{self.crop.ideal_temp_max_c}C for "
                        f"{HEATWAVE_DAYS}+ days, ending {date}."
                    )
            else:
                hot_streak = 0

        if warnings:
            logger.warning(
                f"{len(warnings)} weather warning(s) for {self.farm_plot.plot_name}"
            )

        return warnings