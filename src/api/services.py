import sqlite3
from typing import cast

from fastapi import HTTPException

from . import schemas


def create_lift(connection: sqlite3.Connection, lift: schemas.PartialLift) -> schemas.Lift:
    cursor = connection.execute("INSERT INTO lift (name, slug) VALUES (:name, :slug)", lift.model_dump())
    return schemas.Lift(**lift.model_dump(exclude={"id"}), id=cast(int, cursor.lastrowid))


def create_split(connection: sqlite3.Connection, split: schemas.SplitInput) -> schemas.Split:
    interpolations = "(" + ", ".join(["?" for _ in range(len(split.lifts))]) + ")"
    cursor = connection.execute("SELECT id, name, slug FROM lift WHERE slug IN %s" % interpolations, split.lifts)
    results = cursor.fetchall()
    if len(results) != len(split.lifts):
        found = [item[2] for item in results]
        missing = [lift for lift in split.lifts if lift not in found]
        raise HTTPException(status_code=404, detail="Could not find the following lifts: %s" % ", ".join(missing))

    lifts = [schemas.Lift(id=item[0], name=item[1], slug=item[2]) for item in results]

    cursor = connection.execute("INSERT INTO split (name, slug) VALUES (:name, :slug)", { "name": split.name, "slug": split.slug, })
    split_id = cast(int, cursor.lastrowid)
    new_split = schemas.Split(name=split.name, slug=split.slug, id=split_id, lifts=lifts)

    # create associations
    for lift in lifts:
        connection.execute("INSERT INTO split_lift (split_id, lift_id) VALUES (:split_id, :lift_id)", { "split_id": split_id, "lift_id": lift.id })

    return new_split


def get_lift_by_slug(connection: sqlite3.Connection, slug: str) -> schemas.Lift | None:
    cursor = connection.execute("SELECT id, name, slug FROM lift WHERE slug = ?", (slug,))
    lift_data = cursor.fetchone()
    if lift_data is None:
        return None

    return schemas.Lift(id=lift_data[0], name=lift_data[1], slug=lift_data[2])


def get_split_by_slug(connection: sqlite3.Connection, slug: str) -> schemas.Split | None:
    cursor = connection.execute("SELECT id, name, slug FROM split WHERE slug = :slug", { "slug": slug })
    split_data = cursor.fetchone()
    if split_data is None:
        return None

    split = schemas.Split(id=split_data[0], name=split_data[1], slug=split_data[2], lifts=[])
    cursor = connection.execute("""SELECT lift.id, lift.name, lift.slug FROM lift
INNER JOIN split_lift ON lift.id = split_lift.lift_id WHERE split_lift.split_id = :split_id
ORDER BY lift.id ASC""", { "split_id": split.id })
    lifts = cursor.fetchall()
    for lift_data in lifts:
        lift = schemas.Lift(id=lift_data[0], name=lift_data[1], slug=lift_data[2])
        split.lifts.append(lift)

    return split


def update_lift_by_slug(connection: sqlite3.Connection, slug: str, lift: schemas.PartialLift) -> schemas.Lift | None:
    cursor = connection.execute("UPDATE lift SET name = :name, slug = :new_slug WHERE slug = :slug RETURNING lift.id", {
        "name": lift.name,
        "slug": slug,
        "new_slug": lift.slug,
    })
    result = cursor.fetchone()
    if result is None:
        return None

    return schemas.Lift(**lift.model_dump(exclude={"id"}), id=result[0])


def update_split_by_slug(connection: sqlite3.Connection, slug: str, split: schemas.SplitInput) -> schemas.Split | None:
    cursor = connection.execute("UPDATE split SET name = :name, slug = :new_slug WHERE slug = :slug RETURNING split.id", {
        "name": split.name,
        "slug": slug,
        "new_slug": split.slug,
    })
    result = cursor.fetchone()
    if result is None:
        return None

    split_id = result[0]

    # update lifts
    interpolations = "(" + ", ".join(["?" for _ in range(len(split.lifts))]) + ")"
    cursor = connection.execute("SELECT id, name, slug FROM lift WHERE slug in %s" % interpolations, split.lifts)
    lifts = cursor.fetchall()

    connection.execute("DELETE FROM split_lift WHERE lift_id NOT IN %s" % interpolations, split.lifts)

    interpolations = ", ".join(["(?, ?)" for _ in range(len(split.lifts))])
    values = []
    lift_models = []
    for lift in lifts:
        values.extend([split_id, lift[0]])
        lift_models.append(schemas.Lift(id=lift[0], name=lift[1], slug=lift[2]))
    connection.execute("INSERT INTO split_lift (split_id, lift_id) VALUES %s" % interpolations, values)

    return schemas.Split(
        id=split_id,
        name=split.name,
        slug=split.slug,
        lifts=lift_models,
    )
