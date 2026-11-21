"""
Integration tests migrated from the legacy test_app.py unittest suite.
Covers database seeding, AI triage, citizen reporting flow, tracking,
admin authentication, AJAX API endpoints, and error page handlers.
"""

import json
import pytest


# ---------------------------------------------------------------------------
# Database seeding
# ---------------------------------------------------------------------------

def test_database_seeded_with_12_complaints(app):
    """Verify 12 sample complaints are seeded with correct aggregates."""
    import database
    with app.app_context():
        stats = database.get_dashboard_stats()
    assert stats["total"] >= 12
    assert stats["critical"] >= 3
    assert stats["resolved"] >= 4


# ---------------------------------------------------------------------------
# AI Demo-mode classifier
# ---------------------------------------------------------------------------

def test_ai_critical_drainage_manhole(app):
    """Drainage manhole near school must resolve to Critical priority."""
    import ai_service
    result = ai_service.analyze_complaint(
        title="Dangerous open manhole on pedestrian path",
        description="Open manhole next to an elementary school with raw sewage exposed.",
        location="NSR Road, Saibaba Colony",
    )
    assert result["category"] == "Drainage"
    assert result["priority"] == "Critical"
    assert result["department"] == "Storm Water Drain Department"
    assert "manhole" in result["priority_reason"].lower()
    assert result["ai_mode"] == "Demo Mode"


def test_ai_high_priority_pothole(app):
    """Large pothole on a main road should be High priority."""
    import ai_service
    result = ai_service.analyze_complaint(
        title="Huge pothole crater on highway",
        description="Deep crater on main road causing buses to brake suddenly.",
        location="Trichy Road",
    )
    assert result["category"] == "Pothole"
    assert result["priority"] == "High"
    assert result["department"] == "Roads & Highways Department"


def test_ai_low_priority_streetlight(app):
    """Single dim bulb should produce Low priority with Electricity dept."""
    import ai_service
    result = ai_service.analyze_complaint(
        title="Dim streetlight bulb",
        description="Single dim flickering bulb on park jogging track.",
        location="Race Course",
    )
    assert result["category"] == "Streetlight"
    assert result["priority"] == "Low"
    assert result["department"] == "Electricity Department / Street Lighting Division"


# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------

def test_homepage_renders_hero(client):
    """Landing page returns 200 and contains the hero heading text."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"CivicResolve" in response.data
    assert b"Report Civic Issues" in response.data


# ---------------------------------------------------------------------------
# Citizen reporting flow
# ---------------------------------------------------------------------------

def test_citizen_report_flow_water_pipeline(client):
    """Submit a water-pipe complaint and confirm AI routes it correctly."""
    post_data = {
        "title": "Test Broken Water Pipeline near Market",
        "description": "High pressure drinking water pipe burst flooding road near grocery shops.",
        "location": "Opposite Town Hall, Big Bazaar St, Coimbatore",
        "category": "Auto-detect with AI",
        "citizen_name": "Test Citizen",
        "citizen_contact": "test@example.com",
        "latitude": "10.9955",
        "longitude": "76.9610",
    }
    response = client.post("/report", data=post_data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Complaint Successfully Filed!" in response.data
    assert b"Water Supply" in response.data


# ---------------------------------------------------------------------------
# Public tracking portal
# ---------------------------------------------------------------------------

def test_tracking_portal_loads_cr_0001(client):
    """Tracking page for CR-2026-0001 must display the complaint and history."""
    response = client.get("/track?code=CR-2026-0001")
    assert response.status_code == 200
    assert b"CR-2026-0001" in response.data
    assert b"Roads" in response.data


# ---------------------------------------------------------------------------
# Public dashboard filters
# ---------------------------------------------------------------------------

def test_dashboard_filter_in_progress_pothole(client):
    """Dashboard with status/category filters should still return 200."""
    response = client.get("/dashboard?status=In Progress&category=Pothole")
    assert response.status_code == 200
    assert b"Public Civic Dashboard" in response.data


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------

def test_api_stats_shape(client):
    """/api/stats must return JSON with 'total' and 'critical' keys."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "total" in data
    assert "critical" in data


def test_api_complaints_non_empty_list(client):
    """/api/complaints must return a non-empty JSON array."""
    response = client.get("/api/complaints")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0


# ---------------------------------------------------------------------------
# Admin authentication & actions
# ---------------------------------------------------------------------------

def test_unauthenticated_admin_redirects_to_login(client):
    """/admin without session must redirect (302) to login."""
    response = client.get("/admin")
    assert response.status_code == 302


def test_admin_login_then_status_update_and_rerun_ai(client):
    """Full admin flow: login → status update → re-run AI → verify history."""
    import database

    # Login
    login = client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=True,
    )
    assert login.status_code == 200
    assert b"Municipal Command Center" in login.data

    # Update complaint #1 to Resolved
    update = client.post(
        "/api/complaint/1/update-status",
        json={
            "status": "Resolved",
            "remark": "All potholes patched with bituminous hot-mix and inspected.",
        },
    )
    assert update.status_code == 200
    assert json.loads(update.data)["success"] is True

    # Confirm status_history entry persisted
    history = database.get_status_history(1)
    remarks = [h["remark"] for h in history]
    assert any("bituminous hot-mix" in r for r in remarks)

    # Re-run AI analysis
    rerun = client.post("/api/complaint/1/rerun-ai")
    assert rerun.status_code == 200
    assert json.loads(rerun.data)["success"] is True


# ---------------------------------------------------------------------------
# Custom error pages
# ---------------------------------------------------------------------------

def test_404_page_returns_branded_html(client):
    """Requests to unknown routes must return HTTP 404 with branded content."""
    response = client.get("/this-route-does-not-exist-at-all")
    assert response.status_code == 404
    assert b"404" in response.data
    assert b"CivicResolve" in response.data
