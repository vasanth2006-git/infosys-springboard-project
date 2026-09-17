import pytest
import models

# -------------------------------------------------------------
# Admin Management API Tests
# -------------------------------------------------------------
def test_approve_vendor_success(client, db, pending_vendor, admin_cookies):
    """POST /admin/vendors/{email}/approve should update vendor status to Approved."""
    response = client.post(
        f"/admin/vendors/{pending_vendor.email}/approve",
        cookies=admin_cookies
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Vendor approved successfully."

    # Verify status in database
    db.refresh(pending_vendor)
    assert pending_vendor.status == "Approved"

def test_approve_vendor_unauthorized(client, pending_vendor):
    """POST /admin/vendors/{email}/approve without admin session should return 401."""
    response = client.post(f"/admin/vendors/{pending_vendor.email}/approve")
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

def test_approve_vendor_not_found(client, admin_cookies):
    """POST /admin/vendors/{email}/approve for non-existent vendor should return 404."""
    response = client.post(
        "/admin/vendors/nonexistent@shopsense.com/approve",
        cookies=admin_cookies
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Vendor not found"

def test_suspend_vendor_success(client, db, approved_vendor, admin_cookies):
    """POST /admin/vendors/{email}/suspend should update vendor status to Suspended."""
    response = client.post(
        f"/admin/vendors/{approved_vendor.email}/suspend",
        cookies=admin_cookies
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Vendor suspended successfully."

    # Verify status in database
    db.refresh(approved_vendor)
    assert approved_vendor.status == "Suspended"

def test_suspend_vendor_unauthorized(client, approved_vendor):
    """POST /admin/vendors/{email}/suspend without admin session should return 401."""
    response = client.post(f"/admin/vendors/{approved_vendor.email}/suspend")
    assert response.status_code == 401

def test_get_admin_customers_success(client, sample_customer, admin_cookies):
    """GET /admin/api/customers should return customer list with behavioral segmentation."""
    response = client.get("/admin/api/customers", cookies=admin_cookies)
    assert response.status_code == 200
    customers = response.json()
    assert isinstance(customers, list)
    assert len(customers) >= 1

    target = next((c for c in customers if c["name"] == sample_customer.name), None)
    assert target is not None
    assert target["total_spend"] == 1250.0
    assert target["segment"] == "Premium Customer"

def test_get_admin_customers_unauthorized(client):
    """GET /admin/api/customers without admin session should return 401."""
    response = client.get("/admin/api/customers")
    assert response.status_code == 401
