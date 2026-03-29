# Database

SQLite, stored at `./data/kanban.db` (relative to the running container's working directory). Created automatically on first startup.

## Schema

Four tables: `users`, `boards`, `columns`, `cards`. See `docs/schema.json` for the full column definitions.

```
users
  id            INTEGER PK
  username      TEXT UNIQUE NOT NULL
  password_hash TEXT NOT NULL

boards
  id            INTEGER PK
  user_id       INTEGER FK -> users.id  (CASCADE DELETE)
  name          TEXT NOT NULL

columns
  id            INTEGER PK
  board_id      INTEGER FK -> boards.id (CASCADE DELETE)
  title         TEXT NOT NULL
  position      INTEGER NOT NULL

cards
  id            INTEGER PK
  column_id     INTEGER FK -> columns.id (CASCADE DELETE)
  title         TEXT NOT NULL
  details       TEXT NOT NULL
  position      INTEGER NOT NULL
```

## Ordering

`position` is a zero-indexed integer. When a card or column is moved, the application re-assigns position values for the affected rows. Reads always ORDER BY position ASC.

## Passwords

`password_hash` stores a bcrypt hash. Plain text passwords are never written to the database. For the MVP the single user is seeded on startup; the hash is computed at seed time.

## Startup behaviour

On startup, FastAPI runs `CREATE TABLE IF NOT EXISTS` for all four tables, then checks whether the seed user exists. If not, it inserts `username='user'` with the bcrypt hash of `'password'` and creates their default board with five columns (Backlog, Discovery, In Progress, Review, Done).

## Multi-user readiness

The schema supports multiple users. The MVP restricts login to a single hardcoded user, but no schema changes are needed to support more users in future.
