import os


def test_devfiles_exist():
    assert os.path.exists('backend/docker-compose.yml')
    assert os.path.exists('backend/Makefile')
