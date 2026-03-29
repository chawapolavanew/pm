import pytest
from fastapi.testclient import TestClient
from main import app
import auth as auth_module

client = TestClient(app)


def test_login_success():
    res = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert res.status_code == 200
    assert "token" in res.json()


def test_login_wrong_password():
    res = client.post("/api/auth/login", json={"username": "user", "password": "wrong"})
    assert res.status_code == 401


def test_login_unknown_user():
    res = client.post("/api/auth/login", json={"username": "nobody", "password": "password"})
    assert res.status_code == 401


def test_logout_invalidates_token():
    token = client.post(
        "/api/auth/login", json={"username": "user", "password": "password"}
    ).json()["token"]

    res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert token not in auth_module._tokens


def test_logout_without_token_is_safe():
    res = client.post("/api/auth/logout")
    assert res.status_code == 200


def test_hello_is_public():
    res = client.get("/api/hello")
    assert res.status_code == 200


def test_get_current_user_rejects_bad_token():
    from auth import get_current_user
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        get_current_user("Bearer bad-token")
    assert exc.value.status_code == 401
