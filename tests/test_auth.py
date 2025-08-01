import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_user():
    """Test user registration"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data

def test_login_user():
    """Test user login"""
    # First register a user
    user_data = {
        "email": "login@example.com",
        "username": "loginuser",
        "password": "loginpass123"
    }
    client.post("/auth/register", json=user_data)
    
    # Then login
    login_data = {
        "email": "login@example.com",
        "password": "loginpass123"
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_get_current_user():
    """Test getting current user info"""
    # Register and login
    user_data = {
        "email": "current@example.com",
        "username": "currentuser",
        "password": "currentpass123"
    }
    client.post("/auth/register", json=user_data)
    
    login_response = client.post("/auth/login", json={
        "email": "current@example.com",
        "password": "currentpass123"
    })
    token = login_response.json()["access_token"]
    
    # Get user info
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "current@example.com"
    assert data["username"] == "currentuser"
