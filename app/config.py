"""
Cấu hình Flask
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
APP_DIR = Path(__file__).parent

class Config:
    """Base configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG') or False
    TESTING = os.environ.get('TESTING') or False
    
    # Server settings
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # File upload settings
    UPLOAD_FOLDER = str(BASE_DIR / 'uploads')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
    
    # Model settings
    MODEL_PATH = str(BASE_DIR / 'output' / 'model.pth')
    MODEL_INPUT_SIZE = 64
    MODEL_NUM_CLASSES = 43
    
    # Output settings
    OUTPUT_DIR = str(BASE_DIR / 'output')
    AUDIO_DIR = str(BASE_DIR / 'output' / 'audio')
    VIDEO_UPLOAD_DIR = str(BASE_DIR / 'uploads' / 'videos')
    VIDEO_OUTPUT_DIR = str(BASE_DIR / 'output' / 'videos')
    
    # Create necessary directories
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(VIDEO_UPLOAD_DIR, exist_ok=True)
    os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True


# Load configuration based on environment
FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'

if FLASK_ENV == 'production':
    config = ProductionConfig
elif FLASK_ENV == 'testing':
    config = TestingConfig
else:
    config = DevelopmentConfig
