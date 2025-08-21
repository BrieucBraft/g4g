# app/config.py

import os
from dotenv import load_dotenv

load_dotenv()

# --- Application Information ---
APP_VERSION = "1.1.0"

# --- Remote URIs ---
VERSION_URL = "https://gist.githubusercontent.com/BrieucBraft/3bf9efacf9a3c6529eee4ce083764a8a/raw/version.json"
DOWNLOAD_URL = "https://github.com/BrieucBraft/g4g/releases"
SENTRY_DSN = os.getenv("SENTRY_DSN", None) # Put your Sentry DSN in the .env file

# --- Dropbox API Credentials ---
DROPBOX_APP_KEY = os.getenv('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.getenv('DROPBOX_APP_SECRET')
DROPBOX_REFRESH_TOKEN = os.getenv('DROPBOX_REFRESH_TOKEN')
DROPBOX_NAMESPACE_ID = "11228085027"

# --- Base Directories ---
# Assumes the script is run from the root of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DROPBOX_BASE_DIR = '/8. Installations operationnelles/3. Maintenance par projet'

# --- Local Directories ---
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")
TEMP_DIR = os.path.join(OUTPUT_DIR, "temp")
TEMP_IMAGES_DIR = os.path.join(BASE_DIR, "temp_images")
CROPPED_IMAGES_DIR = os.path.join(BASE_DIR, "cropped_images")
ANNOTATED_TESTS_DIR = os.path.join(BASE_DIR, "tests")

# --- Model Paths ---
YOLO_MODEL_PATH = os.path.join(BASE_DIR, "models", "last.pt")
DINO_CONFIG_PATH = os.path.join(BASE_DIR, "config", "dino_config.py")
DINO_MODEL_PATH = os.path.join(BASE_DIR, "models", "groundingdino_swint_ogc.pth")

# --- File Names ---
OUTPUT_XLSX = os.path.join(OUTPUT_DIR, "output.xlsx")
OUTPUT_CSV = os.path.join(TEMP_DIR, "output.csv")
OUTPUT_TEMP_CSV = os.path.join(TEMP_DIR, "outputTemp.csv")
LOCK_FILE = os.path.join(BASE_DIR, 'app.lock')

# --- Vision API Settings ---
TEXT_PROMPT = "digital screen display . electronic device"
BOX_THRESHOLD = 0.2
TEXT_THRESHOLD = 0.15