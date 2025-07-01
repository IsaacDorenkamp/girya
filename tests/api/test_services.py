from __future__ import annotations
import sqlite3
import typing
import pytest

from api import services, schemas


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


@pytest.mark.usefixtures("lifts")
@pytest.mark.unit
def test_update_lift_by_slug(db_connection: sqlite3.Connection, lifts: list[schemas.Lift]):
    new_lift = lifts[0].model_copy()
    new_lift.slug = "new-slug"
    new_lift.name = "New Lift"

    print("base slug:", lifts[0].slug)

    lift = services.update_lift_by_slug(db_connection, lifts[0].slug, new_lift)
    assert lift
    assert lift.slug == "new-slug"
    assert lift.name == "New Lift"

    fetched = services.get_lift_by_slug(db_connection, "new-slug")
    assert fetched
    assert fetched.slug == "new-slug"
    assert fetched.name == "New Lift"

