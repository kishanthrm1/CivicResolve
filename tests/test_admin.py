"""
Integration tests for administrative authentication, route protection, and dispatch actions.
"""

import json
from config import TestingConfig
import database

def test_admin_route_protected_redirects_unauthenticated(client):
    """Verify accessing /admin without login redirects to /admin/login."""
    response = client.get("/admin")
    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]

def test_admin_login_success(client):
    """Verify signing in with configured admin credentials succeeds."""
    response = client.post("/admin/login", data={
        "username": TestingConfig.ADMIN_USERNAME,
        "password": "admin123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Municipal Command Center" in response.data

def test_admin_login_invalid_password_rejected(client):
    """Verify wrong credentials return 401 status."""
    response = client.post("/admin/login", data={
        "username": TestingConfig.ADMIN_USERNAME,
        "password": "wrongpassword123"
    })
    assert response.status_code == 401
    assert b"Invalid administrator credentials" in response.data

def test_admin_status_update_action(admin_client):
    """Verify authenticated admin can update complaint status and add official remark."""
    payload = {
        "status": "In Progress",
        "remark": "Field engineering team deployed with repair machinery."
    }
    response = admin_client.post(
        "/api/complaint/1/update-status",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    res_data = json.loads(response.data)
    assert res_data["success"] is True

    # Verify updated in database
    complaint = database.get_complaint_by_id(1)
    assert complaint["status"] == "In Progress"
    assert "Field engineering team deployed" in complaint["admin_remarks"]

    # Verify added to status history
    history = database.get_status_history(1)
    assert any("Field engineering team deployed" in h["remark"] for h in history)

def test_admin_override_action(admin_client):
    """Verify authenticated admin can override category, priority, and department."""
    payload = {
        "category": "Drainage",
        "priority": "Critical",
        "department": "Storm Water Drain Department",
        "priority_reason": "Manual emergency elevation after inspection."
    }
    response = admin_client.post(
        "/api/complaint/1/update-details",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    assert json.loads(response.data)["success"] is True

    complaint = database.get_complaint_by_id(1)
    assert complaint["category"] == "Drainage"
    assert complaint["priority"] == "Critical"
    assert complaint["department"] == "Storm Water Drain Department"

def test_admin_rerun_ai_action(admin_client):
    """Verify authenticated admin can trigger AI re-evaluation."""
    response = admin_client.post("/api/complaint/1/rerun-ai")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert "result" in data

def test_unauthenticated_api_status_update_blocked(client):
    """Verify anonymous caller cannot update status on API."""
    response = client.post(
        "/api/complaint/1/update-status",
        data=json.dumps({"status": "Resolved"}),
        content_type="application/json"
    )
    assert response.status_code == 302
