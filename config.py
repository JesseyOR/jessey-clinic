import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Business rules
    TAX_RATE = float(os.getenv('TAX_RATE', 0.10))
    LOW_STOCK_THRESHOLD = int(os.getenv('LOW_STOCK_THRESHOLD', 20))
    EXPIRY_WARNING_DAYS = int(os.getenv('EXPIRY_WARNING_DAYS', 30))
    
    # Paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    @staticmethod
    def init_app(app):
        """Initialize app with configuration (create necessary folders)."""
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        for sub in ['prescriptions', 'temp']:
            os.makedirs(os.path.join(Config.UPLOAD_FOLDER, sub), exist_ok=True)
        os.makedirs(os.path.join(Config.BASE_DIR, 'logs'), exist_ok=True)
        os.makedirs(os.path.join(Config.BASE_DIR, 'backups', 'daily'), exist_ok=True)
        os.makedirs(os.path.join(Config.BASE_DIR, 'backups', 'manual'), exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL', 'sqlite:///jessey_clinic_dev.db')


class ProductionConfig(Config):
    DEBUG = False
    # ✅ FALLBACK PROVIDED – NO raise ValueError
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///jessey_clinic.db')
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///:memory:')


# Environment mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

flask_env = os.getenv('FLASK_ENV', 'development')
ActiveConfig = config_map.get(flask_env, DevelopmentConfig)
