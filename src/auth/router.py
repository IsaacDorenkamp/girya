import sqlite3
import time
import typing

import argon2
from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, HTTPException, status
import jwt

from config import JWT_KEY, JWT_ISS, JWT_AUD, JWT_ALGO, JWT_ALGS, PERMISSIONS_GROUPS
from dependencies import db_connection
from . import services
from . import schemas


router = APIRouter()


@router.post("/users", response_model_exclude_none=True)
def create_user(
    user: schemas.UserInput,
    connection: typing.Annotated[sqlite3.Connection, Depends(db_connection)]
) -> schemas.User:
    try:
        return services.create_user(connection, user.email, user.password, user.first_name, user.last_name)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="A user with that email already exists.")


@router.post("/login")
def login(
    credentials: schemas.Credentials,
    connection: typing.Annotated[sqlite3.Connection, Depends(db_connection)]
) -> schemas.Tokens:
    user = services.find_user(connection, credentials.email)
    if user is None:
        raise HTTPException(status_code=401, detail="Could not log in.")

    hasher = PasswordHasher()
    try:
        hasher.verify(user.password, credentials.password)
    except argon2.exceptions.VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Could not log in.")

    access_token = jwt.encode({
        "iss": JWT_ISS,
        "sub": user.email,
        "aud": JWT_AUD,
        "exp": int(time.time()) + (60 * 5),
        "scope": PERMISSIONS_GROUPS[user.auth_group]
    }, JWT_KEY, algorithm=JWT_ALGO)
    refresh_token = jwt.encode({
        "iss": JWT_ISS,
        "sub": user.email,
        "aud": JWT_AUD,
        "exp": int(time.time()) + (60 * 60),
        "scope": ("refresh " + PERMISSIONS_GROUPS[user.auth_group]).strip()
    }, JWT_KEY, algorithm=JWT_ALGO)
    return schemas.Tokens(
        access=access_token,
        refresh=refresh_token,
    )


@router.post("/refresh")
def refresh(
    refresh: schemas.RefreshToken,
) -> schemas.Tokens:
    try:
        decoded_token = jwt.decode(refresh.refresh, JWT_KEY, audience=JWT_AUD, algorithms=JWT_ALGS)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    new_token = decoded_token.copy()
    scopes = new_token["scope"].split(" ")
    if "refresh" not in scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token does not have 'refresh' scope")
    scopes = [scope for scope in scopes if scope != "refresh"]
    token_scope = " ".join(scopes)
    new_token["scope"] = token_scope
    new_token["exp"] = int(time.time()) + (60 * 5)

    access_token  = jwt.encode(new_token, JWT_KEY, algorithm=JWT_ALGO)
    new_token["exp"] = int(time.time()) + (60 * 60)
    new_token["scope"] = ("refresh " + token_scope).strip()
    refresh_token = jwt.encode(new_token, JWT_KEY, algorithm=JWT_ALGO)
    return schemas.Tokens(
        access=access_token,
        refresh=refresh_token,
    )
