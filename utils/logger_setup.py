"""
utils/logger_setup.py

Purpose:
Sets up a consistent logging system for the whole application, so
every class (WeatherClient, PlantingAdvisor, FarmLogStore, etc.) can
record what it's doing -- instead of scattering print() statements
throughout the code.

Why this matters:
- print() statements vanish once the terminal closes. Logs are saved
  to a file, so there's a record you can check later or show during
  a demo.
- Logging separates routine info (INFO), things worth noting but not
  fatal (WARNING), and actual failures (ERROR), instead of every
  message looking the same.
- Every entry is timestamped automatically.
"""

import logging
import os

LOG_DIRECTORY = "logs"
LOG_FILE = os.path.join(LOG_DIRECTORY, "app.log")


def setup_logger(name: str) -> logging.Logger:
    """
    Creates and returns a logger configured to write to both the
    console (so you see it live while the app runs) and a log file
    (so there's a permanent record).

    Parameters:
        name (str): usually __name__ of the calling file, so log
                    messages show which part of the app produced them.

    Returns:
        logging.Logger: a ready-to-use logger object.
    """
    # Make sure the "logs" folder exists before writing to it.
    # exist_ok=True means: don't raise an error if it's already there.
    os.makedirs(LOG_DIRECTORY, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Guard against duplicate handlers. This matters specifically for
    # Streamlit: it reruns the whole script on every user interaction,
    # so without this check, every click would attach a new handler,
    # and log messages would print multiple times over.
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Writes logs to logs/app.log -- the permanent record
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(formatter)

        # Also prints logs to the terminal while the app runs live
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger