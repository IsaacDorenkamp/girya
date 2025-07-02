from __future__ import annotations
import typing

import pytest

from tests.conftest import simple_access_token


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


if typing.TYPE_CHECKING:
    from fastapi.testclient import TestClient
