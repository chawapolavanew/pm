import os
import tempfile
import sqlite3
import pytest

# Set DB_PATH before any app module is imported so database.py picks it up
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DB_PATH"] = _tmp.name


@pytest.fixture(autouse=True)
def reset_db():
    import database as db_module
    import auth as auth_module

    conn = sqlite3.connect(_tmp.name)
    conn.executescript("""
        DROP TABLE IF EXISTS cards;
        DROP TABLE IF EXISTS columns;
        DROP TABLE IF EXISTS boards;
        DROP TABLE IF EXISTS users;
    """)
    conn.close()

    db_module.init_db()
    auth_module._tokens.clear()
    yield
    auth_module._tokens.clear()
