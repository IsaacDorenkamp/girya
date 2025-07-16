import datetime
import sqlite3
import threading
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
    SecurityScopes,
)
import jwt
from starlette.requests import Request

import auth.schemas
import config


def setup():
    sqlite3.register_adapter(datetime.datetime, lambda dt: int(dt.timestamp()))
    sqlite3.register_converter("datetime", lambda dtstr: datetime.datetime.fromtimestamp(int(dtstr), tz=datetime.timezone.utc))


_conn_lock = threading.Lock()
_connections: dict[int, tuple[int, sqlite3.Connection]] = {}


def db_connection(request: Request):
    global _conn_lock
    global _connections

    req_id = id(request)
    with _conn_lock:
        entry = _connections.get(req_id)
        if entry is None:
            usages = 1
            connection = sqlite3.Connection(config.DB_FILE, autocommit=False, check_same_thread=False)
        else:
            usages = entry[0] + 1
            connection = entry[1]
        
        _connections[req_id] = (usages, connection)

    try:
        yield connection
    finally:
        # only finalize connection if all usages of dependency have exited
        # references a custom attribute used to manually close a connection
        # for very specific purposes
        with _conn_lock:
            entry = _connections[req_id]
            usages = entry[0] - 1
            if usages == 0:
                connection.commit()
                connection.close()
                del _connections[req_id]
            else:
                _connections[req_id] = (usages, connection)


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
