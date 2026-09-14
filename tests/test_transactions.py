import pytest
import models

# -------------------------------------------------------------
# Transactions & Order Processing API Tests
# -------------------------------------------------------------
def test_create_transaction_success(client, db, sample_product):
    """POST /api/transactions/create should create transaction and decrement stock."""
    initial_stock = sample_product.stock
    purchase_qty = 2

    response = client.post(
        "/api/transactions/create",
        data={
            "product_id": sample_product.id,
            "quantity": purchase_qty
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["product_id"] == sample_product.id
    assert data["quantity"] == purchase_qty
    assert data["amount"] == round(sample_product.price * purchase_qty, 2)
    assert "transaction_id" in data

    # Verify inventory was decremented in database
    db.refresh(sample_product)
    assert sample_product.stock == initial_stock - purchase_qty

    # Verify transaction record exists
    tx = db.query(models.Transaction).filter(models.Transaction.id == data["transaction_id"]).first()
    assert tx is not None
    assert tx.vendor_email == sample_product.vendor_email
    assert tx.quantity == purchase_qty

def test_create_transaction_insufficient_stock(client, sample_product):
    """POST /api/transactions/create with quantity > stock should return 400."""
    response = client.post(
        "/api/transactions/create",
        data={
            "product_id": sample_product.id,
            "quantity": sample_product.stock + 50
        }
    )
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]

def test_create_transaction_product_not_found(client):
    """POST /api/transactions/create for non-existent product should return 404."""
    response = client.post(
        "/api/transactions/create",
        data={
            "product_id": 99999,
            "quantity": 1
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"
