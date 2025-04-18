import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    five_gigs = 5 * 1024 * 1024 * 1024
    MAX_CONTENT_LENGTH = os.getenv('MAX_CONTENT_LENGTH', five_gigs)
    DEFAULT_QUOTA = os.getenv('DEFAULT_QUOTA', five_gigs)
    ADMIN_DISCORD_USER_ID = os.getenv('ADMIN_DISCORD_USER_ID', 0)
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    SECRET_KEY = os.getenv('SECRET_KEY','supersecretkey')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'zip', 'rar', '7z','srt'}
    REDIRECT_URI = os.getenv('REDIRECT_URI', 'https://localhost:5000/callback')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PREMIUM_DISCORD_USER_ID = os.getenv('PREMIUM_DISCORD_USER_ID', 0)
    PREFERRED_URL_SCHEME = 'https'
    FRONTEND_URI = os.getenv('FRONTEND_URI', 'https://localhost:3000')
    MONITOR_SERVICE_URL = os.getenv('MONITOR_SERVICE_URL', 'http://localhost:61208/api/3/all')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-for-jwt')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hour in seconds
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))  # 30 days in seconds