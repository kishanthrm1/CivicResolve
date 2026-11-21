"""
Integration tests for citizen tracking portal and complaint lookup.
"""

def test_track_empty_view(client):
    """Verify visiting /track without query parameter renders test sample pills."""
    response = client.get("/track")
    assert response.status_code == 200
    assert b"Track Your Complaint Status" in response.data
    assert b"Instant Status Verification" in response.data

def test_track_valid_code(client):
    """Verify tracking an existing complaint renders progress stage and history."""
    response = client.get("/track?code=CR-2026-0001")
    assert response.status_code == 200
    assert b"CR-2026-0001" in response.data
    assert b"Resolution Progress Stage" in response.data
    assert b"Roads &amp; Highways Department" in response.data or b"Roads & Highways Department" in response.data

def test_track_invalid_code_not_found(client):
    """Verify tracking a non-existent code renders a friendly not-found message."""
    response = client.get("/track?code=CR-9999-9999")
    assert response.status_code == 200
    assert b"Complaint Not Found" in response.data
    assert b"CR-9999-9999" in response.data
