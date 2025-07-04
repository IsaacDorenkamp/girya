import sqlite3

import pytest

from auth import services


@pytest.mark.unit
@pytest.mark.parametrize("email", [
    "email@example.com",
    "firstname.lastname@example.com",
    "email@subdomain.example.com",
    "firstname+lastname@example.com",
    "\"email\"@example.com",
    "1234567890@example.com",
    "email@example-one.com",
    "_______@example.com",
    "email@example.name",
    "email@example.museum",
    "email@example.co.jp",
    "firstname-lastname@example.com",
    "much.\"more\\ unusual\"@example.com",
    "very.unusual.\"@\".unusual.com@example.com",
    r'"very.(),:;<>[]\".VERY.\"very@\\ \"very\".unusual"@strange.example.com',
])
def test_validate_email_success(email: str):
    services.validate_email(email)  # test will fail if email is invalid


@pytest.mark.unit
def test_create_user(db_connection: sqlite3.Connection):
    services.create_user(db_connection, "test@example.com", "Test", "Person", "password")
    cur = db_connection.execute("SELECT id FROM user WHERE email='test@example.com'")
    result = cur.fetchone()
    assert result


@pytest.mark.unit
def test_create_user_conflict(db_connection: sqlite3.Connection):
    services.create_user(db_connection, "test@example.com", "Test", "Person", "password")
    with pytest.raises(sqlite3.IntegrityError):
        services.create_user(db_connection, "test@example.com", "Test", "Person", "password")


@pytest.mark.unit
def test_find_user(db_connection: sqlite3.Connection):
    assert services.find_user(db_connection, "test@example.com") is None

    db_connection.execute("INSERT INTO user(email, first_name, last_name, password, auth_group) VALUES "
        "('test@example.com', 'Test', 'Person', 'hash', 'common')")
    user = services.find_user(db_connection, "test@example.com")
    assert user
    assert user.email == "test@example.com"
    assert user.first_name == "Test"
    assert user.last_name == "Person"
    assert user.password == "hash"
