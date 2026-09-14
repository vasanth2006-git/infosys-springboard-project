import pytest
import models
from main import ADMIN_EMAIL, ADMIN_PASSWORD

# -------------------------------------------------------------
# Authentication & Onboarding Tests
# -------------------------------------------------------------
def test_get_login_page(client):
    """GET /login should render the login HTML page."""
    response = client.get("/login")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

def test_post_login_admin_success(client):
    """POST /login with valid admin credentials should redirect to admin dashboard and set cookie."""
    response = client.post(
        "/login",
        data={
            "role": "admin",
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        },
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers.get("location") == "/admin/dashboard"
    assert "admin_session" in response.cookies

def test_post_login_admin_invalid_password(client):
    """POST /login with incorrect admin password should fail and re-render login with error."""
    response = client.post(
        "/login",
        data={
            "role": "admin",
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 200
    assert "Invalid admin email or password" in response.text

def test_post_login_vendor_approved_success(client, approved_vendor):
    """POST /login with approved vendor credentials should redirect to vendor dashboard."""
    response = client.post(
        "/login",
        data={
            "role": "vendor",
            "email": approved_vendor.email,
            "password": "password123"
        },
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers.get("location") == "/vendor/dashboard"
    assert "vendor_session" in response.cookies

def test_post_login_vendor_pending_rejected(client, pending_vendor):
    """POST /login with pending vendor credentials should notify that account is pending approval."""
    response = client.post(
        "/login",
        data={
            "role": "vendor",
            "email": pending_vendor.email,
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "pending admin approval" in response.text

def test_post_login_vendor_suspended_rejected(client, suspended_vendor):
    """POST /login with suspended vendor credentials should notify that account is suspended."""
    response = client.post(
        "/login",
        data={
            "role": "vendor",
            "email": suspended_vendor.email,
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "suspended" in response.text

def test_post_login_vendor_invalid_password(client, approved_vendor):
    """POST /login with wrong password should fail."""
    response = client.post(
        "/login",
        data={
            "role": "vendor",
            "email": approved_vendor.email,
            "password": "incorrectpassword"
        }
    )
    assert response.status_code == 200
    assert "Invalid email or password" in response.text

def test_get_register_page(client):
    """GET /register should render the vendor registration form."""
    response = client.get("/register")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

def test_post_register_success(client, db):
    """POST /register should create a new vendor with Pending status."""
    new_email = "newvendor@shopsense.com"
    response = client.post(
        "/register",
        data={
            "full_name": "New Vendor",
            "business_name": "New Ventures Ltd",
            "email": new_email,
            "password": "securepassword123",
            "phone_number": "+1 555-9999",
            "business_address": "456 Enterprise Way"
        }
    )
    assert response.status_code == 200

    # Verify vendor exists in database with status Pending
    vendor = db.query(models.Vendor).filter(models.Vendor.email == new_email).first()
    assert vendor is not None
    assert vendor.status == "Pending"
    assert vendor.business_name == "New Ventures Ltd"

def test_post_register_validation_short_password(client):
    """POST /register with password < 6 characters should fail validation."""
    response = client.post(
        "/register",
        data={
            "full_name": "Short Pass",
            "business_name": "Short Co",
            "email": "shortpass@shopsense.com",
            "password": "123"
        }
    )
    assert response.status_code == 200
    assert "Password must be at least 6 characters" in response.text

def test_post_register_duplicate_email(client, approved_vendor):
    """POST /register with already existing email should be rejected."""
    response = client.post(
        "/register",
        data={
            "full_name": "Duplicate User",
            "business_name": "Duplicate LLC",
            "email": approved_vendor.email,
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "Email is already registered" in response.text

def test_logout(client):
    """GET /logout should clear cookies and redirect to login."""
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers.get("location") == "/login"
