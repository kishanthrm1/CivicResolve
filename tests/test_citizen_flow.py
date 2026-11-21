"""
Integration tests for citizen reporting, input validation, and public dashboard flows.
"""

import io

def test_homepage_loads(client):
    """Verify landing page renders successfully with live statistics."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"CivicResolve" in response.data
    assert b"Report Civic Issues in Seconds" in response.data

def test_report_form_page_loads(client):
    """Verify citizen report form page renders with accessible inputs."""
    response = client.get("/report")
    assert response.status_code == 200
    assert b"Report a Civic Issue" in response.data
    assert b"Auto-detect with AI" in response.data

def test_valid_complaint_submission(client):
    """Verify successful complaint submission redirects to confirmation page."""
    data = {
        "title": "Severe road cavity on main bus route",
        "description": "Deep asphalt hole opening up on main bus lane near commercial junction.",
        "location": "Cross Cut Road, Gandhipuram, Coimbatore",
        "category": "Auto-detect with AI",
        "citizen_name": "Test Reporter",
        "citizen_contact": "+91 98421 99999",
        "latitude": "11.0168",
        "longitude": "76.9558"
    }
    response = client.post("/report", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Complaint Successfully Filed!" in response.data
    assert b"CR-2026-" in response.data

def test_validation_empty_title_fails(client):
    """Verify submission fails with 400 when title is missing."""
    data = {
        "title": "",
        "description": "Valid long description of the issue occurring on the sidewalk.",
        "location": "RS Puram, Coimbatore"
    }
    response = client.post("/report", data=data)
    assert response.status_code == 400
    assert b"Title is required" in response.data

def test_validation_short_description_fails(client):
    """Verify submission fails with 400 when description is under 10 chars."""
    data = {
        "title": "Valid Issue Title",
        "description": "Too short",
        "location": "RS Puram, Coimbatore"
    }
    response = client.post("/report", data=data)
    assert response.status_code == 400
    assert b"Description is required" in response.data

def test_validation_empty_location_fails(client):
    """Verify submission fails with 400 when location is missing."""
    data = {
        "title": "Valid Issue Title",
        "description": "Valid detailed description of the municipal issue.",
        "location": ""
    }
    response = client.post("/report", data=data)
    assert response.status_code == 400
    assert b"Location is required" in response.data

def test_validation_invalid_latitude_fails(client):
    """Verify coordinate range validation fails for latitude > 90."""
    data = {
        "title": "Valid Issue Title",
        "description": "Valid detailed description of the municipal issue.",
        "location": "Town Hall, Coimbatore",
        "latitude": "150.0"  # Invalid latitude
    }
    response = client.post("/report", data=data)
    assert response.status_code == 400
    assert b"Invalid latitude range" in response.data

def test_validation_invalid_file_type_fails(client):
    """Verify uploading an unauthorized file type (e.g. .txt or .exe) is rejected."""
    fake_txt = (io.BytesIO(b"malicious script content"), "test.exe")
    data = {
        "title": "Valid Issue Title",
        "description": "Valid detailed description of the municipal issue.",
        "location": "Town Hall, Coimbatore",
        "image": fake_txt
    }
    response = client.post("/report", data=data)
    assert response.status_code == 400
    assert b"Invalid file format" in response.data

def test_dashboard_pagination(client):
    """Verify dashboard loads page 1 and respects pagination parameters."""
    response = client.get("/dashboard?page=1")
    assert response.status_code == 200
    assert b"Public Civic Dashboard" in response.data
    assert b"Page 1" in response.data
