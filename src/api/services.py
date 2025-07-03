import sqlite3
from typing import cast

from fastapi import HTTPException, status

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


def build_split(connection: sqlite3.Connection, data: tuple):
    split = schemas.Split(id=data[0], name=data[1], slug=data[2], lifts=[])
    cursor = connection.execute("""SELECT lift.id, lift.name, lift.slug FROM lift
INNER JOIN split_lift ON lift.id = split_lift.lift_id WHERE split_lift.split_id = :split_id
ORDER BY lift.id ASC""", { "split_id": split.id })
    lifts = cursor.fetchall()
    for lift_data in lifts:
        lift = schemas.Lift(id=lift_data[0], name=lift_data[1], slug=lift_data[2])
        split.lifts.append(lift)

    return split


def get_split_by_slug(connection: sqlite3.Connection, slug: str) -> schemas.Split | None:
    cursor = connection.execute("SELECT id, name, slug FROM split WHERE slug = :slug", { "slug": slug })
    split_data = cursor.fetchone()
    if split_data is None:
        return None

    return build_split(connection, split_data)


def get_split_by_id(connection: sqlite3.Connection, id: int) -> schemas.Split | None:
    cursor = connection.execute("SELECT id, name, slug FROM split WHERE id = :id", { "id": id })
    split_data = cursor.fetchone()
    if split_data is None:
        return None

    return build_split(connection, split_data)


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


def create_workout(connection: sqlite3.Connection, workout_input: schemas.WorkoutInput, user_id: int) -> schemas.Workout:
    split = get_split_by_slug(connection, workout_input.split)
    if split is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No split '{workout_input.split}'")

    workout = schemas.Workout(**workout_input.model_dump(exclude={"split"}), user_id=user_id, split=split)
    connection.execute("INSERT INTO workout (at, slug, split_id, user_id) VALUES (:at, :slug, :split_id, :user_id)", {
        "at": workout.at,
        "slug": workout.slug,
        "split_id": workout.split.id,
        "user_id": workout.user_id,
    })
    return workout


def get_workout_by_slug(connection: sqlite3.Connection, slug: str):
    cursor = connection.execute("SELECT at, slug, split_id, user_id FROM workout WHERE slug = ?", (slug,))
    result = cursor.fetchone()
    if result is None:
        return None

    split = get_split_by_id(connection, result[2])
    if split is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No split with id '{result[2]}'")

    return schemas.Workout(
        at=result[0],
        slug=result[1],
        split=split,
        user_id=result[3],
    )


def delete_workout_by_slug(connection: sqlite3.Connection, slug: str, user_id: int | None = None):
    data: dict[str, str | int] = { "slug": slug }
    if user_id is not None:
        query = "DELETE FROM workout WHERE slug = :slug AND user_id = :user_id"
        data["user_id"] = user_id
    else:
        query = "DELETE FROM workout WHERE slug = :slug"

    cursor = connection.execute(query, data)
    connection.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workout '{slug}' not found")


def create_set(connection: sqlite3.Connection, set_input: schemas.SetInput, user_id: int | None = None) -> schemas.Set:
    data = {
        "lift_slug": set_input.lift,
        "workout_slug": set_input.workout,
        "reps": set_input.reps,
        "weight": set_input.weight,
        "weight_unit": set_input.weight_unit,
    }
    if user_id is not None:
        data["user_id"] = user_id
        query = """INSERT INTO lift_set (lift_slug, workout_slug, reps, weight, weight_unit)
SELECT set_data.* FROM (VALUES (:lift_slug, :workout_slug, :reps, :weight, :weight_unit)) as set_data
INNER JOIN workout ON workout.slug = :workout_slug
WHERE workout.user_id = :user_id
"""
    else:
        query = """INSERT INTO lift_set (lift_slug, workout_slug, reps, weight, weight_unit) VALUES
(:lift_slug, :workout_slug, :reps, :weight, :weight_unit)"""
    cursor = connection.execute(query, data)
    connection.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No workout '{set_input.workout}'")

    lift = get_lift_by_slug(connection, set_input.lift)
    set_id = cast(int, cursor.lastrowid)
    return schemas.Set(
        lift=cast(schemas.Lift, lift),
        reps=set_input.reps,
        weight=set_input.weight,
        weight_unit=set_input.weight_unit,
        id=set_id,
    )


def update_set_by_id(connection: sqlite3.Connection, set_id: int, set_input: schemas.SetUpdateInput, user_id: int) -> schemas.Set:
    cursor = connection.execute("""UPDATE lift_set SET lift_slug = :lift_slug, reps = :reps, weight = :weight, weight_unit = :weight_unit
    WHERE id IN (
        SELECT lift_set.id FROM lift_set
        INNER JOIN workout ON lift_set.workout_slug = workout.slug
        WHERE lift_set.id = :set_id AND workout.user_id = :user_id
    )""", {
        "lift_slug": set_input.lift,
        "reps": set_input.reps,
        "weight": set_input.weight,
        "weight_unit": set_input.weight_unit,
        "set_id": set_id,
        "user_id": user_id,
    })
    connection.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No set '{set_id}'")

    # If we've reached here, we can know that the lift exists. Otherwise, an integrity error would have occurred.
    lift = get_lift_by_slug(connection, set_input.lift)
    return schemas.Set(
        lift=cast(schemas.Lift, lift),
        reps=set_input.reps,
        weight=set_input.weight,
        weight_unit=set_input.weight_unit,
        id=set_id,
    )


def get_set_by_id(connection: sqlite3.Connection, set_id: int, user_id: int | None = None) -> schemas.Set | None:
    data = { "set_id": set_id }
    if user_id is not None:
        data["user_id"] = user_id
        query = """SELECT a.lift_slug, a.reps, a.weight, a.weight_unit FROM lift_set a
INNER JOIN workout ON a.workout_slug = workout.slug
WHERE a.id = :set_id AND workout.user_id = :user_id
"""
    else:
        query = "SELECT lift_slug, reps, weight, weight_unit FROM lift_set WHERE id = :set_id"

    cursor = connection.execute(query, data)
    set_data = cursor.fetchone()
    if set_data is None:
        return None

    lift = get_lift_by_slug(connection, set_data[0])
    return schemas.Set(
        lift=cast(schemas.Lift, lift),
        reps=set_data[1],
        weight=set_data[2],
        weight_unit=set_data[3],
        id=set_id,
    )


def delete_set_by_id(connection: sqlite3.Connection, set_id: int, user_id: int | None = None):
    data = { "set_id": set_id }
    if user_id is not None:
        data["user_id"] = user_id
        query = """DELETE FROM lift_set WHERE id in (
    SELECT lift_set.id FROM lift_set INNER JOIN workout ON lift_set.workout_slug = workout.slug WHERE workout.user_id = :user_id AND
    lift_set.id = :set_id
)"""
    else:
        query = "DELETE FROM lift_set WHERE id = :set_id"

    cursor = connection.execute(query, data)
    connection.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No set '{set_id}'")

