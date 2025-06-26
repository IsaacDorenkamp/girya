from __future__ import annotations
import typing

from fastapi.testclient import TestClient
import jwt
import pytest

from auth import services
from config import JWT_KEY, JWT_ALGS, JWT_AUD


@pytest.mark.integration
def test_create_user(test_client: TestClient):
    response = test_client.post("/auth/users", json={
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "Person",
        "password": "password",
    })
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "Person"
    assert "password" not in data


@pytest.mark.integration
def test_login(test_client: TestClient, db_connection: sqlite3.Connection):
    services.create_user(db_connection, "test@example.com", "password", "Test", "Person")

    fail_response = test_client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "failure",
    })
    assert fail_response.status_code == 401

    response = test_client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password",
    })
    assert response.status_code == 200

    result = response.json()
    access_token = result["access"]
    refresh_token = result["refresh"]

    decoded_access = jwt.decode(access_token, JWT_KEY, audience=JWT_AUD, algorithms=JWT_ALGS)
    assert decoded_access["sub"] == "test@example.com"

    decoded_refresh = jwt.decode(refresh_token, JWT_KEY, audience=JWT_AUD, algorithms=JWT_ALGS)
    assert decoded_refresh["sub"] == "test@example.com"
    assert decoded_refresh["scope"] == "refresh"


@pytest.mark.integration
def test_refresh(test_client: TestClient, simple_refresh_token: str):
    response = test_client.post("/auth/refresh", json={
        "refresh": simple_refresh_token,
    })
    assert response.status_code == 200

    result = response.json()
    access_token = result["access"]
    refresh_token = result["refresh"]

    decoded_access = jwt.decode(access_token, JWT_KEY, audience=JWT_AUD, algorithms=JWT_ALGS)
    assert decoded_access["sub"] == "test@example.com"

    decoded_refresh = jwt.decode(refresh_token, JWT_KEY, audience=JWT_AUD, algorithms=JWT_ALGS)
    assert decoded_refresh["sub"] == "test@example.com"
    assert decoded_refresh["scope"] == "refresh"

if typing.TYPE_CHECKING:
    import sqlite3
