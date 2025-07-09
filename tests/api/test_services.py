from __future__ import annotations
import sqlite3
import datetime

from fastapi import HTTPException
import pytest

import auth.schemas
from api import services, schemas


@pytest.mark.unit
def test_create_lift(db_connection: sqlite3.Connection):
    test_lift = schemas.PartialLift(name="Some Lift", slug="some-lift")
    lift = services.create_lift(db_connection, test_lift)
    cursor = db_connection.execute("SELECT id FROM lift WHERE id = :lift_id", { "lift_id": lift.id })
    result = cursor.fetchall()
    assert len(result) == 1


@pytest.mark.unit
def test_create_lift_conflict(db_connection: sqlite3.Connection):
    test_lift = schemas.PartialLift(name="Some Lift", slug="some-lift")
    services.create_lift(db_connection, test_lift)
    with pytest.raises(sqlite3.IntegrityError):
        services.create_lift(db_connection, test_lift)


@pytest.mark.unit
def test_delete_lift(db_connection: sqlite3.Connection, lifts: list[schemas.Lift]):
    services.delete_lift_by_slug(db_connection, lifts[0].slug)
    cursor = db_connection.execute("SELECT id FROM lift")
    assert len(cursor.fetchall()) == 2

    with pytest.raises(HTTPException):
        services.delete_lift_by_slug(db_connection, "no-lift-slug")


@pytest.mark.unit
def test_create_split(db_connection: sqlite3.Connection, lifts: list[schemas.Lift]):
    split_input = schemas.SplitInput(name="Test Split", slug="test-split", lifts=[lift.slug for lift in lifts])
    split = services.create_split(db_connection, split_input)

    cursor = db_connection.execute("SELECT * FROM split_lift WHERE split_id = ?", (split.id,))
    split_lifts = cursor.fetchall()
    assert len(split_lifts) == len(lifts)

    cursor = db_connection.execute("SELECT name, slug FROM split WHERE id = ?", (split.id,))
    splits = cursor.fetchall()
    assert len(splits) == 1

    split = splits[0]
    assert split[0] == "Test Split"
    assert split[1] == "test-split"


@pytest.mark.unit
def test_create_split_conflict(db_connection: sqlite3.Connection, lifts: list[schemas.Lift]):
    split_input = schemas.SplitInput(name="Test Split", slug="test-split", lifts=[lift.slug for lift in lifts])
    services.create_split(db_connection, split_input)
    with pytest.raises(sqlite3.IntegrityError):
        services.create_split(db_connection, split_input)


@pytest.mark.usefixtures("lifts")
@pytest.mark.unit
def test_get_lift_by_slug(db_connection: sqlite3.Connection):
    lift = services.get_lift_by_slug(db_connection, "some-lift-1")
    assert lift
    assert lift.name == "Lift 1"

    assert services.get_lift_by_slug(db_connection, "no-lift") is None


@pytest.mark.usefixtures("lifts", "split")
@pytest.mark.unit
def test_get_split_by_slug(db_connection: sqlite3.Connection):
    split = services.get_split_by_slug(db_connection, "split")
    assert split
    assert split.name == "Split"
    assert split.slug == "split"
    assert len(split.lifts) == 3

    for index, lift in enumerate(split.lifts):
        assert lift.name == f"Lift {index+1}"
        assert lift.slug == f"some-lift-{index+1}"

    assert services.get_split_by_slug(db_connection, "no-split") is None


@pytest.mark.usefixtures("split")
@pytest.mark.unit
def test_list_splits(db_connection: sqlite3.Connection):
    splits = services.list_splits(db_connection)
    assert len(splits) == 1
    assert len(splits[0].lifts) == 3

    # test to ensure splits without lifts are included
    services.create_split(db_connection, schemas.SplitInput(name="Split 2", slug="split-2", lifts=[]))
    splits = services.list_splits(db_connection)
    assert len(splits) == 2


@pytest.mark.unit
def test_update_lift_by_slug(db_connection: sqlite3.Connection, lifts: list[schemas.Lift]):
    new_lift = lifts[0].model_copy()
    new_lift.slug = "new-slug"
    new_lift.name = "New Lift"

    lift = services.update_lift_by_slug(db_connection, lifts[0].slug, new_lift)
    assert lift
    assert lift.slug == "new-slug"
    assert lift.name == "New Lift"

    fetched = services.get_lift_by_slug(db_connection, "new-slug")
    assert fetched
    assert fetched.slug == "new-slug"
    assert fetched.name == "New Lift"


@pytest.mark.unit
def test_update_split_by_slug(db_connection: sqlite3.Connection, lifts: list[schemas.Lift], split: schemas.Split):
    new_lift = lifts[0].model_copy()
    new_lift.slug = "new-slug"
    new_lift.name = "New Lift"
    services.create_lift(db_connection, new_lift)

    new_split = schemas.SplitInput(name="New Split", slug="new-split", lifts=["some-lift-1", "new-slug"])
    services.update_split_by_slug(db_connection, split.slug, new_split)

    refetched = services.get_split_by_slug(db_connection, "new-split")
    assert refetched
    assert refetched.name == "New Split"
    assert refetched.slug == "new-split"
    assert len(refetched.lifts) == 2


@pytest.mark.unit
def test_delete_split_by_slug(db_connection: sqlite3.Connection, split: schemas.Split):
    with pytest.raises(HTTPException):
        services.delete_split_by_slug(db_connection, "no-split-slug")

    services.delete_split_by_slug(db_connection, split.slug)


@pytest.mark.usefixtures("split")
@pytest.mark.unit
def test_create_workout(db_connection: sqlite3.Connection, simple_user: auth.schemas.User):
    workout_input = schemas.WorkoutInput(
        at=datetime.datetime(year=2025, month=1, day=1, tzinfo=datetime.timezone.utc),
        split="split",
    )
    workout = services.create_workout(db_connection, workout_input, simple_user.id)
    assert workout.slug == f"20250101-000000-000000-{simple_user.id}"
    assert workout.split.name == "Split"
    assert workout.split.slug == "split"


@pytest.mark.unit
def test_create_workout_missing_split(db_connection: sqlite3.Connection, simple_user: auth.schemas.User):
    workout_input = schemas.WorkoutInput(
        at=datetime.datetime(year=2025, month=1, day=1, tzinfo=datetime.timezone.utc),
        split="split",
    )
    with pytest.raises(HTTPException):
        services.create_workout(db_connection, workout_input, simple_user.id)


@pytest.mark.usefixtures("workout")
@pytest.mark.unit
def test_get_workout(db_connection: sqlite3.Connection, simple_user: auth.schemas.User):
    fetched_workout = services.get_workout_by_slug(db_connection, "workout-slug")
    assert fetched_workout
    assert fetched_workout.slug == "workout-slug"

    assert fetched_workout.split.name == "Split"
    assert fetched_workout.split.slug == "split"

    assert fetched_workout.user_id == simple_user.id

    fetched_workout = services.get_workout_by_slug(db_connection, "no-workout-slug")
    assert fetched_workout is None


@pytest.mark.unit
def test_list_workouts(db_connection: sqlite3.Connection, simple_user: auth.schemas.User,
                       workout: schemas.Workout):
    workouts = services.list_workouts(db_connection, simple_user.id)
    assert len(workouts) == 1
    assert len(workouts[0].split.lifts) == 3

    workouts = services.list_workouts(db_connection, simple_user.id, workout.at)
    assert len(workouts) == 1

    workouts = services.list_workouts(db_connection, simple_user.id, workout.at + datetime.timedelta(days=1))
    assert len(workouts) == 0


@pytest.mark.unit
def test_delete_workout(db_connection: sqlite3.Connection, workout: schemas.Workout):
    services.delete_workout_by_slug(db_connection, workout.slug)
    assert services.get_workout_by_slug(db_connection, workout.slug) is None

    with pytest.raises(HTTPException):
        services.delete_workout_by_slug(db_connection, workout.slug)


@pytest.mark.unit
def test_create_set(db_connection: sqlite3.Connection, lifts: list[schemas.Lift], workout: schemas.Workout,
                    simple_user: auth.schemas.User):
    new_set_input = schemas.SetInput(
        lift=lifts[0].slug,
        workout=workout.slug,
        reps=8,
        weight=160,
        weight_unit=schemas.WeightUnit.lb,
    )

    valid_user_ids = [None, simple_user.id]
    for user_id in valid_user_ids:
        new_set = services.create_set(db_connection, new_set_input, user_id)

        assert new_set.lift.slug == lifts[0].slug
        assert new_set.reps == 8
        assert new_set.weight == 160
        assert new_set.weight_unit == schemas.WeightUnit.lb

    bad_user_id = simple_user.id + 1
    with pytest.raises(HTTPException):
        services.create_set(db_connection, new_set_input, bad_user_id)

    new_set_input.lift = "no-lift-slug"
    with pytest.raises(sqlite3.IntegrityError):
        services.create_set(db_connection, new_set_input)


@pytest.mark.unit
def test_update_set(db_connection: sqlite3.Connection, lift_sets: list[schemas.Set], lifts: list[schemas.Lift],
                    simple_user: auth.schemas.User):
    set_to_update = lift_sets[0]
    set_id = set_to_update.id

    set_update_input = schemas.SetUpdateInput(
        lift=lifts[1].slug,
        reps=10,
        weight=170,
        weight_unit=schemas.WeightUnit.kg,
    )
    updated_set = services.update_set_by_id(db_connection, set_id, set_update_input, simple_user.id)

    assert updated_set.lift.slug == lifts[1].slug
    assert updated_set.reps == 10
    assert updated_set.weight == 170
    assert updated_set.weight_unit == schemas.WeightUnit.kg

    set_update_input.lift = "no-lift-slug"
    with pytest.raises(sqlite3.IntegrityError):
        services.update_set_by_id(db_connection, set_id, set_update_input, simple_user.id)

    bad_user_id = simple_user.id + 1
    with pytest.raises(HTTPException):
        services.update_set_by_id(db_connection, set_id, set_update_input, bad_user_id)


@pytest.mark.unit
def test_get_set(db_connection: sqlite3.Connection, lift_sets: list[schemas.Set], lifts: list[schemas.Lift],
                 simple_user: auth.schemas.User):
    valid_user_ids = [simple_user.id, None]
    for user_id in valid_user_ids:
        fetched_set = services.get_set_by_id(db_connection, lift_sets[0].id, user_id)
        assert fetched_set
        assert fetched_set.lift.slug == lifts[0].slug
        assert fetched_set.reps == 8
        assert fetched_set.weight == 160
        assert fetched_set.weight_unit == schemas.WeightUnit.lb

    # non-existent set id
    assert services.get_set_by_id(db_connection, 1000) is None
    # existing set, incorrect user id
    bad_user_id = simple_user.id + 1
    assert services.get_set_by_id(db_connection, lift_sets[0].id, bad_user_id) is None


@pytest.mark.usefixtures("lift_sets", "workout")
@pytest.mark.unit
def test_list_sets(db_connection: sqlite3.Connection, simple_user: auth.schemas.User):
    valid_user_ids = [simple_user.id, None]
    for user_id in valid_user_ids:
        sets = services.list_sets_by_workout(db_connection, "workout-slug", user_id)
        assert len(sets) == 3

    with pytest.raises(HTTPException):
        services.list_sets_by_workout(db_connection, "workout-slug", simple_user.id + 1)


@pytest.mark.unit
def test_delete_set(db_connection: sqlite3.Connection, lift_sets: list[schemas.Set]):
    # try to remove non-existent set
    bad_id = lift_sets[-1].id + 1
    with pytest.raises(HTTPException):
        services.delete_set_by_id(db_connection, bad_id)

    # remove existing set
    result = db_connection.execute("SELECT * FROM lift_set WHERE id = ?", (lift_sets[0].id,))
    assert len(result.fetchall()) == 1

    services.delete_set_by_id(db_connection, lift_sets[0].id)

    result = db_connection.execute("SELECT * FROM lift_set WHERE id = ?", (lift_sets[0].id,))
    assert len(result.fetchall()) == 0


@pytest.mark.unit
def test_delete_set_user_id(db_connection: sqlite3.Connection, lift_sets: list[schemas.Set], simple_user: auth.schemas.User):
    # try to remove an existing set, but specify the wrong user
    bad_user_id = simple_user.id + 1
    with pytest.raises(HTTPException):
        services.delete_set_by_id(db_connection, lift_sets[0].id, bad_user_id)

    # remove existing set with correct user
    result = db_connection.execute("SELECT * FROM lift_set WHERE id = ?", (lift_sets[0].id,))
    assert len(result.fetchall()) == 1

    services.delete_set_by_id(db_connection, lift_sets[0].id, simple_user.id)

    result = db_connection.execute("SELECT * FROM lift_set WHERE id = ?", (lift_sets[0].id,))
    assert len(result.fetchall()) == 0

    # ensure delete does not delete more than it should
    all_sets = db_connection.execute("SELECT * from lift_set")
    assert len(all_sets.fetchall()) == 2

