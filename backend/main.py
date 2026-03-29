import os
from contextlib import asynccontextmanager
from typing import Annotated, Optional
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from auth import check_credentials, create_token, get_current_user, revoke_token
from database import get_db, get_board_id, get_user_id, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
def login(req: LoginRequest):
    if not check_credentials(req.username, req.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": create_token(req.username)}


@app.post("/api/auth/logout")
async def logout(request: Request):
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        revoke_token(auth.removeprefix("Bearer "))
    return {"ok": True}


# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------

@app.get("/api/board")
def get_board(username: Annotated[str, Depends(get_current_user)]):
    with get_db() as db:
        user_id = get_user_id(db, username)
        board_id = get_board_id(db, user_id)

        cols = db.execute(
            "SELECT id, title FROM columns WHERE board_id = ? ORDER BY position",
            (board_id,),
        ).fetchall()

        all_cards = db.execute(
            """
            SELECT cards.id, cards.column_id, cards.title, cards.details
            FROM cards
            JOIN columns ON cards.column_id = columns.id
            WHERE columns.board_id = ?
            ORDER BY cards.position
            """,
            (board_id,),
        ).fetchall()

    cards_by_col: dict[int, list] = {col["id"]: [] for col in cols}
    cards_dict: dict[str, dict] = {}
    for card in all_cards:
        card_id = f"card-{card['id']}"
        cards_dict[card_id] = {
            "id": card_id,
            "title": card["title"],
            "details": card["details"],
        }
        cards_by_col[card["column_id"]].append(card_id)

    columns = [
        {
            "id": f"col-{col['id']}",
            "title": col["title"],
            "cardIds": cards_by_col[col["id"]],
        }
        for col in cols
    ]

    return {"columns": columns, "cards": cards_dict}


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------

class RenameColumnRequest(BaseModel):
    title: str


@app.patch("/api/columns/{col_id}")
def rename_column(
    col_id: int,
    req: RenameColumnRequest,
    username: Annotated[str, Depends(get_current_user)],
):
    with get_db() as db:
        user_id = get_user_id(db, username)
        board_id = get_board_id(db, user_id)
        row = db.execute(
            "SELECT id FROM columns WHERE id = ? AND board_id = ?", (col_id, board_id)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Column not found")
        db.execute("UPDATE columns SET title = ? WHERE id = ?", (req.title, col_id))
    return {"ok": True}


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------

class CreateCardRequest(BaseModel):
    column_id: int
    title: str
    details: str = ""


class UpdateCardRequest(BaseModel):
    title: Optional[str] = None
    details: Optional[str] = None


class MoveCardRequest(BaseModel):
    column_id: int
    position: int


@app.post("/api/cards", status_code=201)
def create_card(
    req: CreateCardRequest,
    username: Annotated[str, Depends(get_current_user)],
):
    with get_db() as db:
        user_id = get_user_id(db, username)
        board_id = get_board_id(db, user_id)
        col = db.execute(
            "SELECT id FROM columns WHERE id = ? AND board_id = ?",
            (req.column_id, board_id),
        ).fetchone()
        if not col:
            raise HTTPException(status_code=404, detail="Column not found")

        max_pos = db.execute(
            "SELECT COALESCE(MAX(position), -1) FROM cards WHERE column_id = ?",
            (req.column_id,),
        ).fetchone()[0]
        db.execute(
            "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
            (req.column_id, req.title, req.details, max_pos + 1),
        )
        card_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    return {"id": f"card-{card_id}", "title": req.title, "details": req.details}


@app.patch("/api/cards/{card_id}")
def update_card(
    card_id: int,
    req: UpdateCardRequest,
    username: Annotated[str, Depends(get_current_user)],
):
    with get_db() as db:
        user_id = get_user_id(db, username)
        board_id = get_board_id(db, user_id)
        card = db.execute(
            """
            SELECT cards.id FROM cards
            JOIN columns ON cards.column_id = columns.id
            WHERE cards.id = ? AND columns.board_id = ?
            """,
            (card_id, board_id),
        ).fetchone()
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")

        if req.title is not None:
            db.execute("UPDATE cards SET title = ? WHERE id = ?", (req.title, card_id))
        if req.details is not None:
            db.execute("UPDATE cards SET details = ? WHERE id = ?", (req.details, card_id))

    return {"ok": True}


@app.delete("/api/cards/{card_id}", status_code=204)
def delete_card(
    card_id: int,
    username: Annotated[str, Depends(get_current_user)],
):
    with get_db() as db:
        user_id = get_user_id(db, username)
        board_id = get_board_id(db, user_id)
        card = db.execute(
            """
            SELECT cards.id, cards.column_id, cards.position FROM cards
            JOIN columns ON cards.column_id = columns.id
            WHERE cards.id = ? AND columns.board_id = ?
            """,
            (card_id, board_id),
        ).fetchone()
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")

        db.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        db.execute(
            "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
            (card["column_id"], card["position"]),
        )


@app.patch("/api/cards/{card_id}/move")
def move_card(
    card_id: int,
    req: MoveCardRequest,
    username: Annotated[str, Depends(get_current_user)],
):
    with get_db() as db:
        user_id = get_user_id(db, username)
        board_id = get_board_id(db, user_id)

        card = db.execute(
            """
            SELECT cards.id, cards.column_id, cards.position FROM cards
            JOIN columns ON cards.column_id = columns.id
            WHERE cards.id = ? AND columns.board_id = ?
            """,
            (card_id, board_id),
        ).fetchone()
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")

        target_col = db.execute(
            "SELECT id FROM columns WHERE id = ? AND board_id = ?",
            (req.column_id, board_id),
        ).fetchone()
        if not target_col:
            raise HTTPException(status_code=404, detail="Target column not found")

        src_col_id = card["column_id"]
        src_pos = card["position"]

        # Remove from source column
        db.execute(
            "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
            (src_col_id, src_pos),
        )
        # Make room in target column
        db.execute(
            "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
            (req.column_id, req.position),
        )
        # Place the card
        db.execute(
            "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
            (req.column_id, req.position, card_id),
        )

    return {"ok": True}


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

@app.get("/api/hello")
def hello():
    return {"message": "hello world"}


# Static files must be mounted last so API routes take priority
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
