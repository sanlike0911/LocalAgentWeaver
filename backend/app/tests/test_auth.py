import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from ..features.auth.service import AuthService
from ..features.auth.schemas import UserCreate


def test_register_user(client: TestClient):
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert data["is_active"] is True


def test_register_duplicate_email(client: TestClient):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "anotherpassword"}
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_login_user(client: TestClient):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "testpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_auth_service_create_user(db_session: Session):
    user_data = UserCreate(email="test@example.com", password="testpassword")
    user = AuthService.create_user(db_session, user_data)
    
    assert user.email == "test@example.com"
    assert user.hashed_password != "testpassword"
    assert user.is_active is True


def test_auth_service_authenticate_user(db_session: Session):
    user_data = UserCreate(email="test@example.com", password="testpassword")
    created_user = AuthService.create_user(db_session, user_data)
    
    authenticated_user = AuthService.authenticate_user(
        db_session, "test@example.com", "testpassword"
    )
    assert authenticated_user is not None
    assert authenticated_user.id == created_user.id
    
    wrong_auth = AuthService.authenticate_user(
        db_session, "test@example.com", "wrongpassword"
    )
    assert wrong_auth is None