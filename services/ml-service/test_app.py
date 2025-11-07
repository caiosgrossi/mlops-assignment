"""
Tests for ML Service
"""
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


def test_health():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_get_playlists():
    """Test get playlists endpoint"""
    response = client.get("/playlists")
    assert response.status_code == 200
    data = response.json()
    assert "playlists" in data
    assert len(data["playlists"]) > 0


def test_get_users():
    """Test get users endpoint"""
    response = client.get("/users")
    assert response.status_code == 200
    data = response.json()
    assert "users" in data


def test_recommend_existing_user():
    """Test recommendations for existing user"""
    response = client.post(
        "/recommend",
        json={"user_id": "user1", "num_recommendations": 3}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user1"
    assert "recommendations" in data
    assert len(data["recommendations"]) <= 3
    assert data["algorithm"] == "collaborative_filtering"


def test_recommend_new_user():
    """Test recommendations for new user (popularity-based)"""
    response = client.post(
        "/recommend",
        json={"user_id": "new_user", "num_recommendations": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "new_user"
    assert "recommendations" in data
    assert len(data["recommendations"]) <= 2


def test_recommend_default_count():
    """Test recommendations with default count"""
    response = client.post(
        "/recommend",
        json={"user_id": "user1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["recommendations"]) <= 3
