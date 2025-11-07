"""
Tests for Backend API Service
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    with patch('app.check_ml_service', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data


def test_health():
    """Test health endpoint"""
    with patch('app.check_ml_service', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


def test_health_ml_service_down():
    """Test health endpoint when ML service is down"""
    with patch('app.check_ml_service', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = False
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["ml_service_status"] == "unavailable"
