# Backend

FastAPI app served inside Docker via uvicorn. Python package management uses `uv`.

## Structure

```
backend/
  main.py           FastAPI app — routes, lifespan
  auth.py           Token store, get_current_user dependency, check_credentials
  database.py       SQLite init, schema creation, seed, get_db context manager
  requirements.txt  Runtime dependencies (fastapi, uvicorn, bcrypt)
  requirements-dev.txt  Test dependencies (pytest, httpx)
  static/           Served at / (replaced by Next.js build in Docker)
  tests/
    conftest.py     Temp DB setup + autouse reset fixture
    test_auth.py    Login, logout, token validation tests
    test_board.py   Board, column, card CRUD + move tests
```

## Routes

| Method | Path                    | Auth | Description                        |
|--------|-------------------------|------|------------------------------------|
| POST   | /api/auth/login         | No   | Returns bearer token               |
| POST   | /api/auth/logout        | No   | Revokes token                      |
| GET    | /api/board              | Yes  | Full board (columns + cards)       |
| PATCH  | /api/columns/{id}       | Yes  | Rename column                      |
| POST   | /api/cards              | Yes  | Create card                        |
| PATCH  | /api/cards/{id}         | Yes  | Update card title/details          |
| DELETE | /api/cards/{id}         | Yes  | Delete card                        |
| PATCH  | /api/cards/{id}/move    | Yes  | Move card to column + position     |
| GET    | /api/hello              | No   | Health check                       |
| GET    | /                       | No   | Static file serving (SPA)          |

## Database

SQLite at `$DB_PATH` (default `./data/kanban.db`). Created on startup via `init_db()`.
Schema: `users`, `boards`, `columns`, `cards` — see `docs/schema.json`.
Seeded with `user`/`password` (bcrypt hash) + default 5-column board on first run.

## Auth

Stateless bearer tokens stored in an in-memory dict (`auth._tokens`). Tokens are
invalidated on logout. `get_current_user` is a FastAPI dependency injected into
all protected routes.

## Running locally (without Docker)

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
uvicorn main:app --reload
pytest tests/
```

## Dependencies

- **fastapi** — web framework
- **uvicorn[standard]** — ASGI server
- **bcrypt** — password hashing
