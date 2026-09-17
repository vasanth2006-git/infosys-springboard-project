import pytest
import models
from datetime import datetime

# -------------------------------------------------------------
# Analytics & Reports API Tests
# -------------------------------------------------------------
def test_get_sales_trend_daily_success(client, db, approved_vendor, sample_product):
    """GET /vendor/api/sales-trend should return time-series sales aggregation."""
    # Seed a transaction
    tx = models.Transaction(
        vendor_email=approved_vendor.email,
        product_id=sample_product.id,
        amount=149.99,
        quantity=1,
        created_at=datetime.utcnow()
    )
    db.add(tx)
    db.commit()

    response = client.get(
        "/vendor/api/sales-trend?filter_type=daily",
        cookies={"vendor_session": approved_vendor.email}
    )
    assert response.status_code == 200
    data = response.json()
    assert "labels" in data
    assert "data" in data
    assert "label" in data
    assert isinstance(data["labels"], list)
    assert isinstance(data["data"], list)

def test_get_sales_trend_unauthorized(client):
    """GET /vendor/api/sales-trend without vendor session should return 401."""
    response = client.get("/vendor/api/sales-trend?filter_type=daily")
    assert response.status_code == 401

def test_export_csv_success(client, db, approved_vendor, sample_product):
    """GET /vendor/reports/export-csv should stream downloadable sales_report.csv."""
    # Seed a transaction
    tx = models.Transaction(
        vendor_email=approved_vendor.email,
        product_id=sample_product.id,
        amount=299.98,
        quantity=2,
        created_at=datetime.utcnow()
    )
    db.add(tx)
    db.commit()

    response = client.get(
        "/vendor/reports/export-csv",
        cookies={"vendor_session": approved_vendor.email}
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert "sales_report.csv" in response.headers.get("content-disposition", "")
    assert "Transaction ID" in response.text

def test_export_csv_unauthorized(client):
    """GET /vendor/reports/export-csv without vendor session should return 401."""
    response = client.get("/vendor/reports/export-csv")
    assert response.status_code == 401
