"""
utils/validators.py

Purpose:
Contains regex-based functions that check user input is well-formed
before we try to use it -- coordinates, location names, numeric
values pulled from data, and dates.

Why this matters:
- Catches bad input immediately, with a clear error message, instead
  of letting it crash something later (like a failed API call).
- Centralizes all validation logic in one place, so every other file
  in the project reuses the same rules instead of repeating regex
  everywhere.
- Every function here raises a ValueError with a clear message when
  input is invalid. Other parts of the app (like app.py) will catch
  these and show a friendly message to the user -- this is the
  "exception handling" requirement working together with the
  "regular expressions" requirement.
"""

import re
from datetime import datetime


# --- Patterns ---
# Precompiling patterns (re.compile) is slightly faster when a pattern
# is reused, and keeps the pattern itself easy to find and read.

# Matches "latitude, longitude" e.g. "9.0765, 7.3986"
#   -?          optional minus sign (southern/western hemispheres)
#   \d+         one or more digits
#   (\.\d+)?    optional decimal point followed by more digits
COORDINATE_PATTERN = re.compile(
    r'^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$'
)

# Matches place names like "Abuja", "Port Harcourt", "St. Mary's"
# Allows letters, spaces, hyphens, apostrophes, commas, periods
LOCATION_NAME_PATTERN = re.compile(r"^[A-Za-z\s\-',\.]+$")

# Matches a number, with or without a decimal point, optionally negative.
# Used to pull a value like 23.5 out of a string like "23.5mm" or
# "Temperature: 28.3 C"
NUMERIC_PATTERN = re.compile(r'-?\d+\.?\d*')

# Matches dates in YYYY-MM-DD format, e.g. "2026-08-15"
#   (\d{4})                 4-digit year
#   (0[1-9]|1[0-2])         month: 01-09 or 10-12
#   (0[1-9]|[12]\d|3[01])   day: 01-09, 10-29, or 30-31
DATE_PATTERN = re.compile(r'^(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$')


def validate_coordinates(coord_string: str) -> tuple[float, float]:
    """
    Validates a "latitude, longitude" string and returns it as a
    (lat, lon) tuple of floats.

    Example:
        validate_coordinates("9.0765, 7.3986") -> (9.0765, 7.3986)

    Raises:
        ValueError: if the format is wrong, or the values are outside
                    valid Earth coordinate ranges.
    """
    if not coord_string:
        raise ValueError("Coordinates cannot be empty.")

    match = COORDINATE_PATTERN.match(coord_string)
    if not match:
        raise ValueError(
            f"'{coord_string}' is not in 'latitude, longitude' format "
            "(e.g. '9.0765, 7.3986')."
        )

    lat, lon = float(match.group(1)), float(match.group(2))

    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude {lat} is out of range (-90 to 90).")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude {lon} is out of range (-180 to 180).")

    return lat, lon


def validate_location_name(name: str) -> str:
    """
    Validates a place name like "Abuja" or "Port Harcourt".

    Returns:
        str: the cleaned (trimmed) name if valid.

    Raises:
        ValueError: if the name is empty or contains characters that
                    don't belong in a place name (digits, symbols).
    """
    if not name or not name.strip():
        raise ValueError("Location name cannot be empty.")

    cleaned = name.strip()
    if not LOCATION_NAME_PATTERN.match(cleaned):
        raise ValueError(
            f"'{name}' contains characters not allowed in a location "
            "name (only letters, spaces, hyphens, apostrophes, "
            "commas, and periods are allowed)."
        )

    return cleaned


def extract_numeric_value(text) -> float:
    """
    Pulls the first number out of a string, ignoring any units or
    surrounding text. Used for parsing values like rainfall or
    temperature out of API responses or user input.

    Example:
        extract_numeric_value("23.5mm") -> 23.5
        extract_numeric_value("Temp: -2.1 C") -> -2.1

    Raises:
        ValueError: if no number is found in the text.
    """
    match = NUMERIC_PATTERN.search(str(text))
    if not match:
        raise ValueError(f"No numeric value found in '{text}'.")

    return float(match.group())


def validate_date(date_string: str) -> datetime:
    """
    Validates a date string in YYYY-MM-DD format and returns it as a
    datetime object.

    Example:
        validate_date("2026-08-15") -> datetime(2026, 8, 15)

    Raises:
        ValueError: if the format is wrong, or the date doesn't
                    actually exist (e.g. "2026-02-30").
    """
    if not date_string or not DATE_PATTERN.match(date_string.strip()):
        raise ValueError(
            f"'{date_string}' is not a valid date in YYYY-MM-DD format "
            "(e.g. '2026-08-15')."
        )

    # The regex above only confirms the FORMAT is right -- it can't
    # catch every invalid real-world date (e.g. "2026-02-30" matches
    # the pattern, but February never has 30 days). strptime catches
    # that, because it checks against the real calendar.
    try:
        return datetime.strptime(date_string.strip(), "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"'{date_string}' is not a real calendar date.")