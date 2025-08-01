import argon2
from fastapi.testclient import TestClient
import jwt
import pytest

import sqlite3
import time

import auth.schemas
from main import app
import config
from config import JWT_ALGO, JWT_AUD, JWT_ISS, JWT_KEY, PERMISSIONS_GROUPS
from dependencies import db_connection as db_conn_dep


def _create_tables(connection):
    connection.executescript("""
BEGIN;
CREATE TABLE user(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR UNIQUE NOT NULL,
    auth_group VARCHAR NOT NULL,
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
    split_id INTEGER NOT NULL,
    lift_id INTEGER NOT NULL,
    PRIMARY KEY (split_id, lift_id),
    FOREIGN KEY (split_id) REFERENCES split(id) ON DELETE CASCADE,
    FOREIGN KEY (lift_id) REFERENCES lift(id) ON DELETE CASCADE,
    UNIQUE(split_id, lift_id) ON CONFLICT ROLLBACK
);
CREATE TABLE workout(
    at DATETIME NOT NULL,
    slug VARCHAR PRIMARY KEY,
    split_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (split_id) REFERENCES split(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);
CREATE TABLE lift_set(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lift_slug VARCHAR NOT NULL,
    workout_slug VARCHAR NOT NULL,
    reps INTEGER NOT NULL,
    weight REAL NOT NULL,
    weight_unit VARCHAR NOT NULL,
    FOREIGN KEY (lift_slug) REFERENCES lift(slug) ON DELETE CASCADE,
    FOREIGN KEY (workout_slug) REFERENCES workout(slug) ON DELETE CASCADE
);
COMMIT;
""")


@pytest.fixture(scope="function", autouse=True)
def db_connection():
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.execute("PRAGMA foreign_keys = 1")

    _create_tables(connection)

    app.dependency_overrides[db_conn_dep] = lambda: connection
    yield connection
    del app.dependency_overrides[db_conn_dep]


@pytest.fixture(scope="function")
def test_client():
    orig_env = config.ENVIRONMENT
    config.ENVIRONMENT = "test"
    with TestClient(app) as client:
        yield client
    config.ENVIRONMENT = orig_env


@pytest.fixture
def simple_user(db_connection: sqlite3.Connection) -> auth.schemas.User:
    hashed = argon2.PasswordHasher().hash("simple")
    cursor = db_connection.execute("""INSERT INTO user (email, first_name, last_name, password, auth_group)
VALUES ("test@example.com", "Simple", "User", "%s", "common") RETURNING id""" % hashed)
    user_id = cursor.fetchone()[0]
    return auth.schemas.User(
        email="test@example.com",
        first_name="Simple",
        last_name="User",
        auth_group="common",
        id=user_id,
    )


@pytest.fixture
def admin_user(db_connection: sqlite3.Connection) -> auth.schemas.User:
    hashed = argon2.PasswordHasher().hash("admin")
    cursor = db_connection.execute("""INSERT INTO user (email, first_name, last_name, password, auth_group)
VALUES ("admin@example.com", "Admin", "User", "%s", "admin") RETURNING id""" % hashed)
    user_id = cursor.fetchone()[0]
    return auth.schemas.User(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        auth_group="admin",
        id=user_id,
    )


@pytest.fixture
def simple_access_token(simple_user: auth.schemas.User) -> str:
    return jwt.encode({
        "iss": JWT_ISS,
        "sub": "test@example.com",
        "aud": JWT_AUD,
        "exp": int(time.time()) + (60 * 5),
        "scope": PERMISSIONS_GROUPS["common"]
    }, JWT_KEY, algorithm=JWT_ALGO)


@pytest.fixture
def simple_refresh_token(simple_user: auth.schemas.User) -> str:
    return jwt.encode({
        "iss": JWT_ISS,
        "sub": "test@example.com",
        "aud": JWT_AUD,
        "exp": int(time.time()) + (60 * 60),
        "scope": "refresh",
    }, JWT_KEY, algorithm=JWT_ALGO)


@pytest.fixture
def admin_access_token(admin_user: auth.schemas.User) -> str:
    return jwt.encode({
        "iss": JWT_ISS,
        "sub": "admin@example.com",
        "aud": JWT_AUD,
        "exp": int(time.time()) + (60 * 5),
        "scope": PERMISSIONS_GROUPS["admin"],
    }, JWT_KEY, algorithm=JWT_ALGO)

