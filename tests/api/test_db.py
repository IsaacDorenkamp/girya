from __future__ import annotations
import typing

import pytest

from api.schemas import Lift, Workout, Set, WeightUnit


@pytest.fixture
def sets(db_connection: sqlite3.Connection, lifts: list[Lift], workout: Workout) -> list[Set]:
    result = db_connection.execute(f"""
INSERT INTO lift_set (lift_slug, workout_slug, reps, weight, weight_unit) VALUES
    ("{lifts[0].slug}", "{workout.slug}", 8, 160, "lb"),
    ("{lifts[0].slug}", "{workout.slug}", 7, 160, "lb"),
    ("{lifts[0].slug}", "{workout.slug}", 6, 160, "lb") RETURNING id;
""")
    ids = result.fetchall()
    return [
        Set(lift=lifts[0], reps=8, weight=160, weight_unit=WeightUnit.lb, id=ids[0][0]),
        Set(lift=lifts[0], reps=7, weight=160, weight_unit=WeightUnit.lb, id=ids[1][0]),
        Set(lift=lifts[0], reps=6, weight=160, weight_unit=WeightUnit.lb, id=ids[2][0]),
    ]


@pytest.mark.unit
def test_delete_workout_cascade_to_set(db_connection: sqlite3.Connection, sets: list[Set], workout: Workout):
    db_connection.execute("DELETE FROM workout WHERE slug = :slug", { "slug": workout.slug })
    result = db_connection.execute("SELECT id FROM lift_set WHERE workout_slug = :slug", { "slug": workout.slug })
    sets = result.fetchall()
    assert len(sets) == 0


if typing.TYPE_CHECKING:
    import sqlite3

