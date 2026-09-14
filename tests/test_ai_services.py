import pytest
from unittest.mock import patch

# -------------------------------------------------------------
# AI Services Unit Tests (AI Data Analyst & Shopping Assistant)
# -------------------------------------------------------------
def test_ai_query_empty_question(client, approved_vendor):
    """POST /vendor/api/ai-query with empty question should return 400."""
    response = client.post(
        "/vendor/api/ai-query",
        json={"question": "   "},
        cookies={"vendor_session": approved_vendor.email}
    )
    assert response.status_code == 400
    assert "Question cannot be empty" in response.json()["detail"]

def test_ai_query_unauthorized(client):
    """POST /vendor/api/ai-query without vendor session should return 401."""
    response = client.post(
        "/vendor/api/ai-query",
        json={"question": "What were my sales?"}
    )
    assert response.status_code == 401

def test_ai_query_success_mocked(client, approved_vendor):
    """POST /vendor/api/ai-query with mocked Gemini call should return structured insight."""
    mock_sql = f"SELECT id, amount, quantity FROM transactions WHERE vendor_email = '{approved_vendor.email}'"
    mock_nl_answer = "Your sales total is steady across current recorded transactions."

    with patch("main.call_gemini", side_effect=[mock_sql, mock_nl_answer]):
        response = client.post(
            "/vendor/api/ai-query",
            json={"question": "Show my transactions"},
            cookies={"vendor_session": approved_vendor.email}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "answer" in data
        assert "sql" in data

def test_shopping_assistant_empty_question(client, approved_vendor):
    """POST /vendor/api/shopping-assistant with empty question should return 400."""
    response = client.post(
        "/vendor/api/shopping-assistant",
        json={"question": "  "},
        cookies={"vendor_session": approved_vendor.email}
    )
    assert response.status_code == 400
    assert "Question cannot be empty" in response.json()["detail"]

def test_shopping_assistant_unauthorized(client):
    """POST /vendor/api/shopping-assistant without vendor session should return 401."""
    response = client.post(
        "/vendor/api/shopping-assistant",
        json={"question": "Find wireless headphones"}
    )
    assert response.status_code == 401

def test_shopping_assistant_success_mocked(client, approved_vendor, sample_product):
    """POST /vendor/api/shopping-assistant with matching product and mocked Gemini."""
    mock_nl_answer = "I recommend the Pro Wireless Headphones X2 at ₹149.99 for high-fidelity audio."

    with patch("main.call_gemini", return_value=mock_nl_answer):
        response = client.post(
            "/vendor/api/shopping-assistant",
            json={"question": "headphones"},
            cookies={"vendor_session": approved_vendor.email}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "answer" in data
        assert len(data["matched_products"]) >= 1
        assert data["matched_products"][0]["name"] == sample_product.name
