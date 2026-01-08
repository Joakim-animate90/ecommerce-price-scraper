"""
Apache Superset Configuration for E-commerce Price Scraper.

This configuration sets up Superset for visualizing laptop prices
from the PostgreSQL database.
"""

import os
from datetime import timedelta

# Security
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "changeme_superset_secret")
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# Database connection
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{os.getenv('DATABASE_USER', 'scraper_user')}:"
    f"{os.getenv('DATABASE_PASSWORD', 'changeme')}@"
    f"{os.getenv('DATABASE_HOST', 'postgres')}:"
    f"{os.getenv('DATABASE_PORT', '5432')}/"
    f"{os.getenv('DATABASE_DB', 'ecommerce_prices')}"
)

# Disable SQLAlchemy track modifications
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask App Builder configuration
APP_NAME = "E-commerce Price Comparison Dashboard"
APP_ICON = "/static/assets/images/superset-logo-horiz.png"
APP_ICON_WIDTH = 126

# Session configuration
PERMANENT_SESSION_LIFETIME = timedelta(days=7)

# Enable embedding
ENABLE_PROXY_FIX = True
PUBLIC_ROLE_LIKE_GAMMA = True

# Cache configuration
CACHE_CONFIG = {"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300}

# Feature flags
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_NATIVE_FILTERS_SET": True,
    "EMBEDDABLE_CHARTS": True,
    "ESCAPE_MARKDOWN_HTML": False,
}

# CSV export settings
CSV_EXPORT = {
    "encoding": "utf-8",
}

# Row limit for SQL queries
ROW_LIMIT = 10000
SQL_MAX_ROW = 50000

# Webserver configuration
SUPERSET_WEBSERVER_PROTOCOL = "http"
SUPERSET_WEBSERVER_ADDRESS = "0.0.0.0"
SUPERSET_WEBSERVER_PORT = 8088

# Workers configuration
SUPERSET_WORKERS = 4
SUPERSET_WORKER_TIMEOUT = 120

# Upload folder
UPLOAD_FOLDER = "/app/superset_home/uploads/"
IMG_UPLOAD_FOLDER = "/app/superset_home/uploads/images/"

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
