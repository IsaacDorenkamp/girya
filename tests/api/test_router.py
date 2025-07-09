from __future__ import annotations
import datetime
import typing

import pytest

from api import schemas


@pytest.mark.integration
def test_create_lift(test_client: TestClient, admin_access_token: str):
    response = test_client.post("/api/lifts", json={
        "name": "Lift",
        "slug": "lift",
    }, headers={ "Authorization": f"Bearer {admin_access_token}" })

    assert response.status_code == 201
    
    lift = response.json()
    assert lift["name"] == "Lift"
    assert lift["slug"] == "lift"
    assert "id" in lift


@pytest.mark.integration
def test_create_lift_forbidden(test_client: TestClient, simple_access_token: str):
    response = test_client.post("/api/lifts", json={
        "name": "Lift",
        "slug": "lift",
    }, headers={ "Authorization": f"Bearer {simple_access_token}" })

    assert response.status_code == 403


@pytest.mark.usefixtures("lifts")
@pytest.mark.integration
def test_get_lift(test_client: TestClient, simple_access_token: str):
    response = test_client.get("/api/lifts/some-lift-1", headers={
        "Authorization": f"Bearer {simple_access_token}",
    })

    assert response.status_code == 200
    
    lift = response.json()
    assert lift["name"] == "Lift 1"
    assert lift["slug"] == "some-lift-1"
    assert "id" in lift


@pytest.mark.integration
def test_get_lift_unauthorized(test_client: TestClient):
    response = test_client.get("/api/lifts/some-lift-1")
    assert response.status_code == 401


@pytest.mark.usefixtures("lifts")
@pytest.mark.integration
def test_put_lift(test_client: TestClient, admin_access_token: str):
    response = test_client.put("/api/lifts/some-lift-1", json={
        "name": "New Lift",
        "slug": "new-lift"
    }, headers={
        "Authorization": f"Bearer {admin_access_token}",
    })

    assert response.status_code == 200
    lift = response.json()
    assert lift["name"] == "New Lift"
    assert lift["slug"] == "new-lift"
    assert "id" in lift


@pytest.mark.usefixtures("lifts")
@pytest.mark.integration
def test_put_lift_forbidden(test_client: TestClient, simple_access_token: str):
    response = test_client.put("/api/lifts/some-lift-1", json={
        "name": "New Lift",
        "slug": "new-lift",
    }, headers={
        "Authorization": f"Bearer {simple_access_token}"
    })
    assert response.status_code == 403


@pytest.mark.usefixtures("lifts")
@pytest.mark.integration
def test_delete_lift(test_client: TestClient, admin_access_token: str):
    response = test_client.delete("/api/lifts/some-lift-1", headers={
        "Authorization": f"Bearer {admin_access_token}"
    })
    assert response.status_code == 204


@pytest.mark.usefixtures("lifts")
@pytest.mark.integration
def test_delete_lift_forbidden(test_client: TestClient, simple_access_token: str):
    response = test_client.delete("/api/lifts/some-lift-1", headers={
        "Authorization": f"Bearer {simple_access_token}"
    })
    assert response.status_code == 403


@pytest.mark.usefixtures("lifts")
@pytest.mark.integration
def test_create_split(test_client: TestClient, admin_access_token: str):
    response = test_client.post("/api/splits", json={
        "name": "Split",
        "slug": "split",
        "lifts": ["some-lift-1"],
    }, headers={ "Authorization": f"Bearer {admin_access_token}" })
    assert response.status_code == 201


@pytest.mark.usefixtures("lifts")
@pytest.mark.integration
def test_create_split_forbidden(test_client: TestClient, simple_access_token: str):
    response = test_client.post("/api/splits", json={
        "name": "Split",
        "slug": "split",
        "lifts": ["some-lift-1"],
    }, headers={ "Authorization": f"Bearer {simple_access_token}" })
    assert response.status_code == 403


@pytest.mark.usefixtures("split")
@pytest.mark.integration
def test_update_split(test_client: TestClient, admin_access_token: str):
    response = test_client.put("/api/splits/split", json={
        "name": "New Split",
        "slug": "new-split",
        "lifts": ["some-lift-1"]
    }, headers={ "Authorization": f"Bearer {admin_access_token}" })
    assert response.status_code == 200

    split = response.json()
    assert split["name"] == "New Split"
    assert split["slug"] == "new-split"
    assert len(split["lifts"]) == 1
    
    lift = split["lifts"][0]
    assert lift["name"] == "Lift 1"


@pytest.mark.usefixtures("split")
@pytest.mark.integration
def test_update_split_forbidden(test_client: TestClient, simple_access_token: str):
    response = test_client.put("/api/splits/split", json={
        "name": "New Split",
        "slug": "new-split",
        "lifts": ["some-lift-1"]
    }, headers={ "Authorization": f"Bearer {simple_access_token}" })
    assert response.status_code == 403


@pytest.mark.usefixtures("split")
@pytest.mark.integration
def test_delete_split(test_client: TestClient, admin_access_token: str):
    response = test_client.delete("/api/splits/split", headers={
        "Authorization": f"Bearer {admin_access_token}",
    })
    assert response.status_code == 204


@pytest.mark.usefixtures("split")
@pytest.mark.integration
def test_delete_split_forbidden(test_client: TestClient, simple_access_token: str):
    response = test_client.delete("/api/splits/split", headers={
        "Authorization": f"Bearer {simple_access_token}",
    })
    assert response.status_code == 403


@pytest.mark.usefixtures("split")
@pytest.mark.integration
def test_get_split(test_client: TestClient, simple_access_token: str):
    response = test_client.get("/api/splits/split", headers={
        "Authorization": f"Bearer {simple_access_token}",
    })
    assert response.status_code == 200

    split = response.json()
    assert split["name"] == "Split"
    assert split["slug"] == "split"


@pytest.mark.usefixtures("split")
@pytest.mark.integration
def test_get_split_unauthorized(test_client: TestClient):
    response = test_client.get("/api/splits/split")
    assert response.status_code == 401


@pytest.mark.usefixtures("split")
@pytest.mark.integration
def test_list_splits(test_client: TestClient, simple_access_token: str):
    response = test_client.get("/api/splits", headers={
        "Authorization": f"Bearer {simple_access_token}",
    })
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.usefixtures("split")
@pytest.mark.integration
def test_list_splits_unauthorized(test_client: TestClient):
    response = test_client.get("/api/splits")
    assert response.status_code == 401


@pytest.mark.usefixtures("split")
@pytest.mark.integration
def test_create_workout(test_client: TestClient, simple_access_token: str):
    response = test_client.post("/api/workouts", json={
        "at": "2025-01-01T00:00:00",
        "split": "split"
    }, headers={
        "Authorization": f"Bearer {simple_access_token}",
    })
    assert response.status_code == 201

    workout = response.json()
    assert workout["at"]


@pytest.mark.usefixtures("split")
@pytest.mark.integration
def test_create_workout_unauthorized(test_client: TestClient):
    response = test_client.post("/api/workouts", json={
        "at": "2025-01-01T00:00:00",
        "split": "split"
    })
    assert response.status_code == 401



@pytest.mark.usefixtures("split", "workout")
@pytest.mark.integration
def test_get_workout(test_client: TestClient, simple_access_token: str):
    response = test_client.get("/api/workouts/workout-slug", headers={
        "Authorization": f"Bearer {simple_access_token}"
    })
    assert response.status_code == 200
    
    workout = response.json()
    assert (
        datetime.datetime.fromisoformat(workout["at"]) == 
        datetime.datetime(year=2025, month=1, day=1, tzinfo=datetime.timezone.utc)
    )


@pytest.mark.usefixtures("split", "workout")
@pytest.mark.integration
def test_get_workout_unauthorized(test_client: TestClient):
    response = test_client.get("/api/workouts/workout-slug")
    assert response.status_code == 401


@pytest.mark.usefixtures("split")
@pytest.mark.integration
def test_list_workouts(test_client: TestClient, simple_access_token: str, workout: schemas.Workout):
    response = test_client.get("/api/workouts", headers={
        "Authorization": f"Bearer {simple_access_token}",
    })
    assert response.status_code == 200

    workouts = response.json()
    assert len(workouts) == 1
    assert workouts[0]["slug"] == "workout-slug"
    assert len(workouts[0]["split"]["lifts"]) == 3

    response = test_client.get("/api/workouts", params={
        "at": workout.at.isoformat()
    }, headers={
        "Authorization": f"Bearer {simple_access_token}"
    })
    assert response.status_code == 200

    workouts = response.json()
    assert len(workouts) == 1

    response = test_client.get("/api/workouts", params={
        "at": (workout.at + datetime.timedelta(days=1)).isoformat(),
    }, headers={
        "Authorization": f"Bearer {simple_access_token}"
    })
    assert response.status_code == 200

    workouts = response.json()
    assert len(workouts) == 0


@pytest.mark.usefixtures("workout", "lift_sets")
@pytest.mark.integration
def test_list_workout_sets(test_client: TestClient, simple_access_token: str):
    response = test_client.get("/api/workouts/workout-slug/sets", headers={
        "Authorization": f"Bearer {simple_access_token}",
    })
    assert response.status_code == 200

    sets = response.json()
    assert len(sets) == 3


@pytest.mark.usefixtures("workout", "lift_sets")
@pytest.mark.unit
def test_list_workout_sets_not_found(test_client: TestClient, admin_access_token: str):
    # incorrect user
    response = test_client.get("/api/workouts/workout-slug/sets", headers={
        "Authorization": f"Bearer {admin_access_token}",
    })
    assert response.status_code == 404


@pytest.mark.usefixtures("split", "workout")
@pytest.mark.integration
def test_delete_workout(test_client: TestClient, simple_access_token: str):
    response = test_client.delete("/api/workouts/workout-slug", headers={
        "Authorization": f"Bearer {simple_access_token}"
    })
    assert response.status_code == 204

    response = test_client.delete("/api/workouts/workout-slug", headers={
        "Authorization": f"Bearer {simple_access_token}"
    })
    assert response.status_code == 404


@pytest.mark.usefixtures("split", "workout")
@pytest.mark.integration
def test_delete_workout_unauthorized(test_client: TestClient):
    response = test_client.delete("/api/workouts/workout-slug")
    assert response.status_code == 401


@pytest.mark.integration
def test_create_set(test_client: TestClient, lifts: list[schemas.Lift], workout: schemas.Workout,
                    simple_access_token: str):
    response = test_client.post("/api/sets", json={
        "lift": lifts[0].slug,
        "workout": workout.slug,
        "reps": 8,
        "weight": 160,
        "weight_unit": schemas.WeightUnit.lb,
    }, headers={ "Authorization": f"Bearer {simple_access_token}" })
    assert response.status_code == 201

    lift_set = response.json()
    assert lift_set["lift"]["slug"] == lifts[0].slug
    assert lift_set["reps"] == 8
    assert lift_set["weight"] == 160
    assert lift_set["weight_unit"] == schemas.WeightUnit.lb


@pytest.mark.integration
def test_create_set_workout_not_found(test_client: TestClient, lifts: list[schemas.Lift],
                                      workout: schemas.Workout, admin_access_token: str):
    # The admin_access_token refers to a user who does not own the provided workout, which
    # should incur a 404 (since the workout cannot be found for the authorized user)
    response = test_client.post("/api/sets", json={
        "lift": lifts[0].slug,
        "workout": workout.slug,
        "reps": 8,
        "weight": 160,
        "weight_unit": schemas.WeightUnit.lb,
    }, headers={ "Authorization": f"Bearer {admin_access_token}" })
    assert response.status_code == 404


@pytest.mark.integration
def test_update_set(test_client: TestClient, lifts: list[schemas.Lift], lift_sets: list[schemas.Set], workout: schemas.Workout,
                    simple_access_token: str):
    response = test_client.put(f"/api/sets/{lift_sets[0].id}", json={
        "lift": lifts[1].slug,
        "workout": workout.slug,
        "reps": 8,
        "weight": 160,
        "weight_unit": schemas.WeightUnit.lb,
    }, headers={ "Authorization": f"Bearer {simple_access_token}" })
    assert response.status_code == 200

    lift_set = response.json()
    assert lift_set["lift"]["slug"] == lifts[1].slug
    assert lift_set["reps"] == 8
    assert lift_set["weight"] == 160
    assert lift_set["weight_unit"] == schemas.WeightUnit.lb


@pytest.mark.integration
def test_update_set_not_found(test_client: TestClient, lifts: list[schemas.Lift], lift_sets: list[schemas.Set], workout: schemas.Workout,
                              admin_access_token: str):
    # invalid user
    response = test_client.put(f"/api/sets/{lift_sets[0].id}", json={
        "lift": lifts[1].slug,
        "workout": workout.slug,
        "reps": 8,
        "weight": 160,
        "weight_unit": schemas.WeightUnit.lb,
    }, headers={ "Authorization": f"Bearer {admin_access_token}" })
    assert response.status_code == 404


@pytest.mark.integration
def test_get_set(test_client: TestClient, lift_sets: list[schemas.Set], simple_access_token: str):
    response = test_client.get(f"/api/sets/{lift_sets[0].id}",
                               headers={ "Authorization": f"Bearer {simple_access_token}" })
    assert response.status_code == 200

    lift_set = response.json()
    assert lift_set["lift"]["slug"] == lift_sets[0].lift.slug
    assert lift_set["reps"] == 8
    assert lift_set["weight"] == 160
    assert lift_set["weight_unit"] == schemas.WeightUnit.lb


@pytest.mark.integration
def test_get_set_not_found(test_client: TestClient, lift_sets: list[schemas.Set], simple_access_token: str, admin_access_token: str):
    # non-existent set
    response = test_client.get(f"/api/sets/{lift_sets[-1].id + 1}",
                               headers={ "Authorization": f"Bearer {simple_access_token}" })
    assert response.status_code == 404

    # existing set, incorrect user
    response = test_client.get(f"/api/sets/{lift_sets[0].id}",
                               headers={ "Authorization": f"Bearer {admin_access_token}" })
    assert response.status_code == 404


@pytest.mark.integration
def test_delete_set(test_client: TestClient, lift_sets: list[schemas.Set], simple_access_token: str):
    assert test_client.get(f"/api/sets/{lift_sets[0].id}", headers={
        "Authorization": f"Bearer {simple_access_token}",
    }).status_code == 200
    response = test_client.delete(f"/api/sets/{lift_sets[0].id}",
                                  headers={ "Authorization": f"Bearer {simple_access_token}" })
    assert response.status_code == 204
    assert test_client.get(f"/api/sets/{lift_sets[0].id}", headers={
        "Authorization": f"Bearer {simple_access_token}",
    }).status_code == 404


@pytest.mark.integration
def test_delete_not_found(test_client: TestClient, lift_sets: list[schemas.Set], simple_access_token: str,
                          admin_access_token: str):
    # non-existent set
    response = test_client.delete(f"/api/sets/{lift_sets[-1].id + 1}", headers={
        "Authorization": f"Bearer {simple_access_token}",
    })
    assert response.status_code == 404

    # existing set, incorrect user
    response = test_client.delete(f"/api/sets/{lift_sets[0].id}", headers={
        "Authorization": f"Bearer {admin_access_token}",
    })
    assert response.status_code == 404


if typing.TYPE_CHECKING:
    from fastapi.testclient import TestClient

