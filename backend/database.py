import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", "./data/kanban.db")

_DEFAULT_COLUMNS = ["Backlog", "Discovery", "In Progress", "Review", "Done"]


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS boards (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name    TEXT NOT NULL DEFAULT 'My Board'
            );
            CREATE TABLE IF NOT EXISTS columns (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
                title    TEXT NOT NULL,
                position INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cards (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                column_id INTEGER NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
                title     TEXT NOT NULL,
                details   TEXT NOT NULL DEFAULT '',
                position  INTEGER NOT NULL
            );
        """)

    # Seed user + board if not present
    with get_db() as db:
        row = db.execute("SELECT id FROM users WHERE username = 'user'").fetchone()
        if row:
            return

        import bcrypt
        pw_hash = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode()
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES ('user', ?)", (pw_hash,)
        )

    with get_db() as db:
        user_id = db.execute(
            "SELECT id FROM users WHERE username = 'user'"
        ).fetchone()["id"]
        db.execute(
            "INSERT INTO boards (user_id, name) VALUES (?, 'My Board')", (user_id,)
        )

    with get_db() as db:
        user_id = db.execute(
            "SELECT id FROM users WHERE username = 'user'"
        ).fetchone()["id"]
        board_id = db.execute(
            "SELECT id FROM boards WHERE user_id = ?", (user_id,)
        ).fetchone()["id"]
        for position, title in enumerate(_DEFAULT_COLUMNS):
            db.execute(
                "INSERT INTO columns (board_id, title, position) VALUES (?, ?, ?)",
                (board_id, title, position),
            )


def get_user_id(db: sqlite3.Connection, username: str) -> int:
    row = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if not row:
        raise ValueError(f"User not found: {username}")
    return row["id"]


def get_board_id(db: sqlite3.Connection, user_id: int) -> int:
    row = db.execute(
        "SELECT id FROM boards WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not row:
        raise ValueError("Board not found")
    return row["id"]


def verify_password(plain: str, hashed: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(plain.encode(), hashed.encode())
