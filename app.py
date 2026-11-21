"""
CivicResolve - AI-Powered Civic Issue Reporting and Resolution Platform
Main Application Factory and WSGI Entry Point.
"""

import os
import logging
import json
from typing import Optional, Type
from flask import Flask, session, request, Response, render_template
from config import Config, DevelopmentConfig, ProductionConfig
from extensions import csrf, limiter
import database


def configure_logging(app: Flask) -> None:
    """Configure structured JSON logging for Cloud Run / GCP Cloud Logging.

    In production (FLASK_ENV=production) each log record is emitted as a
    single-line JSON object with the fields expected by Cloud Logging:
    ``severity``, ``message``, ``logger``, ``pathname``, ``lineno``.
    In development the standard human-readable format is used instead.
    """
    is_production = os.getenv("FLASK_ENV", "development").lower() == "production"

    if is_production:
        class JsonFormatter(logging.Formatter):
            """Formats log records as Cloud Logging–compatible JSON."""
            def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
                log_entry = {
                    "severity": record.levelname,
                    "message": super().format(record),
                    "logger": record.name,
                    "pathname": record.pathname,
                    "lineno": record.lineno,
                }
                return json.dumps(log_entry)

        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logging.root.handlers = [handler]
        logging.root.setLevel(logging.INFO)
        app.logger.info("CivicResolve starting in production mode with JSON logging.")
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        app.logger.debug("CivicResolve starting in development mode.")

def create_app(config_class: Optional[Type[Config]] = None) -> Flask:
    """Application factory for CivicResolve."""
    app = Flask(__name__)

    # Determine environment config
    if config_class is None:
        env = os.getenv("FLASK_ENV", "development").lower()
        if env == "production":
            config_class = ProductionConfig
        else:
            config_class = DevelopmentConfig

    app.config.from_object(config_class)

    # Configure structured logging
    configure_logging(app)

    # Initialize extensions
    csrf.init_app(app)
    limiter.init_app(app)

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Register Blueprints
    from routes.citizen import citizen_bp
    from routes.admin import admin_bp
    from routes.api import api_bp, health_check

    app.register_blueprint(citizen_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Exempt health check from CSRF
    csrf.exempt(health_check)

    # Global Template Context Processor
    @app.context_processor
    def inject_global_data():
        gemini_key = app.config.get("GEMINI_API_KEY", "")
        return {
            "active_ai_mode": "Gemini" if gemini_key else "Demo Mode",
            "has_gemini_key": bool(gemini_key),
            "admin_logged_in": session.get("is_admin", False),
            "admin_user": session.get("admin_user", ""),
        }

    # Security Response Headers Middleware
    @app.after_request
    def set_security_headers(response: Response) -> Response:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy allowing specified CDNs
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https://*.tile.openstreetmap.org https://unpkg.com; "
            "connect-src 'self' https://*.tile.openstreetmap.org;"
        )
        response.headers["Content-Security-Policy"] = csp
        return response

    # Auto-create tables and seed data if DB is empty on boot (crucial for Cloud Run)
    with app.app_context():
        database.init_db(app.config.get("DB_PATH"))

    # Custom Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        """Render branded 404 page with accessible markup."""
        app.logger.warning("404 Not Found: %s %s", request.method, request.path)
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Render branded 500 page; log the full exception."""
        app.logger.error("500 Internal Server Error: %s", error, exc_info=True)
        return render_template("500.html"), 500

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Return JSON for API callers, HTML page for browser requests."""
        app.logger.warning("429 Rate limit exceeded: %s %s", request.method, request.path)
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            from flask import jsonify
            return jsonify({"error": "Too many requests. Please slow down.", "code": 429}), 429
        from flask import flash, redirect, url_for
        flash("You are sending requests too quickly. Please wait a moment and try again.", "error")
        return redirect(url_for("citizen.index")), 429

    return app

# WSGI Application instance for Gunicorn
app = create_app()

if __name__ == "__main__":
    # Cloud Run injects $PORT (defaulting to 5000 for local development)
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
