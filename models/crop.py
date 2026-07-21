"""
models/crop.py

Purpose:
Defines the Crop class, which represents baseline agricultural
knowledge about a single crop (maize, cassava, tomato, or rice) --
its ideal planting months, water needs, and common pest/disease
risks. This data is loaded from data/crop_knowledge.json.

Why this matters:
- This is a pure data class -- it doesn't call any API or make
  decisions. WeatherClient (live weather) and Crop (baseline
  knowledge) are two separate, independent inputs that PlantingAdvisor
  will combine later. Keeping them separate makes each easy to test
  and understand on its own.
- Demonstrates three of the four required Python concepts together:
  OOP (the class itself), file handling (reading the JSON knowledge
  base), and exception handling (missing file, corrupted file,
  unsupported crop).
"""

import json


class Crop:
    """
    Represents a single crop and its baseline agricultural data.
    """

    def __init__(self, name, display_name, planting_months,
                 water_needs_mm_per_week, growing_period_days,
                 ideal_temp_min_c, ideal_temp_max_c,
                 common_pests, common_diseases,
                 drought_sensitive, heat_sensitive):
        self.name = name
        self.display_name = display_name
        self.planting_months = planting_months
        self.water_needs_mm_per_week = water_needs_mm_per_week
        self.growing_period_days = growing_period_days
        self.ideal_temp_min_c = ideal_temp_min_c
        self.ideal_temp_max_c = ideal_temp_max_c
        self.common_pests = common_pests
        self.common_diseases = common_diseases
        self.drought_sensitive = drought_sensitive
        self.heat_sensitive = heat_sensitive

    @classmethod
    def load(cls, crop_name: str, filepath: str = "data/crop_knowledge.json"):
        """
        Loads a single crop's data from the crop knowledge JSON file
        and returns a ready-to-use Crop object.

        This is a "classmethod" -- an alternative way to build an
        object. Instead of constructing a Crop by hand and passing in
        every value yourself, you call Crop.load("maize") and this
        method handles reading the file and building the object for
        you. cls refers to the Crop class itself.

        Raises:
            FileNotFoundError: if the knowledge base file is missing.
            ValueError: if the file isn't valid JSON, or the crop
                        isn't one this app supports.
        """
        crop_name = crop_name.lower().strip()

        try:
            with open(filepath, "r") as f:
                all_crops = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Crop knowledge base not found at '{filepath}'."
            )
        except json.JSONDecodeError:
            raise ValueError(
                f"Crop knowledge base at '{filepath}' is corrupted "
                "or not valid JSON."
            )

        if crop_name not in all_crops:
            supported = ", ".join(all_crops.keys())
            raise ValueError(
                f"'{crop_name}' is not a supported crop. "
                f"Supported crops: {supported}."
            )

        data = all_crops[crop_name]
        return cls(
            name=crop_name,
            display_name=data["display_name"],
            planting_months=data["planting_months"],
            water_needs_mm_per_week=data["water_needs_mm_per_week"],
            growing_period_days=data["growing_period_days"],
            ideal_temp_min_c=data["ideal_temp_min_c"],
            ideal_temp_max_c=data["ideal_temp_max_c"],
            common_pests=data["common_pests"],
            common_diseases=data["common_diseases"],
            drought_sensitive=data["drought_sensitive"],
            heat_sensitive=data["heat_sensitive"],
        )

    def is_in_planting_season(self, month: int) -> bool:
        """
        Returns True if the given month (1-12) falls within this
        crop's ideal planting window.
        """
        return month in self.planting_months

    def __repr__(self):
        # Controls how this object prints -- makes debugging output
        # readable (e.g. "Crop(Maize)") instead of a generic memory
        # address like Python shows by default.
        return f"Crop({self.display_name})"