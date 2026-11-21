"""
Flask extensions and security decorators for CivicResolve.
"""

from functools import wraps
from flask import session, flash, redirect, url_for, request
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

csrf = CSRFProtect()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://"
)

def login_required(f):
    """Decorator to enforce admin authentication on protected endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Please sign in with administrator credentials to access this portal.", "warning")
            return redirect(url_for("admin.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function
