"""
Temporary test file - confirms config.py and logger_setup.py work.
Safe to delete once verified.
"""

from config import GEMINI_API_KEY
from utils.logger_setup import setup_logger

# Test 1: confirm the API key loaded from .env
if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    print("[OK] API key loaded:", GEMINI_API_KEY[:15] + "...")
else:
    print("[FAIL] API key not found - check your .env file")

# Test 2: confirm logging works
logger = setup_logger("test")
logger.info("Logger test successful")
print("[OK] Check logs/app.log - it should now contain a log entry")