"""
Admin Management Blueprint for CivicResolve.
Handles municipal administrator authentication with rate limiting and hash verification,
session management, and the administrative triage and dispatch command center.
"""

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session
)
import database
from extensions import limiter, login_required
from config import Config

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    """Admin authentication endpoint with rate limiting and constant-time password check."""
    if session.get("is_admin"):
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if Config.verify_admin(username, password):
            session.clear()
            session["is_admin"] = True
            session["admin_user"] = username
            flash("Welcome! Signed in to Municipal Admin Command Center.", "success")
            next_url = request.args.get("next") or url_for("admin.dashboard")
            return redirect(next_url)
        else:
            flash("Invalid administrator credentials. Access denied.", "error")
            return render_template(
                "admin_login.html",
                default_user=Config.ADMIN_USERNAME,
                default_pass="admin123"
            ), 401

    return render_template(
        "admin_login.html",
        default_user=Config.ADMIN_USERNAME,
        default_pass="admin123"
    )

@admin_bp.route("/logout")
def logout():
    """Terminates admin session securely."""
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("admin.login"))

@admin_bp.route("")
@login_required
def dashboard():
    """
    Administrative control panel.
    Displays complaints sorted with Critical priority first, with pagination and filters.
    """
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
        sort_priority=True,
        page=page,
        per_page=15
    )
    stats = database.get_dashboard_stats()

    return render_template(
        "admin.html",
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
