import os
from pathlib import Path

from dotenv import load_dotenv

# 从项目根目录加载 .env 文件
root_dir = Path(__file__).parent.parent.parent
env = os.getenv('FLASK_ENV', 'development')
env_file = root_dir / f'.env.{env}'

# 如果特定环境的文件不存在，尝试加载默认的 .env
if not env_file.exists():
    env_file = root_dir / '.env'

load_dotenv(env_file, override=True)


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
