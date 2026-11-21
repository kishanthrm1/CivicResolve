"""
API Blueprint for CivicResolve.
Provides health checks for Cloud Run, public aggregated metrics,
and authenticated AJAX endpoints for administrative triage actions.
"""

import os
from typing import Dict, Any, List
from flask import Blueprint, jsonify, request, current_app
import database
import ai_service
from extensions import login_required
from config import Config

api_bp = Blueprint("api", __name__)

@api_bp.route("/health")
def health_check():
    """Health check endpoint required for Google Cloud Run container liveness/readiness."""
    return jsonify({"status": "ok", "service": "CivicResolve"}), 200

@api_bp.route("/api/stats")
def api_stats():
    """Returns real-time aggregated metrics for public dashboard charts."""
    stats = database.get_dashboard_stats()
    return jsonify(stats), 200

@api_bp.route("/api/complaints")
def api_complaints():
    """Returns complaints with coordinates for Leaflet geospatial rendering."""
    complaints, _, _, _ = database.get_all_complaints(page=1, per_page=100)
    data: List[Dict[str, Any]] = []
    for c in complaints:
        data.append({
            "id": c["id"],
            "code": c["complaint_code"],
            "title": c["title"],
            "description": c["description"],
            "location": c["location"],
            "latitude": c["latitude"],
            "longitude": c["longitude"],
            "category": c["category"],
            "priority": c["priority"],
            "department": c["department"],
            "status": c["status"],
            "image_path": c["image_path"],
            "created_at": c["created_at"]
        })
    return jsonify(data), 200

@api_bp.route("/api/complaint/<int:id>/update-status", methods=["POST"])
@login_required
def api_update_status(id: int):
    """Admin action: updates resolution status and appends remark to audit log."""
    data = request.get_json(silent=True) or request.form
    new_status = data.get("status", "").strip()
    remark = data.get("remark", "").strip()

    if new_status not in ["Reported", "In Progress", "Resolved"]:
        return jsonify({"success": False, "error": "Invalid status value"}), 400

    if len(remark) > 500:
        return jsonify({"success": False, "error": "Remarks must not exceed 500 characters"}), 400

    complaint = database.get_complaint_by_id(id)
    if not complaint:
        return jsonify({"success": False, "error": "Complaint not found"}), 404

    database.update_complaint_status(id, new_status, remark)
    return jsonify({"success": True, "message": f"Status updated to {new_status}"}), 200

@api_bp.route("/api/complaint/<int:id>/update-details", methods=["POST"])
@login_required
def api_update_details(id: int):
    """Admin action: overrides AI-assigned category, priority, or department."""
    data = request.get_json(silent=True) or request.form
    category = data.get("category", "").strip()
    priority = data.get("priority", "").strip()
    department = data.get("department", "").strip()
    reason = data.get("priority_reason", "Administrative manual override").strip()

    if category not in ai_service.VALID_CATEGORIES:
        return jsonify({"success": False, "error": "Invalid category"}), 400
    if priority not in ai_service.VALID_PRIORITIES:
        return jsonify({"success": False, "error": "Invalid priority"}), 400
    if not department:
        return jsonify({"success": False, "error": "Department is required"}), 400

    complaint = database.get_complaint_by_id(id)
    if not complaint:
        return jsonify({"success": False, "error": "Complaint not found"}), 404

    database.update_complaint_details(id, category, priority, department, reason)
    return jsonify({"success": True, "message": "Complaint details updated successfully"}), 200

@api_bp.route("/api/complaint/<int:id>/rerun-ai", methods=["POST"])
@login_required
def api_rerun_ai(id: int):
    """Admin action: re-evaluates complaint using AI triage service."""
    complaint = database.get_complaint_by_id(id)
    if not complaint:
        return jsonify({"success": False, "error": "Complaint not found"}), 404

    img_abs_path = None
    if complaint["image_path"]:
        img_abs_path = os.path.join(Config.BASE_DIR, "static", complaint["image_path"])

    ai_result = ai_service.analyze_complaint(
        title=complaint["title"],
        description=complaint["description"],
        location=complaint["location"],
        user_selected_category=complaint["category"],
        image_path=img_abs_path
    )

    database.update_complaint_ai(id, ai_result)
    return jsonify({"success": True, "message": "AI re-analysis completed", "result": ai_result}), 200

@api_bp.route("/api/complaint/<int:id>/delete", methods=["POST"])
@login_required
def api_delete_complaint(id: int):
    """Admin action: deletes spam or invalid complaint."""
    complaint = database.get_complaint_by_id(id)
    if not complaint:
        return jsonify({"success": False, "error": "Complaint not found"}), 404

    database.delete_complaint(id)
    return jsonify({"success": True, "message": "Complaint deleted successfully"}), 200
