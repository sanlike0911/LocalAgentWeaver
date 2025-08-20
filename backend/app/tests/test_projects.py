import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from ..features.auth.service import AuthService
from ..features.auth.schemas import UserCreate
from ..features.projects.service import ProjectService
from ..features.projects.schemas import ProjectCreate


def get_auth_headers(client: TestClient) -> dict:
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_project(client: TestClient):
    headers = get_auth_headers(client)
    
    response = client.post(
        "/projects/",
        json={"name": "Test Project", "description": "A test project"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "A test project"
    assert "id" in data
    assert "owner_id" in data


def test_create_project_without_auth(client: TestClient):
    response = client.post(
        "/projects/",
        json={"name": "Test Project", "description": "A test project"}
    )
    assert response.status_code == 401


def test_get_projects(client: TestClient):
    headers = get_auth_headers(client)
    
    client.post(
        "/projects/",
        json={"name": "Test Project 1", "description": "First project"},
        headers=headers
    )
    client.post(
        "/projects/",
        json={"name": "Test Project 2", "description": "Second project"},
        headers=headers
    )
    
    response = client.get("/projects/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] in ["Test Project 1", "Test Project 2"]


def test_get_project_by_id(client: TestClient):
    headers = get_auth_headers(client)
    
    create_response = client.post(
        "/projects/",
        json={"name": "Test Project", "description": "A test project"},
        headers=headers
    )
    project_id = create_response.json()["id"]
    
    response = client.get(f"/projects/{project_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["id"] == project_id


def test_update_project(client: TestClient):
    headers = get_auth_headers(client)
    
    create_response = client.post(
        "/projects/",
        json={"name": "Test Project", "description": "A test project"},
        headers=headers
    )
    project_id = create_response.json()["id"]
    
    response = client.put(
        f"/projects/{project_id}",
        json={"name": "Updated Project", "description": "Updated description"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Project"
    assert data["description"] == "Updated description"


def test_delete_project(client: TestClient):
    headers = get_auth_headers(client)
    
    create_response = client.post(
        "/projects/",
        json={"name": "Test Project", "description": "A test project"},
        headers=headers
    )
    project_id = create_response.json()["id"]
    
    response = client.delete(f"/projects/{project_id}", headers=headers)
    assert response.status_code == 200
    
    get_response = client.get(f"/projects/{project_id}", headers=headers)
    assert get_response.status_code == 404


def test_project_service_create_project(db_session: Session):
    user_data = UserCreate(email="test@example.com", password="testpassword")
    user = AuthService.create_user(db_session, user_data)
    
    project_data = ProjectCreate(name="Test Project", description="A test project")
    project = ProjectService.create_project(db_session, project_data, user)
    
    assert project.name == "Test Project"
    assert project.description == "A test project"
    assert project.owner_id == user.id


def test_project_service_check_ownership(db_session: Session):
    user_data = UserCreate(email="test@example.com", password="testpassword")
    user = AuthService.create_user(db_session, user_data)
    
    project_data = ProjectCreate(name="Test Project", description="A test project")
    project = ProjectService.create_project(db_session, project_data, user)
    
    assert ProjectService.check_project_ownership(db_session, project.id, user) is True
    
    other_user_data = UserCreate(email="other@example.com", password="testpassword")
    other_user = AuthService.create_user(db_session, other_user_data)
    
    assert ProjectService.check_project_ownership(db_session, project.id, other_user) is False