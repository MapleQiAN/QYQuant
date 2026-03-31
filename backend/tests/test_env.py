import os
from datetime import timedelta


def test_env_files_exist():
    assert os.path.exists('backend/.env.development')
    assert os.path.exists('backend/.env.test')
    assert os.path.exists('backend/.env.production')


def test_default_access_token_ttl_is_one_hour(app):
    assert app.config['JWT_ACCESS_TOKEN_EXPIRES'] == timedelta(minutes=60)
