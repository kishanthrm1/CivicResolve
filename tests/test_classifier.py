"""
Unit tests for ai_service.py rule-based triage and risk evaluation.
"""

import ai_service

def test_critical_manhole_drainage():
    """Verify open manhole near school is classified as Critical Drainage."""
    result = ai_service.analyze_complaint(
        title="Open manhole on pedestrian path",
        description="Dangerous uncovered manhole next to elementary school with exposed sewer water.",
        location="Saibaba Colony, NSR Road"
    )
    assert result["category"] == "Drainage"
    assert result["priority"] == "Critical"
    assert result["department"] == "Storm Water Drain Department"
    assert "manhole" in result["priority_reason"].lower()
    assert result["confidence"] >= 80
    assert result["ai_mode"] in ("Gemini", "Demo Mode")

def test_critical_burst_water_main():
    """Verify high-pressure pipe burst is classified as Critical Water Leakage."""
    result = ai_service.analyze_complaint(
        title="Major water pipe burst flooding road",
        description="Drinking water pipe burst spewing water 4 feet high and flooding basements.",
        location="Avinashi Road, Peelamedu"
    )
    assert result["category"] == "Water Leakage"
    assert result["priority"] == "Critical"
    assert result["department"] == "Water Supply & Sewerage Board"
    assert "burst" in result["priority_reason"].lower() or "rupture" in result["priority_reason"].lower()

def test_critical_sparking_electric_wire():
    """Verify exposed live wire is classified as Critical Streetlight."""
    result = ai_service.analyze_complaint(
        title="Exposed sparking wire dangling from street light",
        description="Loose overhead electrical live wire hanging near market entrance.",
        location="Ukkadam Bypass"
    )
    assert result["category"] == "Streetlight"
    assert result["priority"] == "Critical"
    assert result["department"] == "Electricity Department / Street Lighting Division"

def test_high_priority_pothole():
    """Verify deep crater on main road is classified as High Priority Pothole."""
    result = ai_service.analyze_complaint(
        title="Deep pothole crater on highway",
        description="Large asphalt crater on main road causing heavy traffic swerving.",
        location="Trichy Road, Singanallur"
    )
    assert result["category"] == "Pothole"
    assert result["priority"] == "High"
    assert result["department"] == "Roads & Highways Department"

def test_medium_priority_garbage():
    """Verify overflowing dumpsters are classified as Medium Priority Garbage."""
    result = ai_service.analyze_complaint(
        title="Overflowing commercial garbage dump",
        description="Uncollected waste bins behind market emitting foul smell.",
        location="RS Puram, DB Road"
    )
    assert result["category"] == "Garbage"
    assert result["priority"] == "Medium"
    assert result["department"] == "Solid Waste Management / Sanitation Department"

def test_low_priority_dim_bulb():
    """Verify single flickering bulb is classified as Low Priority."""
    result = ai_service.analyze_complaint(
        title="Dim flickering streetlight",
        description="Single dim flickering bulb on park jogging track.",
        location="Race Course"
    )
    assert result["category"] == "Streetlight"
    assert result["priority"] == "Low"
    assert result["department"] == "Electricity Department / Street Lighting Division"

def test_user_category_override():
    """Verify user preset category is respected if valid."""
    result = ai_service.analyze_complaint(
        title="Broken surface near corner",
        description="Asphalt unevenness",
        location="Gandhipuram",
        user_selected_category="Road Damage"
    )
    assert result["category"] == "Road Damage"
    assert result["department"] == "Roads & Highways Department"
