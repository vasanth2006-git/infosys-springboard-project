import pytest

# -------------------------------------------------------------
# API Documentation & OpenAPI Specification Tests
# -------------------------------------------------------------
def test_swagger_ui_available(client):
    """GET /docs should serve the interactive Swagger UI."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "swagger" in response.text.lower()

def test_redoc_available(client):
    """GET /redoc should serve the ReDoc interactive documentation."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "redoc" in response.text.lower()

def test_openapi_json_schema(client):
    """GET /openapi.json should return valid OpenAPI schema with ShopSense metadata."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()

    # Verify root OpenAPI metadata
    assert "openapi" in data
    assert data["info"]["title"] == "ShopSense Marketplace Portal API"
    assert data["info"]["version"] == "1.0.0"

    # Verify key paths are documented
    paths = data.get("paths", {})
    assert "/login" in paths
    assert "/register" in paths
    assert "/logout" in paths
    assert "/admin/api/customers" in paths
    assert "/vendor/api/sales-trend" in paths
    assert "/vendor/api/ai-query" in paths
    assert "/vendor/api/shopping-assistant" in paths
    assert "/api/transactions/create" in paths

    # Verify tags are properly configured
    tags = [tag["name"] for tag in data.get("tags", [])]
    assert "Authentication & Onboarding" in tags
    assert "Admin Management" in tags
    assert "Vendor Dashboard & Catalog" in tags
    assert "Analytics & Reports" in tags
    assert "AI Services" in tags
