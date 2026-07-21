"""
config.py
---------
Central configuration for the Expense Tracker application.
Reads sensitive values from environment variables (.env file) so that
credentials are never hard-coded into source control.
"""

import os
from dotenv import load_dotenv

# Load variables from a .env file if present
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Flask core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")

    # --- Database (MySQL) ---
    # Format: mysql+pymysql://<user>:<password>@<host>:<port>/<database>
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "2005")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "expense_tracker")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Uploads ---
    UPLOAD_FOLDER = os.path.join(basedir, "static", "images", "receipts")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}

    # --- Session ---
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 hours

    # --- CSRF ---
    WTF_CSRF_TIME_LIMIT = None


class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
