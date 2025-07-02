import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Security, HTTPException, status

from dependencies import db_connection, get_user

import auth.schemas
from . import schemas, services


router = APIRouter()


@router.post("/lifts", status_code=201)
def create_lift(
    lift_input: schemas.PartialLift,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    _: Annotated[auth.schemas.User, Security(get_user, scopes=["write:lift"])]
) -> schemas.Lift:
    return services.create_lift(connection, lift_input)


@router.get("/lifts/{slug}")
def get_lift(
    slug: str,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    _: Annotated[auth.schemas.User, Security(get_user, scopes=["read:lift"])],
) -> schemas.Lift:
    lift = services.get_lift_by_slug(connection, slug)
    if lift is not None:
        return lift
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Lift '{slug}' not found.")


@router.put("/lifts/{slug}")
def put_lift(
    slug: str,
    lift_input: schemas.PartialLift,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    _: Annotated[auth.schemas.User, Security(get_user, scopes=["write:lift"])]
) -> schemas.Lift:
    updated_lift = services.update_lift_by_slug(connection, slug, lift_input)
    if updated_lift is not None:
        return updated_lift
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Lift '{slug}' not found.")

@router.post("/splits", status_code=201)
def create_split(
    split_input: schemas.SplitInput,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    _: Annotated[auth.schemas.User, Security(get_user, scopes=["write:split"])]
):
    return services.create_split(connection, split_input)


@router.put("/splits/{slug}")
def update_split(
    slug: str,
    split_input: schemas.SplitInput,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    _: Annotated[auth.schemas.User, Security(get_user, scopes=["write:split"])]
):
    return services.update_split_by_slug(connection, slug, split_input)


@router.get("/splits/{slug}")
def get_split(
    slug: str,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    _: Annotated[auth.schemas.User, Security(get_user, scopes=["read:split"])]
):
    return services.get_split_by_slug(connection, slug)
