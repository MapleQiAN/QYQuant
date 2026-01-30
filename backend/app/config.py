import os

from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    def __init__(self):
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
        self.JWT_SECRET_KEY = os.getenv('JWT_SECRET', 'dev-jwt-secret')
        self.SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:5174').split(',')
        self.JSON_SORT_KEYS = False
        self.PROPAGATE_EXCEPTIONS = True


class DevConfig(BaseConfig):
    def __init__(self):
        super().__init__()
        self.DEBUG = True


class TestConfig(BaseConfig):
    def __init__(self):
        super().__init__()
        self.TESTING = True
        self.DEBUG = False


class ProdConfig(BaseConfig):
    def __init__(self):
        super().__init__()
        self.DEBUG = False


def get_config(env=None):
    env = env or os.getenv('FLASK_ENV', 'development')
    config_cls = {
        'development': DevConfig,
        'testing': TestConfig,
        'production': ProdConfig,
    }.get(env, DevConfig)
    return config_cls()
