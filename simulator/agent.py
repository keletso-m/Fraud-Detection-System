"""realistic multi step attack sequence through the live API """
import sys
import time
import requests
from pathlib import Path
import os
from dotenv import load_dotenv


load_dotenv()

BASE_URL = os.getenv("SENTINEL_URL", "http://localhost:8000")
USERNAME = os.getenv("SENTINEL_USER")
PASSWORD = os.getenv("SENTINEL_PASSWORD")
DELAY    = float(os.getenv("SENTINEL_DELAY", "2.5"))

if not USERNAME or not PASSWORD:
    print("SENTINEL_USER and SENTINEL_PASSWORD must be set in your file.")
    sys.exit(1)