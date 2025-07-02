import sqlite3
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
    SecurityScopes,
)
import jwt

import auth.schemas
import config


def db_connection():
    connection = sqlite3.connect(config.DB_FILE, autocommit=False)
    try:
        yield connection
    finally:
        connection.commit()
        connection.close()


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
    except jwt.InvalidTokenError as err:
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
