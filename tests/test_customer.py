import pytest
from unittest.mock import patch
import models
from main import hash_password

# -------------------------------------------------------------
# Customer Portal & Authentication Unit Tests
# -------------------------------------------------------------

@pytest.fixture
def registered_customer(db):
    """Pre-seeded customer with email and password for testing."""
    customer = models.Customer(
        name="Alex Morgan",
        email="alex.morgan@example.com",
        password_hash=hash_password("customerpass123"),
        total_spend=150.0
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def test_get_customer_register_page(client):
    """GET /customer/register should serve the customer registration HTML page."""
    response = client.get("/customer/register")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Register as a Customer" in response.text


def test_post_customer_register_success(client, db):
    """POST /customer/register should create a customer, set session, and redirect to portal."""
    new_email = "newcustomer@shopsense.com"
    response = client.post(
        "/customer/register",
        data={
            "full_name": "Test Customer",
            "email": new_email,
            "password": "securepassword123"
        },
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers.get("location") == "/customer/portal"
    assert "customer_session" in response.cookies

    # Verify customer in database
    cust = db.query(models.Customer).filter(models.Customer.email == new_email).first()
    assert cust is not None
    assert cust.name == "Test Customer"
    assert cust.total_spend == 0.0


def test_post_customer_register_short_password(client):
    """POST /customer/register with short password should fail validation."""
    response = client.post(
        "/customer/register",
        data={
            "full_name": "Short Pass User",
            "email": "short@example.com",
            "password": "123"
        }
    )
    assert response.status_code == 200
    assert "Password must be at least 6 characters" in response.text


def test_post_customer_register_duplicate_email(client, registered_customer):
    """POST /customer/register with existing email should show duplicate warning."""
    response = client.post(
        "/customer/register",
        data={
            "full_name": "Duplicate User",
            "email": registered_customer.email,
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "already registered" in response.text.lower()


def test_post_login_customer_success(client, registered_customer):
    """POST /login with role=customer should set customer_session and redirect to portal."""
    response = client.post(
        "/login",
        data={
            "role": "customer",
            "email": registered_customer.email,
            "password": "customerpass123"
        },
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers.get("location") == "/customer/portal"
    assert "customer_session" in response.cookies
    assert response.cookies["customer_session"] == registered_customer.email


def test_post_login_customer_invalid_password(client, registered_customer):
    """POST /login with incorrect customer password should re-render login with error."""
    response = client.post(
        "/login",
        data={
            "role": "customer",
            "email": registered_customer.email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 200
    assert "Invalid customer email or password" in response.text


def test_customer_portal_unauthorized(client):
    """GET /customer/portal without customer_session should redirect to /login."""
    response = client.get("/customer/portal", follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers.get("location")


def test_customer_portal_authorized(client, registered_customer, sample_product):
    """GET /customer/portal with customer_session should render customer portal with catalog."""
    response = client.get(
        "/customer/portal",
        cookies={"customer_session": registered_customer.email}
    )
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert registered_customer.name in response.text
    assert sample_product.name in response.text
    assert "AI Shopping Assistant" in response.text


def test_get_customer_products_api(client, sample_product):
    """GET /customer/api/products should return catalog products JSON."""
    response = client.get("/customer/api/products")
    assert response.status_code == 200
    prods = response.json()
    assert isinstance(prods, list)
    assert any(p["id"] == sample_product.id for p in prods)

    # Test keyword filter
    res_search = client.get("/customer/api/products?q=Headphones")
    assert res_search.status_code == 200
    search_prods = res_search.json()
    assert len(search_prods) >= 1
    assert "Headphones" in search_prods[0]["name"]


def test_customer_shopping_assistant_unauthorized(client):
    """POST /customer/api/shopping-assistant without customer session should return 401."""
    response = client.post(
        "/customer/api/shopping-assistant",
        json={"question": "What is the best laptop for gaming?"}
    )
    assert response.status_code == 401


def test_customer_shopping_assistant_empty_question(client, registered_customer):
    """POST /customer/api/shopping-assistant with empty question should return 400."""
    response = client.post(
        "/customer/api/shopping-assistant",
        json={"question": "   "},
        cookies={"customer_session": registered_customer.email}
    )
    assert response.status_code == 400
    assert "Question cannot be empty" in response.json()["detail"]


def test_customer_shopping_assistant_success_mocked(client, registered_customer, sample_product):
    """POST /customer/api/shopping-assistant with mocked Gemini should return grounded recommendation."""
    mock_nl_answer = f"I recommend the {sample_product.name} at ${sample_product.price:.2f}. This recommendation is based on the products currently available in the catalog."

    with patch("main.call_gemini", return_value=mock_nl_answer):
        response = client.post(
            "/customer/api/shopping-assistant",
            json={"question": "Show me headphones"},
            cookies={"customer_session": registered_customer.email}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert sample_product.name in data["answer"]
        assert len(data["matched_products"]) >= 1
        assert data["matched_products"][0]["name"] == sample_product.name


def test_customer_logout_clears_cookie(client, registered_customer):
    """GET /logout should clear customer_session cookie."""
    response = client.get(
        "/logout",
        cookies={"customer_session": registered_customer.email},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers.get("location") == "/login"


def test_customer_product_detail_page(client, registered_customer, sample_product):
    """GET /customer/product/{product_id} should render product details with stock and price."""
    response = client.get(
        f"/customer/product/{sample_product.id}",
        cookies={"customer_session": registered_customer.email}
    )
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert sample_product.name in response.text
    assert sample_product.category in response.text
    assert f"{sample_product.stock}" in response.text
    assert "Place Order" in response.text


def test_customer_product_detail_not_found(client, registered_customer):
    """GET /customer/product/99999 for non-existent product should return 404."""
    response = client.get(
        "/customer/product/99999",
        cookies={"customer_session": registered_customer.email}
    )
    assert response.status_code == 404


def test_customer_product_detail_unauthorized(client, sample_product):
    """GET /customer/product/{product_id} without customer session should redirect to /login."""
    response = client.get(
        f"/customer/product/{sample_product.id}",
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "/login" in response.headers.get("location", "")


def test_customer_order_placement_success(client, db, registered_customer, sample_product):
    """POST /customer/order/create should create transaction, decrement stock, and update total spend."""
    initial_stock = sample_product.stock
    initial_spend = registered_customer.total_spend
    order_qty = 2
    expected_amount = round(sample_product.price * order_qty, 2)

    response = client.post(
        "/customer/order/create",
        data={
            "product_id": sample_product.id,
            "quantity": order_qty
        },
        cookies={"customer_session": registered_customer.email},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "/customer/order-confirmation/" in response.headers.get("location", "")

    # Verify inventory was decremented in database
    db.refresh(sample_product)
    assert sample_product.stock == initial_stock - order_qty

    # Verify customer spend was updated
    db.refresh(registered_customer)
    assert registered_customer.total_spend == initial_spend + expected_amount

    # Verify transaction record exists
    tx = db.query(models.Transaction).filter(
        models.Transaction.product_id == sample_product.id,
        models.Transaction.quantity == order_qty
    ).first()
    assert tx is not None
    assert tx.amount == expected_amount
    assert tx.vendor_email == sample_product.vendor_email


def test_customer_order_insufficient_stock(client, registered_customer, sample_product):
    """POST /customer/order/create with quantity > stock should return 400."""
    response = client.post(
        "/customer/order/create",
        data={
            "product_id": sample_product.id,
            "quantity": sample_product.stock + 20
        },
        cookies={"customer_session": registered_customer.email}
    )
    assert response.status_code == 400
    assert "Insufficient stock" in response.text


def test_customer_order_zero_quantity(client, registered_customer, sample_product):
    """POST /customer/order/create with quantity <= 0 should return 400."""
    response = client.post(
        "/customer/order/create",
        data={
            "product_id": sample_product.id,
            "quantity": 0
        },
        cookies={"customer_session": registered_customer.email}
    )
    assert response.status_code == 400
    assert "select at least 1 unit" in response.text


def test_customer_order_confirmation_page(client, db, registered_customer, sample_product):
    """GET /customer/order-confirmation/{id} should render confirmation with order summary."""
    tx = models.Transaction(
        vendor_email=sample_product.vendor_email,
        product_id=sample_product.id,
        amount=sample_product.price,
        quantity=1
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    response = client.get(
        f"/customer/order-confirmation/{tx.id}",
        cookies={"customer_session": registered_customer.email}
    )
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Order Placed Successfully" in response.text
    assert f"TXN-{tx.id}" in response.text
    assert sample_product.name in response.text
    assert registered_customer.name in response.text
    assert "Return to Customer Portal" in response.text

