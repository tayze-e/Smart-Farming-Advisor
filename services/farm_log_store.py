"""
services/farm_log_store.py

Purpose:
Saves and loads FarmPlot objects to/from a local JSON file, so a
user's farm plots and activity logs persist between runs of the app.

Why this matters:
- This is the "file handling" requirement in its most direct form:
  reading and writing structured data to disk.
- Only FarmPlot data gets saved -- NOT the season calendar, since a
  calendar can always be recalculated fresh from a plot's planting
  date and its crop's growing period (see SeasonCalendar). Storing
  it separately would risk it going stale.
"""

import json
import os

from models.farm_plot import FarmPlot
from utils.logger_setup import setup_logger
from config import SAVE_DIRECTORY

logger = setup_logger(__name__)


class FarmLogStore:
    """
    Saves and loads a collection of FarmPlot objects to/from a single
    JSON file.
    """

    def __init__(self, filename: str = "farm_plots.json",
                 directory: str = SAVE_DIRECTORY):
        self.directory = directory
        self.filepath = os.path.join(directory, filename)

    def save(self, plots: list) -> None:
        """
        Saves a list of FarmPlot objects to the JSON file, overwriting
        whatever was there before.

        Raises:
            OSError: if the file can't be written (permissions, disk
                     full, etc.)
        """
        os.makedirs(self.directory, exist_ok=True)
        data = [plot.to_dict() for plot in plots]

        try:
            with open(self.filepath, "w") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save farm plots: {e}")
            raise OSError(f"Could not save farm plots to '{self.filepath}': {e}")

        logger.info(f"Saved {len(plots)} farm plot(s) to {self.filepath}")

    def load(self) -> list:
        """
        Loads all saved FarmPlot objects from the JSON file.

        Returns:
            list[FarmPlot]: empty list if no save file exists yet --
                             that's a normal first-run case, not an
                             error.

        Raises:
            ValueError: if the save file exists but contains invalid
                        JSON (a corrupted file).
        """
        if not os.path.exists(self.filepath):
            logger.info(f"No saved plots found at {self.filepath} (first run)")
            return []

        try:
            with open(self.filepath, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Saved plots file is corrupted: {e}")
            raise ValueError(
                f"'{self.filepath}' exists but isn't valid JSON. "
                "It may be corrupted."
            )

        plots = [FarmPlot.from_dict(entry) for entry in data]
        logger.info(f"Loaded {len(plots)} farm plot(s) from {self.filepath}")
        return plots