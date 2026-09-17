import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

import models
from services.agent_workflow import (
    extract_vendor_data,
    analyze_sales_metrics,
    generate_ai_advice,
    dispatch_email_report,
    run_weekly_vendor_analysis,
    build_agent_graph
)


# -------------------------------------------------------------
# Node 1: Data Extraction Unit Tests
# -------------------------------------------------------------
def test_extract_vendor_data_success(db, approved_vendor, sample_product):
    """extract_vendor_data should dynamically query MySQL/DB for vendor profile and catalog."""
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

    state = {"vendor_email": approved_vendor.email}
    result = extract_vendor_data(state, db=db)

    assert result.get("error") is None
    assert result["vendor_name"] == approved_vendor.full_name
    assert result["business_name"] == approved_vendor.business_name
    assert len(result["raw_products"]) >= 1
    assert len(result["raw_transactions"]) >= 1


def test_extract_vendor_data_not_found(db):
    """extract_vendor_data with non-existent vendor should return error in state."""
    state = {"vendor_email": "nonexistent_vendor@shopsense.com"}
    result = extract_vendor_data(state, db=db)

    assert result.get("error") is not None
    assert "not found" in result["error"].lower()


# -------------------------------------------------------------
# Node 2: Analytics & Metrics Unit Tests
# -------------------------------------------------------------
def test_analyze_sales_metrics():
    """analyze_sales_metrics should accurately compute revenue, units, AOV, top/low items, and stock alerts."""
    state = {
        "raw_products": [
            {"id": 1, "name": "Wireless Headphones", "category": "Electronics", "price": 100.0, "stock": 5},
            {"id": 2, "name": "USB Cable", "category": "Accessories", "price": 15.0, "stock": 50},
            {"id": 3, "name": "Laptop Stand", "category": "Office", "price": 40.0, "stock": 20}
        ],
        "raw_transactions": [
            {"id": 101, "product_id": 1, "amount": 200.0, "quantity": 2},
            {"id": 102, "product_id": 1, "amount": 100.0, "quantity": 1},
            {"id": 103, "product_id": 2, "amount": 30.0, "quantity": 2}
        ]
    }

    result = analyze_sales_metrics(state)
    metrics = result["metrics"]

    # Assert accurate mathematical totals
    assert metrics["total_revenue"] == 330.0
    assert metrics["units_sold"] == 5
    assert metrics["order_count"] == 3
    assert metrics["average_order_value"] == 110.0

    # Top product should be Wireless Headphones ($300 revenue)
    assert len(result["top_products"]) >= 1
    assert result["top_products"][0]["name"] == "Wireless Headphones"
    assert result["top_products"][0]["revenue"] == 300.0

    # Low product should be Laptop Stand (0 sales)
    assert len(result["low_products"]) >= 1
    assert any(p["name"] == "Laptop Stand" for p in result["low_products"])

    # Inventory alert should trigger for Wireless Headphones (stock = 5 <= 10)
    assert len(result["inventory_alerts"]) == 1
    assert result["inventory_alerts"][0]["name"] == "Wireless Headphones"


# -------------------------------------------------------------
# Node 3: AI Advisor Advice Generation (Mocked Gemini)
# -------------------------------------------------------------
def test_generate_ai_advice_mocked():
    """generate_ai_advice should formulate strategic insights and numbered recommendations."""
    mock_llm_response = """Apex Retail Co demonstrated steady revenue this week driven primarily by customer demand for audio equipment.
However, inventory levels for flagship products require immediate attention to prevent stockouts.

1. Product Bundling Strategy: Bundle Wireless Headphones with USB cables at a 10% discount to lift order value.
2. Immediate Inventory Restock: Replenish stock for low-inventory electronics within 48 hours.
3. Flash Promotion Campaign: Run a targeted promotion on slow-moving inventory to improve cash flow.
"""
    state = {
        "business_name": "Apex Retail Co",
        "metrics": {"total_revenue": 330.0, "units_sold": 5, "order_count": 3, "average_order_value": 110.0},
        "top_products": [{"name": "Wireless Headphones", "units_sold": 3, "revenue": 300.0}],
        "low_products": [{"name": "Laptop Stand", "stock": 20}],
        "inventory_alerts": [{"name": "Wireless Headphones", "stock": 5}]
    }

    with patch("main.call_gemini", return_value=mock_llm_response):
        result = generate_ai_advice(state)

        assert "Apex Retail Co" in result["ai_insights"]
        assert len(result["recommendations"]) == 3
        assert "Product Bundling Strategy" in result["recommendations"][0]


# -------------------------------------------------------------
# Node 4: Email Dispatch & HTML Rendering
# -------------------------------------------------------------
def test_dispatch_email_report_simulated():
    """dispatch_email_report should render HTML report and archive to reports/ in simulation fallback."""
    state = {
        "vendor_email": "test_vendor@shopsense.com",
        "vendor_name": "Alice Johnson",
        "business_name": "Apex Retail Co",
        "period_start": "Sep 08, 2026",
        "period_end": "Sep 15, 2026",
        "metrics": {"total_revenue": 500.0, "units_sold": 5, "order_count": 3, "average_order_value": 166.67},
        "top_products": [{"name": "Wireless Headphones", "category": "Electronics", "units_sold": 3, "revenue": 300.0}],
        "low_products": [{"name": "Laptop Stand", "category": "Office", "units_sold": 0, "stock": 20}],
        "inventory_alerts": [{"name": "Wireless Headphones", "stock": 5}],
        "ai_insights": "Strong sales performance across core product lines.",
        "recommendations": ["Bundle accessories with top sellers", "Restock headphones"]
    }

    result = dispatch_email_report(state)

    assert "html_report" in result
    assert "Apex Retail Co" in result["html_report"]
    assert "$500.00" in result["html_report"]
    assert result["email_status"]["recipient"] == "test_vendor@shopsense.com"
    assert result["email_status"]["status"] in ("sent", "simulated")


# -------------------------------------------------------------
# Node 5: Full LangGraph End-to-End Workflow Execution
# -------------------------------------------------------------
def test_full_agent_workflow_execution(db, approved_vendor, sample_product):
    """run_weekly_vendor_analysis should execute the entire LangGraph workflow end-to-end."""
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

    mock_llm_response = """Your weekly performance was steady with strong headphone revenue.

1. Promote Top Seller: Maintain front-page placement for flagship headphones.
2. Restock Low Inventory: Order replenishments for fast-moving items.
3. Optimize Product Listings: Refresh photography and keywords on secondary listings.
"""
    with patch("main.call_gemini", return_value=mock_llm_response):
        final_state = run_weekly_vendor_analysis(approved_vendor.email, db=db)

        assert final_state.get("error") is None
        assert final_state["vendor_email"] == approved_vendor.email
        assert final_state["metrics"]["total_revenue"] == 299.98
        assert final_state["metrics"]["units_sold"] == 2
        assert "html_report" in final_state
        assert "email_status" in final_state


# -------------------------------------------------------------
# API Route: POST /vendor/api/weekly-report/generate
# -------------------------------------------------------------
def test_api_generate_weekly_report_success(client, db, approved_vendor, sample_product):
    """POST /vendor/api/weekly-report/generate should invoke workflow and return WeeklyReportResponse."""
    mock_advice = """Sales for Apex Retail were consistent.

1. Cross-sell accessories with primary items.
2. Maintain adequate safety stock for popular products.
3. Run weekend promotional discounts on slow inventory.
"""
    with patch("main.call_gemini", return_value=mock_advice):
        response = client.post(
            "/vendor/api/weekly-report/generate",
            cookies={"vendor_session": approved_vendor.email}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["vendor_email"] == approved_vendor.email
        assert data["business_name"] == approved_vendor.business_name
        assert "metrics" in data
        assert "ai_insights" in data
        assert "email_status" in data


def test_api_generate_weekly_report_unauthorized(client):
    """POST /vendor/api/weekly-report/generate without session cookie should return 401."""
    response = client.post("/vendor/api/weekly-report/generate")
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"
