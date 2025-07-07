from __future__ import annotations
import re
import typing

from argon2 import PasswordHasher
from fastapi import HTTPException

from config import DEFAULT_AUTH_GROUP
from .exceptions import EmailValidationError
from .schemas import User, UserRecord


def validate_email(email: str):
    """
    Validated an e-mail address. Does not support
    IP addresses as domains.

    :param email: The e-mail address.
    :raises EmailValidationError: If the e-mail address is invalid.
    """
    local_part_len = len(email.split("@")[0])
    if local_part_len > 64:
        raise EmailValidationError("Local part of e-mail exceeds 64 characters.")

    is_quoted = False
    is_local_part = True
    is_escaped = False
    last_was_dot = False
    domain = ""

    for character in email:
        if is_local_part:
            if character == '"':
                if is_quoted and not is_escaped:
                    is_quoted = False
                elif is_escaped:
                    is_escaped = False
                else:
                    is_quoted = True
            elif character == '\\':
                if is_escaped:
                    is_escaped = False

                is_escaped = True
                last_was_dot = False
                continue
            elif re.match(r'^[a-zA-Z0-9!#\$%\&\'\*\+\-/\=\?\^_\`\{\|\}\~]$', character):
                last_was_dot = False
                is_escaped = False
                continue
            elif re.match(r'[\(\),:;<>\[\]]', character):
                if not is_quoted:
                    raise EmailValidationError("Character '%s' only allowed in quotes." % character)
            elif character == '@':
                if not is_quoted:
                    is_local_part = False
                    last_was_dot = False
                    continue
            elif re.match(r'^[\t ]$', character):
                if not is_quoted:
                    raise EmailValidationError("Whitespace only allowed in quotes." % character)
            elif character == '.':
                if last_was_dot and not is_quoted:
                    raise EmailValidationError("Two dots may only occur next to each other within quotes.")
        else:
            if character == '@':
                raise EmailValidationError("@ not allowed in the domain")
            else:
                domain += character

    domain_parts = domain.split(".")
    for domain_part in domain_parts:
        if len(domain_part) == 0:
            raise EmailValidationError("Domain should not have empty domain segments")
        elif domain_part.startswith('-') or domain_part.endswith('-'):
            raise EmailValidationError("Domain part should not start or end with '-'")

    validation = re.match(r'^[a-zA-Z0-9\-]+(\.[a-zA-Z0-9\-]+)*$', domain)
    if not validation:
        raise EmailValidationError("Invalid domain '%s'" % domain)


def create_user(connection: sqlite3.Connection, email: str, password: str, first_name: str,
                last_name: str) -> User:
    """
    Create a user in the database.

    :param connection: The connection used to insert the user.
    :param email: The user's email address.
    :param password: The plaintext password to use for this account.
    :param first_name: The user's first name.
    :param last_name: The user's last name.
    """
    validate_email(email)
    hasher = PasswordHasher()
    pw_hash = hasher.hash(password)
    cursor = connection.execute("INSERT INTO user (email, first_name, last_name, password, auth_group) VALUES "
        "(:email, :first_name, :last_name, :password, :auth_group)",
        { "email": email, "first_name": first_name, "last_name": last_name, "password": pw_hash,
         "auth_group": DEFAULT_AUTH_GROUP }
    )
    if cursor.lastrowid is not None:
        return User(email=email, first_name=first_name, last_name=last_name, auth_group=DEFAULT_AUTH_GROUP,
                    id=cursor.lastrowid)
    else:
        raise HTTPException(status_code=500, detail="An error occurred creating a user.")


def find_user(connection: sqlite3.Connection, email: str) -> UserRecord | None:
    result = connection.execute("SELECT email, first_name, last_name, password, auth_group, id FROM user WHERE email = :email",
                                { "email": email })
    user = result.fetchone()
    if user is None:
        return None

    email, first_name, last_name, password, auth_group, user_id = user
    return UserRecord(email=email, first_name=first_name, last_name=last_name, password=password,
                      auth_group=auth_group, id=user_id)


if typing.TYPE_CHECKING:
    import sqlite3

