import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv

# 从项目根目录加载 .env 文件
root_dir = Path(__file__).parent.parent.parent
env = os.getenv('FLASK_ENV', 'development')
env_file = root_dir / f'.env.{env}'

# 如果特定环境的文件不存在，尝试加载默认的 .env
if not env_file.exists():
    env_file = root_dir / '.env'

load_dotenv(env_file, override=False)


class BaseConfig:
    def __init__(self):
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
        self.JWT_SECRET_KEY = os.getenv('JWT_SECRET', 'dev-jwt-secret')
        self.SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

        # 验证数据库配置
        if not self.SQLALCHEMY_DATABASE_URI:
            raise RuntimeError(
                "DATABASE_URL not found in environment. "
                f"Ensure {env_file} exists and contains DATABASE_URL."
            )

        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:5174').split(',')
        self.JSON_SORT_KEYS = False
        self.PROPAGATE_EXCEPTIONS = True
        self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_MINUTES', '60')))
        self.JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_DAYS', '30')))
        self.JWT_TOKEN_LOCATION = ["headers"]
        self.JWT_COOKIE_SECURE = os.getenv('JWT_COOKIE_SECURE', 'false').lower() == 'true'
        self.JWT_COOKIE_SAMESITE = os.getenv('JWT_COOKIE_SAMESITE', 'Strict')
        self.AUTH_SMS_CODE_TTL = int(os.getenv('AUTH_SMS_CODE_TTL', '300'))
        self.AUTH_SMS_THROTTLE_SECONDS = int(os.getenv('AUTH_SMS_THROTTLE_SECONDS', '60'))
        self.AUTH_SMS_MAX_FAILURES = int(os.getenv('AUTH_SMS_MAX_FAILURES', '5'))
        self.AUTH_SMS_LOCK_SECONDS = int(os.getenv('AUTH_SMS_LOCK_SECONDS', '1800'))
        self.AUTH_FIXED_SMS_CODE = os.getenv('AUTH_FIXED_SMS_CODE')
        self.PAYMENT_SANDBOX = os.getenv('PAYMENT_SANDBOX', 'true').lower() == 'true'
        self.CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
        self.CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
        self.CELERYD_CONCURRENCY = int(os.getenv('CELERYD_CONCURRENCY', '10'))
        self.CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv('CELERY_TASK_SOFT_TIME_LIMIT', '300'))
        self.CELERY_TASK_TIME_LIMIT = int(os.getenv('CELERY_TASK_TIME_LIMIT', '330'))
        self.FILE_STORAGE_DIR = os.getenv('FILE_STORAGE_DIR')
        self.MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.example.com')
        self.MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
        self.MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
        self.MAIL_USERNAME = os.getenv('MAIL_USERNAME')
        self.MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
        self.MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@qyquant.com')
        self.OAUTH_WECHAT_CLIENT_ID = os.getenv('OAUTH_WECHAT_CLIENT_ID', '')
        self.OAUTH_WECHAT_CLIENT_SECRET = os.getenv('OAUTH_WECHAT_CLIENT_SECRET', '')
        self.OAUTH_GITHUB_CLIENT_ID = os.getenv('OAUTH_GITHUB_CLIENT_ID', '')
        self.OAUTH_GITHUB_CLIENT_SECRET = os.getenv('OAUTH_GITHUB_CLIENT_SECRET', '')
        self.OAUTH_GOOGLE_CLIENT_ID = os.getenv('OAUTH_GOOGLE_CLIENT_ID', '')
        self.OAUTH_GOOGLE_CLIENT_SECRET = os.getenv('OAUTH_GOOGLE_CLIENT_SECRET', '')
        self.FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'http://localhost:5173')


class DevConfig(BaseConfig):
    def __init__(self):
        super().__init__()
        self.DEBUG = True


class TestConfig(BaseConfig):
    def __init__(self):
        super().__init__()
        self.TESTING = True
        self.DEBUG = False
        self.AUTH_FIXED_SMS_CODE = '123456'
        self.JWT_COOKIE_SECURE = False


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
