from fastapi.testclient import TestClient
import jwt
import pytest

import sqlite3
import time

from main import app
from config import JWT_ALGO, JWT_AUD, JWT_ISS, JWT_KEY
from dependencies import db_connection as db_conn_dep


def _create_tables(connection):
    connection.executescript("""
BEGIN;
CREATE TABLE user(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR UNIQUE NOT NULL,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    password VARCHAR NOT NULL
);
CREATE TABLE lift(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    slug VARCHAR UNIQUE NOT NULL
);
CREATE TABLE split(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    slug VARCHAR UNIQUE NOT NULL
);
CREATE TABLE split_lift(
    split_id INTEGER,
    lift_id INTEGER,
    PRIMARY KEY (split_id, lift_id),
    FOREIGN KEY (split_id) REFERENCES split(id),
    FOREIGN KEY (lift_id) REFERENCES lift(id),
    UNIQUE(split_id, lift_id) ON CONFLICT ROLLBACK
);
COMMIT;
""")


@pytest.fixture(scope="function", autouse=True)
def db_connection():
    connection = sqlite3.connect(":memory:", check_same_thread=False)

    _create_tables(connection)

    app.dependency_overrides[db_conn_dep] = lambda: connection
    yield connection
    del app.dependency_overrides[db_conn_dep]


@pytest.fixture(scope="function")
def test_client():
    return TestClient(app)


@pytest.fixture
def simple_access_token():
    return jwt.encode({
        "iss": JWT_ISS,
        "sub": "test@example.com",
        "aud": JWT_AUD,
        "exp": int(time.time()) + (60 * 5),
    }, JWT_KEY, algorithm=JWT_ALGO)


@pytest.fixture
def simple_refresh_token():
    return jwt.encode({
        "iss": JWT_ISS,
        "sub": "test@example.com",
        "aud": JWT_AUD,
        "exp": int(time.time()) + (60 * 60),
        "scope": "refresh",
    }, JWT_KEY, algorithm=JWT_ALGO)

