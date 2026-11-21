"""
Pytest configuration and shared test fixtures for CivicResolve.
"""

import os
import pytest
from flask import Flask
from app import create_app
from config import TestingConfig
import database

@pytest.fixture(scope="session")
def app() -> Flask:
    """Creates a test application instance with dedicated test database."""
    test_app = create_app(TestingConfig)
    
    # Initialize test database
    with test_app.app_context():
        database.init_db(test_app.config["DB_PATH"])

    yield test_app

    # Teardown: Clean up test database file if created
    test_db = test_app.config.get("DB_PATH")
    if test_db and os.path.exists(test_db):
        try:
            os.remove(test_db)
        except OSError:
            pass

@pytest.fixture
def client(app: Flask):
    """Provides a test client for unauthenticated citizen requests."""
    return app.test_client()

@pytest.fixture
def admin_client(app: Flask):
    """Provides a pre-authenticated test client with admin session."""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["is_admin"] = True
        sess["admin_user"] = TestingConfig.ADMIN_USERNAME
    return client
