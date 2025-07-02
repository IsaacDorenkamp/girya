import datetime
import sqlite3
import typing

import pytest

import auth.schemas
from api import schemas, services


@pytest.fixture
def lifts(db_connection: sqlite3.Connection) -> list[schemas.Lift]:
    lifts = []
    for i in range(3):
        lift_input = schemas.PartialLift(name=f"Lift {i+1}", slug=f"some-lift-{i+1}")
        lift = services.create_lift(db_connection, lift_input)
        lifts.append(lift)
    db_connection.commit()
    return lifts


@pytest.fixture
def split(db_connection: sqlite3.Connection, lifts: list[schemas.Lift]) -> schemas.Split:
    cursor = db_connection.execute("INSERT INTO split (name, slug) VALUES (:name, :slug)", {
        "name": "Split",
        "slug": "split",
    })
    split_id = typing.cast(int, cursor.lastrowid)
    for lift in lifts:
        db_connection.execute("INSERT INTO split_lift (split_id, lift_id) VALUES (:split_id, :lift_id)", {
            "split_id": split_id,
            "lift_id": lift.id,
        })

    db_connection.commit()
    return schemas.Split(id=split_id, name="Split", slug="split", lifts=lifts)


@pytest.fixture
def workout(db_connection: sqlite3.Connection, split: schemas.Split, simple_user: auth.schemas.User) -> schemas.Workout:
    dt = datetime.datetime(year=2025, month=1, day=1, tzinfo=datetime.timezone.utc)
    db_connection.execute("INSERT INTO workout (at, slug, split_id, user_id) VALUES (?, \"workout-slug\", ?, ?)",
                          (dt, split.id, simple_user.id))
    return schemas.Workout(
        at=dt,
        slug="workout-slug",
        split=split,
        user_id=simple_user.id,
    )
