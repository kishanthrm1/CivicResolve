"""
Route blueprints package for CivicResolve.
"""
from routes.citizen import citizen_bp
from routes.admin import admin_bp
from routes.api import api_bp

__all__ = ["citizen_bp", "admin_bp", "api_bp"]
