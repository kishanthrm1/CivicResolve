"""
Citizen-facing Blueprint for CivicResolve.
Handles landing page, reporting flow with validation & rate limiting,
tracking timelines, public dashboard with pagination, and complaint inspection.
"""

import os
import uuid
from typing import Optional
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, abort, current_app
)
from werkzeug.utils import secure_filename
from PIL import Image

import database
import ai_service
from extensions import limiter
from config import Config

citizen_bp = Blueprint("citizen", __name__)

def allowed_file(filename: str) -> bool:
    """Validates image extension against whitelist."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@citizen_bp.route("/")
def index():
    """Landing page featuring platform overview, live statistics, and recent activity."""
    stats = database.get_dashboard_stats()
    recent_complaints, _, _, _ = database.get_all_complaints(page=1, per_page=4)
    return render_template("index.html", stats=stats, recent_complaints=recent_complaints)

@citizen_bp.route("/report", methods=["GET", "POST"])
@limiter.limit("15 per minute", methods=["POST"])
def report():
    """Citizen Issue Reporting page with input validation, geolocation, and AI triage."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        user_category = request.form.get("category", "Auto-detect with AI").strip()
        citizen_name = request.form.get("citizen_name", "").strip() or "Anonymous Citizen"
        citizen_contact = request.form.get("citizen_contact", "").strip()

        # Input sanitization and length validation
        errors = []
        if not title or len(title) < 3 or len(title) > 150:
            errors.append("Title is required and must be between 3 and 150 characters.")
        if not description or len(description) < 10 or len(description) > 3000:
            errors.append("Description is required and must be between 10 and 3000 characters.")
        if not location or len(location) < 3 or len(location) > 250:
            errors.append("Location is required and must be between 3 and 250 characters.")
        if len(citizen_name) > 100:
            errors.append("Citizen name must not exceed 100 characters.")
        if len(citizen_contact) > 100:
            errors.append("Contact information must not exceed 100 characters.")

        # Coordinate parsing & validation
        lat_str = request.form.get("latitude", "").strip()
        lon_str = request.form.get("longitude", "").strip()
        latitude: Optional[float] = None
        longitude: Optional[float] = None

        if lat_str:
            try:
                lat_val = float(lat_str)
                if -90.0 <= lat_val <= 90.0:
                    latitude = lat_val
                else:
                    errors.append("Invalid latitude range (-90 to +90).")
            except ValueError:
                errors.append("Latitude must be a valid decimal number.")

        if lon_str:
            try:
                lon_val = float(lon_str)
                if -180.0 <= lon_val <= 180.0:
                    longitude = lon_val
                else:
                    errors.append("Invalid longitude range (-180 to +180).")
            except ValueError:
                errors.append("Longitude must be a valid decimal number.")

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template(
                "report.html",
                prev_title=title,
                prev_desc=description,
                prev_loc=location,
                prev_name=citizen_name,
                prev_contact=citizen_contact
            ), 400

        # Secure Image Upload Handling
        image_rel_path: Optional[str] = None
        image_abs_path: Optional[str] = None

        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename and file.filename.strip():
                if not allowed_file(file.filename):
                    flash("Invalid file format. Only PNG, JPG, JPEG, and WEBP images are permitted.", "error")
                    return render_template("report.html"), 400

                clean_name = secure_filename(file.filename) or "image.jpg"
                unique_filename = f"{uuid.uuid4().hex}_{clean_name}"
                upload_dir = Config.UPLOAD_FOLDER
                os.makedirs(upload_dir, exist_ok=True)
                save_path = os.path.join(upload_dir, unique_filename)

                # Verify image integrity with Pillow
                try:
                    file.save(save_path)
                    with Image.open(save_path) as img:
                        img.verify()  # Verifies file format header
                    image_rel_path = f"uploads/{unique_filename}"
                    image_abs_path = save_path
                except Exception as img_err:
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    flash("Uploaded file is corrupted or not a valid image.", "error")
                    return render_template("report.html"), 400

        # Execute AI Classification (Gemini 2.5 Flash or Smart Offline Demo Mode)
        ai_result = ai_service.analyze_complaint(
            title=title,
            description=description,
            location=location,
            user_selected_category=user_category,
            image_path=image_abs_path
        )

        complaint_data = {
            "title": title,
            "description": description,
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "category": ai_result["category"],
            "priority": ai_result["priority"],
            "priority_reason": ai_result.get("priority_reason", ""),
            "department": ai_result["department"],
            "ai_summary": ai_result.get("summary", title),
            "ai_confidence": ai_result.get("confidence", 88),
            "ai_mode": ai_result.get("ai_mode", "Demo Mode"),
            "image_path": image_rel_path,
            "citizen_name": citizen_name,
            "citizen_contact": citizen_contact
        }

        complaint_id, complaint_code = database.insert_complaint(complaint_data)
        flash(f"Complaint successfully logged! Complaint ID: {complaint_code}", "success")
        return redirect(url_for("citizen.report_success", complaint_code=complaint_code))

    return render_template("report.html")

@citizen_bp.route("/success/<complaint_code>")
def report_success(complaint_code: str):
    """Confirmation page presenting AI classification results and Complaint ID."""
    complaint = database.get_complaint_by_code(complaint_code)
    if not complaint:
        flash("Complaint not found.", "error")
        return redirect(url_for("citizen.index"))
    return render_template("success.html", complaint=complaint)

@citizen_bp.route("/track")
def track():
    """Citizen Complaint Tracking portal by Complaint ID with visual timeline."""
    code = request.args.get("code", "").strip()
    complaint = None
    history = []

    if code:
        complaint = database.get_complaint_by_code(code)
        if complaint:
            history = database.get_status_history(complaint["id"])
        else:
            flash(f"No complaint found matching ID '{code}'. Please verify the code or check recent samples.", "warning")

    recent_samples, _, _, _ = database.get_all_complaints(page=1, per_page=6)
    return render_template("track.html", complaint=complaint, history=history, search_code=code, recent_samples=recent_samples)

@citizen_bp.route("/dashboard")
def dashboard():
    """Public Civic Dashboard featuring filters, Leaflet map, Chart.js analytics, and pagination."""
    status_filter = request.args.get("status", "All")
    category_filter = request.args.get("category", "All")
    priority_filter = request.args.get("priority", "All")
    search_query = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)

    complaints, total_count, total_pages, current_page = database.get_all_complaints(
        status=status_filter,
        category=category_filter,
        priority=priority_filter,
        search=search_query,
        page=page,
        per_page=Config.ITEMS_PER_PAGE
    )
    stats = database.get_dashboard_stats()

    return render_template(
        "dashboard.html",
        complaints=complaints,
        stats=stats,
        current_status=status_filter,
        current_category=category_filter,
        current_priority=priority_filter,
        current_search=search_query,
        page=current_page,
        total_pages=total_pages,
        total_count=total_count
    )

@citizen_bp.route("/complaint/<int:id>")
def complaint_detail(id: int):
    """Detailed view for a single complaint including AI diagnostics and full audit history."""
    complaint = database.get_complaint_by_id(id)
    if not complaint:
        abort(404)
    history = database.get_status_history(id)
    return render_template("complaint_detail.html", complaint=complaint, history=history)
