"""
Integration tests for /health check and public REST API endpoints.
"""

import json

def test_health_check_endpoint(client):
    """Verify /health endpoint returns HTTP 200 with JSON status ok for Cloud Run."""
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "ok"
    assert data["service"] == "CivicResolve"

def test_api_stats_endpoint(client):
    """Verify /api/stats returns aggregated metrics."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "total" in data
    assert "reported" in data
    assert "in_progress" in data
    assert "resolved" in data
    assert "critical" in data
    assert data["total"] >= 12

def test_api_complaints_endpoint(client):
    """Verify /api/complaints returns geospatial coordinates for Leaflet map."""
    response = client.get("/api/complaints")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) >= 12
    first = data[0]
    assert "code" in first
    assert "latitude" in first
    assert "longitude" in first
    assert "priority" in first
