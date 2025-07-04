import datetime
import sqlite3
import threading
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


# FastAPI usually caches dependencies, so that a database connection
# would only be instantiated once and not a second time. However,
# the Security() dependency type uses security_scopes to generate its
# cache key, causing it to not use the same shared dependency value.
# This normally might not be very noticeable, but it completely breaks
# with a database connection, which is used by the get_user dependency.
# I will use threaindg.local here to use only a single connection which
# will be re-used on multiple invocations. If this app is ever updated
# to use asyncio, this will ensure that only one connection is used per
# thread. It doesn't seem to break tests, but it does break in-vivo
# usage. I assume this is because tests use an in-memory database, while
# in-vivo usage uses an actual file, which appears to become locked when
# a connection is established.
sqlite_ctx = threading.local()


def db_connection():
    if not hasattr(sqlite_ctx, "usages"):
        sqlite_ctx.usages = 0
        sqlite_ctx.connection = None

    if sqlite_ctx.usages == 0:
        connection = sqlite3.connect(config.DB_FILE, autocommit=False)
        connection.execute("PRAGMA foreign_keys = 1")
        sqlite_ctx.usages = 1
        sqlite_ctx.connection = connection
    else:
        connection = cast(sqlite3.Connection, sqlite_ctx.connection)
        sqlite_ctx.usages += 1

    try:
        yield connection
    finally:
        # only finalize connection if all usages of dependency have exited
        sqlite_ctx.usages -= 1
        if sqlite_ctx.usages == 0:
            connection.commit()
            connection.close()
            sqlite_ctx.connection = None


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
    except jwt.InvalidTokenError:
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
