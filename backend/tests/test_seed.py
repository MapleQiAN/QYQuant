import os


def test_seed_script_exists():
    assert os.path.exists('backend/scripts/seed.py')
