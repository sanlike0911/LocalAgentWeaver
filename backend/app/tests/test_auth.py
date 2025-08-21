import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.auth.service import AuthService
from app.features.auth.schemas import UserCreate, UserLogin


def test_register_user(client: TestClient):
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert data["is_active"] is True


def test_register_duplicate_email(client: TestClient):
    client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "username": "testuser", "password": "testpassword"}
    )
    
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "username": "testuser2", "password": "anotherpassword"}
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_login_user(client: TestClient):
    client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "username": "testuser", "password": "testpassword"}
    )
    
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "username": "testuser", "password": "testpassword"}
    )
    
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "testpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_get_current_user(client: TestClient):
    # Register and login first
    client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "username": "testuser", "password": "testpassword"}
    )
    
    login_response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]
    
    # Test getting current user info
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"


def test_get_current_user_invalid_token(client: TestClient):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_service_create_user(db_session: AsyncSession):
    user_data = UserCreate(email="test@example.com", username="testuser", password="testpassword")
    user = await AuthService.create_user(db_session, user_data)
    
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.hashed_password != "testpassword"
    assert user.is_active is True


@pytest.mark.asyncio
async def test_auth_service_authenticate_user(db_session: AsyncSession):
    user_data = UserCreate(email="test@example.com", username="testuser", password="testpassword")
    created_user = await AuthService.create_user(db_session, user_data)
    
    login_data = UserLogin(email="test@example.com", password="testpassword")
    authenticated_user = await AuthService.authenticate_user(db_session, login_data)
    assert authenticated_user is not None
    assert authenticated_user.id == created_user.id
    
    # Test wrong password
    with pytest.raises(Exception):  # Should raise HTTPException
        wrong_login = UserLogin(email="test@example.com", password="wrongpassword")
        await AuthService.authenticate_user(db_session, wrong_login)


@pytest.mark.asyncio
async def test_auth_service_get_user_by_email(db_session: AsyncSession):
    user_data = UserCreate(email="test@example.com", username="testuser", password="testpassword")
    created_user = await AuthService.create_user(db_session, user_data)
    
    found_user = await AuthService.get_user_by_email(db_session, "test@example.com")
    assert found_user is not None
    assert found_user.id == created_user.id
    
    not_found = await AuthService.get_user_by_email(db_session, "notfound@example.com")
    assert not_found is None