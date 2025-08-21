import os

# Base directory for the application
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Asset paths
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
ICONS_DIR = os.path.join(ASSETS_DIR, 'icons')
THEMES_DIR = os.path.join(ASSETS_DIR, 'themes')
ICON_PATH = os.path.join(ICONS_DIR, 'go4greenfr_logo.ico')
LOGO_PATH = os.path.join(ICONS_DIR, 'go4greenfr_logo.jpeg')
THEME_PATH = os.path.join(THEMES_DIR, 'forest-ttk-theme', 'forest-light.tcl')

# Model paths
MODELS_DIR = os.path.join(BASE_DIR, 'models')
YOLO_MODEL_PATH = os.path.join(MODELS_DIR, "last.pt")
DINO_CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'dino_config.py')
DINO_MODEL_PATH = os.path.join(MODELS_DIR, "groundingdino_swint_ogc.pth")


# Output and data paths
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
TEMP_DIR = os.path.join(OUTPUT_DIR, 'temp')
OUTPUT_XLSX = os.path.join(OUTPUT_DIR, 'output.xlsx')
OUTPUT_CSV = os.path.join(TEMP_DIR, 'output.csv')
OUTPUT_TEMP_CSV = os.path.join(TEMP_DIR, 'outputTemp.csv')
CROPPED_IMAGES_DIR = "cropped_images"
TEMP_IMAGES_DIR = "temp_images"

# Remote URLs
VERSION_URL = "https://gist.githubusercontent.com/BrieucBraft/3bf9efacf9a3c6529eee4ce083764a8a/raw/version.json"
RELEASES_URL = "https://github.com/BrieucBraft/g4g/releases"

# Application settings
APP_VERSION = "1.0.0"
DROPBOX_BASE_DIR = '/8. Installations operationnelles/3. Maintenance par projet'