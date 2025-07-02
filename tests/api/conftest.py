import sqlite3
import typing

import pytest

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


