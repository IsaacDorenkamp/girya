import datetime
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
    try:
        return services.create_lift(connection, lift_input)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Lift '{lift_input.slug}' already exists.")


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


@router.delete("/lifts/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lift(
    slug: str,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    _: Annotated[auth.schemas.User, Security(get_user, scopes=["delete:lift"])]
):
    services.delete_lift_by_slug(connection, slug)


@router.post("/splits", status_code=201)
def create_split(
    split_input: schemas.SplitInput,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    _: Annotated[auth.schemas.User, Security(get_user, scopes=["write:split"])]
) -> schemas.Split:
    try:
        return services.create_split(connection, split_input)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Split '{split_input.slug}' already exists.")


@router.put("/splits/{slug}")
def update_split(
    slug: str,
    split_input: schemas.SplitInput,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    _: Annotated[auth.schemas.User, Security(get_user, scopes=["write:split"])]
) -> schemas.Split:
    result = services.update_split_by_slug(connection, slug, split_input)
    if result is not None:
        return result
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No split '{slug}'")


@router.delete("/splits/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_split(
    slug: str,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    _: Annotated[auth.schemas.User, Security(get_user, scopes=["delete:split"])]
):
    services.delete_split_by_slug(connection, slug)


@router.get("/splits/{slug}")
def get_split(
    slug: str,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    _: Annotated[auth.schemas.User, Security(get_user, scopes=["read:split"])]
) -> schemas.Split:
    result = services.get_split_by_slug(connection, slug)
    if result is not None:
        return result
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No split '{slug}'")


@router.post("/workouts", response_model_exclude={"user_id"}, status_code=201)
def post_workout(
    workout_input: schemas.WorkoutInput,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    user: Annotated[auth.schemas.User, Security(get_user, scopes=["write:workout"])]
) -> schemas.Workout:
    try:
        return services.create_workout(connection, workout_input, user.id)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Workout with date '{workout_input.at}' already exists")


@router.get("/workouts/{slug}", response_model_exclude={"user_id"})
def get_workout(
    slug: str,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    user: Annotated[auth.schemas.User, Security(get_user, scopes=["read:workout"])],
) -> schemas.Workout:
    workout = services.get_workout_by_slug(connection, slug)
    if workout is not None and workout.user_id == user.id:
        return workout
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No workout '{slug}'")


@router.get("/workouts/{slug}/sets")
def get_workout_sets(
    slug: str,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    user: Annotated[auth.schemas.User, Security(get_user, scopes=["read:set"])],
) -> list[schemas.Set]:
    sets = services.list_sets_by_workout(connection, slug, user.id)
    return sets


@router.get("/workouts", response_model_exclude={"user_id"})
def list_workouts(
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    user: Annotated[auth.schemas.User, Security(get_user, scopes=["read:workout"])],
    at: datetime.datetime | None = None,
) -> list[schemas.Workout]:
    return services.list_workouts(connection, user.id, at)


@router.delete("/workouts/{slug}", status_code=204)
def delete_workout(
    slug: str,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    user: Annotated[auth.schemas.User, Security(get_user, scopes=["delete:workout"])],
):
    services.delete_workout_by_slug(connection, slug, user.id)


@router.post("/sets", status_code=status.HTTP_201_CREATED)
def create_set(
    set_input: schemas.SetInput,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    user: Annotated[auth.schemas.User, Security(get_user, scopes=["write:set"])],
) -> schemas.Set:
    try:
        return services.create_set(connection, set_input, user.id)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No lift '{set_input.lift}'")


@router.put("/sets/{set_id}")
def update_set(
    set_id: int,
    set_update_input: schemas.SetUpdateInput,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    user: Annotated[auth.schemas.User, Security(get_user, scopes=["write:set"])],
) -> schemas.Set:
    try:
        return services.update_set_by_id(connection, set_id, set_update_input, user.id)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No lift '{set_update_input.lift}'")


@router.get("/sets/{set_id}")
def get_set(
    set_id: int,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    user: Annotated[auth.schemas.User, Security(get_user, scopes=["read:set"])],
) -> schemas.Set:
    lift_set = services.get_set_by_id(connection, set_id, user.id)
    if lift_set is not None:
        return lift_set
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No set '{set_id}'")


@router.delete("/sets/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_set(
    set_id: int,
    connection: Annotated[sqlite3.Connection, Depends(db_connection)],
    user: Annotated[auth.schemas.User, Security(get_user, scopes=["delete:set"])],
):
    services.delete_set_by_id(connection, set_id, user.id)

