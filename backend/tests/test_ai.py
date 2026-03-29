import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
import ai as ai_module

client = TestClient(app, raise_server_exceptions=True)


def _login() -> str:
    res = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert res.status_code == 200
    return res.json()["token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _mock_chat(content: str):
    """Return a context manager that patches ai.chat to return `content`."""
    return patch("main.ai_module" if False else "ai.chat", return_value=content)


def test_ai_ping_requires_auth():
    res = client.get("/api/ai/ping")
    assert res.status_code == 401


def test_ai_ping_returns_reply():
    token = _login()
    with patch("ai.chat", return_value="4") as mock_chat:
        res = client.get("/api/ai/ping", headers=auth(token))
    assert res.status_code == 200
    assert res.json()["reply"] == "4"
    mock_chat.assert_called_once()


def test_ai_ping_sends_correct_question():
    token = _login()
    with patch("ai.chat", return_value="4") as mock_chat:
        client.get("/api/ai/ping", headers=auth(token))
    messages = mock_chat.call_args[0][0]
    assert any("2+2" in m["content"] for m in messages)


def test_ai_chat_function_calls_openrouter():
    """Unit test: ai.chat() calls OpenAI client with the right model and messages."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "42"

    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}), \
         patch("ai.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        result = ai_module.chat([{"role": "user", "content": "hello"}])

    assert result == "42"
    mock_client.chat.completions.create.assert_called_once_with(
        model=ai_module.MODEL,
        messages=[{"role": "user", "content": "hello"}],
    )


def test_ai_chat_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    # Clear cached env in ai module
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
            ai_module.chat([{"role": "user", "content": "hi"}])
