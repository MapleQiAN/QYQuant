import os


def test_env_files_exist():
    assert os.path.exists('backend/.env.development')
    assert os.path.exists('backend/.env.test')
    assert os.path.exists('backend/.env.production')
