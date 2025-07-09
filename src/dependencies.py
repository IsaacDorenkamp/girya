import datetime
import sqlite3
from typing import Annotated, cast

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
    SecurityScopes,
)
import jwt

import auth.schemas
import config


def setup():
    sqlite3.register_adapter(datetime.datetime, lambda dt: int(dt.timestamp()))
    sqlite3.register_converter("datetime", lambda dtstr: datetime.datetime.fromtimestamp(int(dtstr), tz=datetime.timezone.utc))


_usages: int = 0
_connection: sqlite3.Connection | None = None


def db_connection():
    global _usages
    global _connection

    if _usages == 0:
        _connection = sqlite3.Connection(config.DB_FILE, autocommit=False)

    _usages += 1

    connection = cast(sqlite3.Connection, _connection)
    try:
        yield connection
    finally:
        # only finalize connection if all usages of dependency have exited
        # references a custom attribute used to manually close a connection
        # for very specific purposes
        _usages -= 1
        if _usages == 0:
            connection.commit()
            connection.close()
            _connection = None


# security
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login"
)

def get_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
) -> auth.schemas.User:
    import auth.services  # imported here to avoid circular import
    try:
        payload = jwt.decode(token, config.JWT_KEY, audience=config.JWT_AUD, algorithms=config.JWT_ALGS)
        if "sub" not in payload:
            raise jwt.InvalidTokenError()
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials."
        )

    scopes = [scope for scope in payload.get("scope", "").split(" ") if scope]
    for scope in security_scopes.scopes:
        if scope not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

    user = auth.services.find_user(connection, payload["sub"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user
