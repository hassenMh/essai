import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Database
DATABASE_PATH = BASE_DIR / "data" / "store.db"
BACKUP_DIR = BASE_DIR / "data" / "backups"

# Assets
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
THEMES_DIR = ASSETS_DIR / "themes"
PRODUCT_IMAGES_DIR = BASE_DIR / "data" / "product_images"
QR_CODES_DIR = BASE_DIR / "data" / "qrcodes"
RECEIPTS_DIR = BASE_DIR / "data" / "receipts"

# App info
APP_NAME = "StoreManager Pro"
APP_VERSION = "1.0.0"
APP_AUTHOR = "StoreManager"

# Stock
LOW_STOCK_THRESHOLD = 10

# Backup
AUTO_BACKUP_DAYS = 1

# UI
DEFAULT_THEME = "dark"
WINDOW_MIN_WIDTH = 1280
WINDOW_MIN_HEIGHT = 800

# Date formats
DATE_FORMAT = "%d/%m/%Y"
DATETIME_FORMAT = "%d/%m/%Y %H:%M"

# Receipt
STORE_NAME = "Mon Magasin"
STORE_ADDRESS = "Adresse du magasin"
STORE_PHONE = "+216 XX XXX XXX"

def ensure_dirs():
    for d in [DATABASE_PATH.parent, BACKUP_DIR, PRODUCT_IMAGES_DIR, QR_CODES_DIR, RECEIPTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
