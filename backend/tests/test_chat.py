import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app, raise_server_exceptions=True)


def _login() -> str:
    res = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert res.status_code == 200
    return res.json()["token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _ai_response(reply: str, update: dict | None = None) -> str:
    return json.dumps({
        "reply": reply,
        "board_update": {
            "cards_to_create": [],
            "cards_to_update": [],
            "cards_to_delete": [],
            "cards_to_move": [],
            **(update or {}),
        },
    })


# ---------------------------------------------------------------------------
# Basic endpoint behaviour
# ---------------------------------------------------------------------------

def test_chat_requires_auth():
    res = client.post("/api/chat", json={"message": "hello"})
    assert res.status_code == 401


def test_chat_returns_reply():
    token = _login()
    with patch("ai.board_chat", return_value={
        "reply": "Hello there!",
        "board_update": {"cards_to_create": [], "cards_to_update": [], "cards_to_delete": [], "cards_to_move": []},
    }):
        res = client.post("/api/chat", json={"message": "hello"}, headers=auth(token))
    assert res.status_code == 200
    assert res.json()["reply"] == "Hello there!"
    assert res.json()["board_updated"] is False


def test_chat_passes_history_to_ai():
    token = _login()
    captured = {}

    def fake_board_chat(board, history, message):
        captured["history"] = history
        captured["message"] = message
        return {"reply": "ok", "board_update": {"cards_to_create": [], "cards_to_update": [], "cards_to_delete": [], "cards_to_move": []}}

    with patch("ai.board_chat", side_effect=fake_board_chat):
        client.post("/api/chat", json={
            "message": "second message",
            "history": [{"role": "user", "content": "first"}, {"role": "assistant", "content": "response"}],
        }, headers=auth(token))

    assert captured["message"] == "second message"
    assert len(captured["history"]) == 2


def test_chat_passes_board_to_ai():
    token = _login()
    captured = {}

    def fake_board_chat(board, history, message):
        captured["board"] = board
        return {"reply": "ok", "board_update": {"cards_to_create": [], "cards_to_update": [], "cards_to_delete": [], "cards_to_move": []}}

    with patch("ai.board_chat", side_effect=fake_board_chat):
        client.post("/api/chat", json={"message": "hi"}, headers=auth(token))

    assert "columns" in captured["board"]
    assert len(captured["board"]["columns"]) == 5


# ---------------------------------------------------------------------------
# Board update: create
# ---------------------------------------------------------------------------

def test_chat_creates_card():
    token = _login()
    board_before = client.get("/api/board", headers=auth(token)).json()
    backlog = next(c for c in board_before["columns"] if c["title"] == "Backlog")
    count_before = len(backlog["cardIds"])

    with patch("ai.board_chat", return_value={
        "reply": "Created it.",
        "board_update": {
            "cards_to_create": [{"column_title": "Backlog", "title": "AI card", "details": "From AI"}],
            "cards_to_update": [], "cards_to_delete": [], "cards_to_move": [],
        },
    }):
        res = client.post("/api/chat", json={"message": "add a card"}, headers=auth(token))

    assert res.json()["board_updated"] is True

    board_after = client.get("/api/board", headers=auth(token)).json()
    backlog_after = next(c for c in board_after["columns"] if c["title"] == "Backlog")
    assert len(backlog_after["cardIds"]) == count_before + 1
    new_card_id = backlog_after["cardIds"][-1]
    assert board_after["cards"][new_card_id]["title"] == "AI card"


def test_chat_create_card_unknown_column_is_ignored():
    token = _login()
    board_before = client.get("/api/board", headers=auth(token)).json()
    total_before = len(board_before["cards"])

    with patch("ai.board_chat", return_value={
        "reply": "Tried.",
        "board_update": {
            "cards_to_create": [{"column_title": "Nonexistent", "title": "X", "details": ""}],
            "cards_to_update": [], "cards_to_delete": [], "cards_to_move": [],
        },
    }):
        client.post("/api/chat", json={"message": "add card"}, headers=auth(token))

    board_after = client.get("/api/board", headers=auth(token)).json()
    assert len(board_after["cards"]) == total_before


# ---------------------------------------------------------------------------
# Board update: update
# ---------------------------------------------------------------------------

def test_chat_updates_card():
    token = _login()
    # Create a card to update
    board = client.get("/api/board", headers=auth(token)).json()
    col_id = int(board["columns"][0]["id"].removeprefix("col-"))
    card_resp = client.post("/api/cards",
        json={"column_id": col_id, "title": "Old title", "details": "Old"},
        headers=auth(token)).json()
    card_id = card_resp["id"]

    with patch("ai.board_chat", return_value={
        "reply": "Updated.",
        "board_update": {
            "cards_to_create": [],
            "cards_to_update": [{"card_id": card_id, "title": "New title", "details": "New"}],
            "cards_to_delete": [], "cards_to_move": [],
        },
    }):
        res = client.post("/api/chat", json={"message": "update it"}, headers=auth(token))

    assert res.json()["board_updated"] is True
    board_after = client.get("/api/board", headers=auth(token)).json()
    assert board_after["cards"][card_id]["title"] == "New title"


# ---------------------------------------------------------------------------
# Board update: delete
# ---------------------------------------------------------------------------

def test_chat_deletes_card():
    token = _login()
    board = client.get("/api/board", headers=auth(token)).json()
    col_id = int(board["columns"][0]["id"].removeprefix("col-"))
    card_id = client.post("/api/cards",
        json={"column_id": col_id, "title": "To delete", "details": ""},
        headers=auth(token)).json()["id"]

    with patch("ai.board_chat", return_value={
        "reply": "Deleted.",
        "board_update": {
            "cards_to_create": [], "cards_to_update": [],
            "cards_to_delete": [{"card_id": card_id}],
            "cards_to_move": [],
        },
    }):
        res = client.post("/api/chat", json={"message": "delete it"}, headers=auth(token))

    assert res.json()["board_updated"] is True
    board_after = client.get("/api/board", headers=auth(token)).json()
    assert card_id not in board_after["cards"]


# ---------------------------------------------------------------------------
# Board update: move
# ---------------------------------------------------------------------------

def test_chat_moves_card():
    token = _login()
    board = client.get("/api/board", headers=auth(token)).json()
    src_col_id = int(board["columns"][0]["id"].removeprefix("col-"))
    card_id = client.post("/api/cards",
        json={"column_id": src_col_id, "title": "Moveable", "details": ""},
        headers=auth(token)).json()["id"]

    with patch("ai.board_chat", return_value={
        "reply": "Moved it.",
        "board_update": {
            "cards_to_create": [], "cards_to_update": [], "cards_to_delete": [],
            "cards_to_move": [{"card_id": card_id, "column_title": "Done"}],
        },
    }):
        res = client.post("/api/chat", json={"message": "move it to done"}, headers=auth(token))

    assert res.json()["board_updated"] is True
    board_after = client.get("/api/board", headers=auth(token)).json()
    done_col = next(c for c in board_after["columns"] if c["title"] == "Done")
    src_col = next(c for c in board_after["columns"] if c["id"] == f"col-{src_col_id}")
    assert card_id in done_col["cardIds"]
    assert card_id not in src_col["cardIds"]


# ---------------------------------------------------------------------------
# ai.board_chat unit tests
# ---------------------------------------------------------------------------

def test_board_chat_builds_correct_messages():
    from unittest.mock import MagicMock
    import ai as ai_module

    board = {
        "columns": [{"id": "col-1", "title": "Backlog", "cardIds": ["card-1"]}],
        "cards": {"card-1": {"id": "card-1", "title": "My card", "details": "Notes"}},
    }

    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps({
        "reply": "Done",
        "board_update": {"cards_to_create": [], "cards_to_update": [], "cards_to_delete": [], "cards_to_move": []},
    })

    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}), \
         patch("ai.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        result = ai_module.board_chat(board, [], "hello")

    call_kwargs = mock_client.chat.completions.create.call_args
    messages = call_kwargs[1]["messages"] if call_kwargs[1] else call_kwargs[0][1]
    assert messages[0]["role"] == "system"
    assert "Backlog" in messages[0]["content"]
    assert "card-1" in messages[0]["content"]
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "hello"
    assert result["reply"] == "Done"


def test_board_chat_handles_malformed_json():
    import ai as ai_module
    from unittest.mock import MagicMock

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "not json at all"

    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}), \
         patch("ai.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        result = ai_module.board_chat({"columns": [], "cards": {}}, [], "hi")

    assert result["reply"] == ""
    assert result["board_update"]["cards_to_create"] == []
