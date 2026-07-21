"""
models/farm_plot.py

Purpose:
Defines the FarmPlot class -- one of the user's farm plots, with its
location, crop, planting date, and a log of activities (watering,
weeding, etc.) performed on it over time.

Why this matters:
- This is a pure data class: it stores information but doesn't fetch
  weather, call Gemini, or generate calendars itself. PlantingAdvisor
  and SeasonCalendar work ON a FarmPlot rather than FarmPlot doing
  that work internally -- keeping each class focused on one job.
- to_dict()/from_dict() are the bridge to file storage: FarmLogStore
  (built later) will use these to save plots to JSON and load them
  back, since JSON can't store Python objects or datetimes directly.
- Assumes location/crop have already been validated (via
  validators.py) before a FarmPlot is created -- same principle as
  WeatherClient: this class trusts its input rather than
  re-validating it.
"""

from datetime import datetime


class FarmPlot:
    """
    Represents a single farm plot: where it is, what's growing there,
    when it was planted, and what's been done to it.
    """

    def __init__(self, plot_name, latitude, longitude, crop_name,
                 planting_date=None):
        self.plot_name = plot_name
        self.latitude = latitude
        self.longitude = longitude
        self.crop_name = crop_name
        # planting_date is optional -- a plot can exist before it's
        # actually been planted (e.g. while the user is still
        # deciding on timing).
        self.planting_date = planting_date
        self.activity_log = []

    def log_activity(self, activity: str, date=None):
        """
        Records an activity (e.g. "watered", "weeded", "fertilized")
        with a date. Defaults to right now if no date is given.
        """
        if date is None:
            date = datetime.now()
        self.activity_log.append({"date": date, "activity": activity})

    def set_planting_date(self, date):
        """Records when this plot was actually planted."""
        self.planting_date = date

    def to_dict(self) -> dict:
        """
        Converts this FarmPlot into a plain dictionary, ready to be
        saved to JSON. datetime objects become "YYYY-MM-DD" strings,
        since JSON has no native way to store a datetime.
        """
        return {
            "plot_name": self.plot_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "crop_name": self.crop_name,
            "planting_date": (
                self.planting_date.strftime("%Y-%m-%d")
                if self.planting_date else None
            ),
            "activity_log": [
                {
                    "date": entry["date"].strftime("%Y-%m-%d"),
                    "activity": entry["activity"],
                }
                for entry in self.activity_log
            ],
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        Rebuilds a FarmPlot object from a dictionary -- the reverse
        of to_dict(). Used when loading saved plots back from a file.
        """
        plot = cls(
            plot_name=data["plot_name"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            crop_name=data["crop_name"],
            planting_date=(
                datetime.strptime(data["planting_date"], "%Y-%m-%d")
                if data.get("planting_date") else None
            ),
        )
        plot.activity_log = [
            {
                "date": datetime.strptime(entry["date"], "%Y-%m-%d"),
                "activity": entry["activity"],
            }
            for entry in data.get("activity_log", [])
        ]
        return plot

    def __repr__(self):
        return f"FarmPlot({self.plot_name}, {self.crop_name})"