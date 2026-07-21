"""
config.py

Purpose:
This file is responsible for loading application settings and secret
API keys from the .env file, so the rest of the app never has to deal
with raw secrets or hardcoded values directly.

Why this matters:
- Keeps sensitive data (API keys) out of the main codebase.
- Makes it easy to change settings (like cache duration) in one place
  instead of hunting through multiple files.
- If GEMINI_API_KEY is missing, the app fails immediately with a clear
  error, instead of failing later with a confusing API error.
"""

import os
from dotenv import load_dotenv

# Loads the key-value pairs from the .env file into the environment
load_dotenv()

# --- API Keys ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- App settings ---
# How long (in minutes) a cached weather response stays valid before
# we fetch fresh data again. Prevents hammering the Open-Meteo API.
WEATHER_CACHE_MINUTES = 60

# Where farm plot data gets saved locally
SAVE_DIRECTORY = "data/saved_plots"

# Supported crops for this version of the app
SUPPORTED_CROPS = ["maize", "cassava", "tomato", "rice"]


def validate_config():
    """
    Checks that required settings are present before the app starts.
    Raises a clear error early, rather than letting the app crash
    later with a confusing message when it tries to call Gemini.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY is missing. Please add your key to the .env file."
        )