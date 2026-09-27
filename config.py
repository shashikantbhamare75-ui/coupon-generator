import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret keys - in production, load these from environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(BASE_DIR, 'database', 'database.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT settings
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_TOKEN_LOCATION = ['cookies', 'headers']
    JWT_COOKIE_SECURE = False  # Set to True in production (requires HTTPS)
    JWT_COOKIE_CSRF_PROTECT = False  # Simplified for this project
    JWT_ACCESS_COOKIE_NAME = 'access_token'

    # QR code storage
    QR_CODE_FOLDER = os.path.join(BASE_DIR, 'static', 'qrcodes')

    # PDF output storage
    PDF_FOLDER = os.path.join(BASE_DIR, 'static', 'pdfs')