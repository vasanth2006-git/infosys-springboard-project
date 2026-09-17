import pytest
import models

# -------------------------------------------------------------
# Vendor Catalog & Product API Tests
# -------------------------------------------------------------
def test_add_product_success(client, db, approved_vendor):
    """POST /vendor/products/add should create a product and redirect."""
    response = client.post(
        "/vendor/products/add",
        data={
            "name": "Smart Fitness Band",
            "category": "Electronics",
            "price": 49.99,
            "stock": 40,
            "description": "Heart rate and sleep tracking smart band."
        },
        cookies={"vendor_session": approved_vendor.email},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "status=added" in response.headers.get("location", "")

    # Verify product in database
    product = db.query(models.Product).filter(
        models.Product.name == "Smart Fitness Band",
        models.Product.vendor_email == approved_vendor.email
    ).first()
    assert product is not None
    assert product.price == 49.99
    assert product.stock == 40

def test_add_product_unauthorized(client):
    """POST /vendor/products/add without vendor session should redirect to login."""
    response = client.post(
        "/vendor/products/add",
        data={"name": "Test Item", "category": "General", "price": 10.0, "stock": 5},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "/login" in response.headers.get("location", "")

def test_get_product_detail_success(client, approved_vendor, sample_product):
    """GET /vendor/product/{product_id} should return product JSON detail."""
    response = client.get(
        f"/vendor/product/{sample_product.id}",
        cookies={"vendor_session": approved_vendor.email}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_product.id
    assert data["name"] == sample_product.name
    assert data["price"] == sample_product.price
    assert data["stock"] == sample_product.stock

def test_get_product_detail_not_found(client, approved_vendor):
    """GET /vendor/product/{product_id} for non-existent product should return 404."""
    response = client.get(
        "/vendor/product/99999",
        cookies={"vendor_session": approved_vendor.email}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"

def test_get_product_detail_unauthorized(client, sample_product):
    """GET /vendor/product/{product_id} without vendor session should return 401."""
    response = client.get(f"/vendor/product/{sample_product.id}")
    assert response.status_code == 401

def test_edit_product_success(client, db, approved_vendor, sample_product):
    """POST /vendor/products/edit/{product_id} should update product fields."""
    response = client.post(
        f"/vendor/products/edit/{sample_product.id}",
        data={
            "name": "Pro Wireless Headphones X2 - Updated",
            "category": "Electronics",
            "price": 139.99,
            "stock": 35,
            "description": "Updated active noise cancellation description."
        },
        cookies={"vendor_session": approved_vendor.email},
        follow_redirects=False
    )
    assert response.status_code == 303

    db.refresh(sample_product)
    assert sample_product.name == "Pro Wireless Headphones X2 - Updated"
    assert sample_product.price == 139.99
    assert sample_product.stock == 35

def test_delete_product_success(client, db, approved_vendor, sample_product):
    """POST /vendor/products/delete/{product_id} should delete product from catalog."""
    prod_id = sample_product.id
    response = client.post(
        f"/vendor/products/delete/{prod_id}",
        cookies={"vendor_session": approved_vendor.email}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Product deleted successfully."

    # Verify product is removed from database
    deleted = db.query(models.Product).filter(models.Product.id == prod_id).first()
    assert deleted is None

def test_delete_product_unauthorized(client, sample_product):
    """POST /vendor/products/delete/{product_id} without vendor session should return 401."""
    response = client.post(f"/vendor/products/delete/{sample_product.id}")
    assert response.status_code == 401
