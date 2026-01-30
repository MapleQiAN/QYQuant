from pathlib import Path


def test_database_uses_pytest_tmpdir(app, tmp_path):
    uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    assert uri is not None
    db_path = Path(uri.replace('sqlite:///', '')).resolve()
    assert db_path.parent == tmp_path.resolve()
