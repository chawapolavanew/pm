import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app, raise_server_exceptions=True)


def _login() -> str:
    res = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert res.status_code == 200
    return res.json()["token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------

def test_get_board_requires_auth():
    res = client.get("/api/board")
    assert res.status_code == 401


def test_get_board_returns_five_columns():
    token = _login()
    res = client.get("/api/board", headers=auth(token))
    assert res.status_code == 200
    data = res.json()
    assert len(data["columns"]) == 5
    titles = [c["title"] for c in data["columns"]]
    assert titles == ["Backlog", "Discovery", "In Progress", "Review", "Done"]


def test_get_board_columns_have_ids_and_cardids():
    token = _login()
    data = client.get("/api/board", headers=auth(token)).json()
    for col in data["columns"]:
        assert col["id"].startswith("col-")
        assert isinstance(col["cardIds"], list)


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------

def test_rename_column():
    token = _login()
    board = client.get("/api/board", headers=auth(token)).json()
    col_id = int(board["columns"][0]["id"].removeprefix("col-"))

    res = client.patch(f"/api/columns/{col_id}", json={"title": "Todo"}, headers=auth(token))
    assert res.status_code == 200

    board2 = client.get("/api/board", headers=auth(token)).json()
    assert board2["columns"][0]["title"] == "Todo"


def test_rename_column_wrong_user_rejected():
    token = _login()
    res = client.patch("/api/columns/9999", json={"title": "X"}, headers=auth(token))
    assert res.status_code == 404


def test_rename_column_requires_auth():
    res = client.patch("/api/columns/1", json={"title": "X"})
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# Cards — create
# ---------------------------------------------------------------------------

def _first_col_id(token: str) -> int:
    board = client.get("/api/board", headers=auth(token)).json()
    return int(board["columns"][0]["id"].removeprefix("col-"))


def test_create_card():
    token = _login()
    col_id = _first_col_id(token)
    res = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "My card", "details": "Some notes"},
        headers=auth(token),
    )
    assert res.status_code == 201
    body = res.json()
    assert body["id"].startswith("card-")
    assert body["title"] == "My card"


def test_create_card_appears_in_board():
    token = _login()
    col_id = _first_col_id(token)
    card_id = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "New card", "details": ""},
        headers=auth(token),
    ).json()["id"]

    board = client.get("/api/board", headers=auth(token)).json()
    col = next(c for c in board["columns"] if c["id"] == f"col-{col_id}")
    assert card_id in col["cardIds"]
    assert board["cards"][card_id]["title"] == "New card"


def test_create_card_invalid_column():
    token = _login()
    res = client.post(
        "/api/cards",
        json={"column_id": 9999, "title": "X", "details": ""},
        headers=auth(token),
    )
    assert res.status_code == 404


def test_create_card_requires_auth():
    res = client.post("/api/cards", json={"column_id": 1, "title": "X", "details": ""})
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# Cards — update
# ---------------------------------------------------------------------------

def _create_card(token: str, title: str = "Card", details: str = "") -> int:
    col_id = _first_col_id(token)
    body = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": title, "details": details},
        headers=auth(token),
    ).json()
    return int(body["id"].removeprefix("card-"))


def test_update_card_title():
    token = _login()
    card_id = _create_card(token, "Original")
    res = client.patch(f"/api/cards/{card_id}", json={"title": "Updated"}, headers=auth(token))
    assert res.status_code == 200
    board = client.get("/api/board", headers=auth(token)).json()
    assert board["cards"][f"card-{card_id}"]["title"] == "Updated"


def test_update_card_details():
    token = _login()
    card_id = _create_card(token)
    res = client.patch(f"/api/cards/{card_id}", json={"details": "New notes"}, headers=auth(token))
    assert res.status_code == 200
    board = client.get("/api/board", headers=auth(token)).json()
    assert board["cards"][f"card-{card_id}"]["details"] == "New notes"


def test_update_nonexistent_card():
    token = _login()
    res = client.patch("/api/cards/9999", json={"title": "X"}, headers=auth(token))
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Cards — delete
# ---------------------------------------------------------------------------

def test_delete_card():
    token = _login()
    card_id = _create_card(token, "To delete")
    res = client.delete(f"/api/cards/{card_id}", headers=auth(token))
    assert res.status_code == 204

    board = client.get("/api/board", headers=auth(token)).json()
    assert f"card-{card_id}" not in board["cards"]


def test_delete_card_compacts_positions():
    token = _login()
    col_id = _first_col_id(token)
    ids = []
    for i in range(3):
        ids.append(_create_card(token, f"Card {i}"))

    client.delete(f"/api/cards/{ids[1]}", headers=auth(token))

    board = client.get("/api/board", headers=auth(token)).json()
    col = next(c for c in board["columns"] if c["id"] == f"col-{col_id}")
    assert f"card-{ids[1]}" not in col["cardIds"]
    assert col["cardIds"].index(f"card-{ids[0]}") < col["cardIds"].index(f"card-{ids[2]}")


def test_delete_nonexistent_card():
    token = _login()
    res = client.delete("/api/cards/9999", headers=auth(token))
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Cards — move
# ---------------------------------------------------------------------------

def test_move_card_to_different_column():
    token = _login()
    board = client.get("/api/board", headers=auth(token)).json()
    src_col_id = int(board["columns"][0]["id"].removeprefix("col-"))
    dst_col_id = int(board["columns"][1]["id"].removeprefix("col-"))

    card_id = _create_card(token, "Moveable")
    res = client.patch(
        f"/api/cards/{card_id}/move",
        json={"column_id": dst_col_id, "position": 0},
        headers=auth(token),
    )
    assert res.status_code == 200

    board2 = client.get("/api/board", headers=auth(token)).json()
    src_col = next(c for c in board2["columns"] if c["id"] == f"col-{src_col_id}")
    dst_col = next(c for c in board2["columns"] if c["id"] == f"col-{dst_col_id}")
    assert f"card-{card_id}" not in src_col["cardIds"]
    assert f"card-{card_id}" in dst_col["cardIds"]
    assert dst_col["cardIds"][0] == f"card-{card_id}"


def test_move_card_within_same_column():
    token = _login()
    col_id = _first_col_id(token)
    id_a = _create_card(token, "A")
    id_b = _create_card(token, "B")
    id_c = _create_card(token, "C")

    client.patch(
        f"/api/cards/{id_c}/move",
        json={"column_id": col_id, "position": 0},
        headers=auth(token),
    )
    board = client.get("/api/board", headers=auth(token)).json()
    col = next(c for c in board["columns"] if c["id"] == f"col-{col_id}")
    assert col["cardIds"][0] == f"card-{id_c}"


def test_move_card_invalid_column():
    token = _login()
    card_id = _create_card(token)
    res = client.patch(
        f"/api/cards/{card_id}/move",
        json={"column_id": 9999, "position": 0},
        headers=auth(token),
    )
    assert res.status_code == 404


def test_move_card_requires_auth():
    res = client.patch("/api/cards/1/move", json={"column_id": 1, "position": 0})
    assert res.status_code == 401
