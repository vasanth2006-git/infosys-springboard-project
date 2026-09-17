import os
import re
from datetime import datetime, timedelta
from typing import TypedDict, List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from dotenv import load_dotenv

import models
from database import SessionLocal, get_db
from services.email_service import send_weekly_report_email, render_weekly_report_html

# Load environment configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


# --------------------------------------------------------------------
# 1. LangGraph State Schema Definition
# --------------------------------------------------------------------
class WeeklyAnalysisState(TypedDict, total=False):
    vendor_email: str
    vendor_name: str
    business_name: str
    period_start: str
    period_end: str
    raw_transactions: List[Dict[str, Any]]
    raw_products: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    top_products: List[Dict[str, Any]]
    low_products: List[Dict[str, Any]]
    inventory_alerts: List[Dict[str, Any]]
    ai_insights: str
    recommendations: List[str]
    html_report: str
    email_status: Dict[str, Any]
    error: Optional[str]


# --------------------------------------------------------------------
# 2. Node 1: Dynamic Data Extraction from MySQL
# --------------------------------------------------------------------
def extract_vendor_data(state: WeeklyAnalysisState, db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Connects to MySQL to extract vendor profile, recent 7-day transactions,
    and product catalog with live stock levels.
    """
    # If data was already extracted (e.g. via dependency-injected session in tests or API), reuse it
    if state.get("raw_products") is not None and state.get("raw_transactions") is not None and state.get("vendor_name") is not None:
        return {}

    vendor_email = state.get("vendor_email")
    if not vendor_email:
        return {"error": "No vendor_email specified for analysis"}

    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        # Dynamically query vendor from MySQL
        vendor = db.query(models.Vendor).filter(models.Vendor.email == vendor_email).first()
        if not vendor:
            return {"error": f"Vendor '{vendor_email}' not found in database"}

        now = datetime.utcnow()
        period_start = now - timedelta(days=7)

        # Query vendor's transactions from the past 7 days
        tx_query = db.query(models.Transaction).filter(
            models.Transaction.vendor_email == vendor.email,
            models.Transaction.created_at >= period_start
        ).order_by(models.Transaction.created_at.desc()).all()

        # If 0 transactions in the last 7 days, retrieve recent historical transactions
        # to ensure the AI has real data to provide actionable advice
        if not tx_query:
            tx_query = db.query(models.Transaction).filter(
                models.Transaction.vendor_email == vendor.email
            ).order_by(models.Transaction.created_at.desc()).limit(30).all()

        # Query vendor's products from MySQL
        products = db.query(models.Product).filter(
            models.Product.vendor_email == vendor.email
        ).all()

        raw_txs = [
            {
                "id": t.id,
                "product_id": t.product_id,
                "amount": float(t.amount or 0.0),
                "quantity": int(t.quantity or 1),
                "created_at": t.created_at.isoformat() if t.created_at else ""
            }
            for t in tx_query
        ]

        raw_prods = [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "price": float(p.price or 0.0),
                "stock": int(p.stock or 0),
                "description": p.description or ""
            }
            for p in products
        ]

        return {
            "vendor_name": vendor.full_name,
            "business_name": vendor.business_name,
            "period_start": period_start.strftime("%b %d, %Y"),
            "period_end": now.strftime("%b %d, %Y"),
            "raw_transactions": raw_txs,
            "raw_products": raw_prods,
            "error": None
        }
    finally:
        if session_created:
            db.close()


# --------------------------------------------------------------------
# 2. Node 2: Sales Analytics & Metrics Computation
# --------------------------------------------------------------------
def analyze_sales_metrics(state: WeeklyAnalysisState) -> Dict[str, Any]:
    """
    Computes deterministic financial metrics, product sales aggregations,
    top performers, underperforming items, and inventory risk alerts.
    """
    if state.get("error"):
        return {}

    transactions = state.get("raw_transactions", [])
    products = state.get("raw_products", [])

    total_revenue = sum(t["amount"] for t in transactions)
    units_sold = sum(t["quantity"] for t in transactions)
    order_count = len(transactions)
    aov = round(total_revenue / order_count, 2) if order_count > 0 else 0.0

    # Build product sales lookup
    product_sales = {}
    for p in products:
        product_sales[p["id"]] = {
            "id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "price": p["price"],
            "stock": p["stock"],
            "units_sold": 0,
            "revenue": 0.0
        }

    for t in transactions:
        pid = t.get("product_id")
        if pid and pid in product_sales:
            product_sales[pid]["units_sold"] += t["quantity"]
            product_sales[pid]["revenue"] += t["amount"]

    all_sales_list = list(product_sales.values())

    # Top performing products (sorted by revenue descending)
    top_products = [p for p in all_sales_list if p["units_sold"] > 0]
    top_products.sort(key=lambda x: (x["revenue"], x["units_sold"]), reverse=True)
    top_products = top_products[:3]

    # Low performing products (products with 0 sales or lowest sales)
    low_products = [p for p in all_sales_list if p["units_sold"] == 0]
    if not low_products and len(all_sales_list) > 3:
        # If all products had sales, take the bottom 2 lowest by units
        sorted_asc = sorted(all_sales_list, key=lambda x: x["units_sold"])
        low_products = sorted_asc[:2]

    # Inventory alerts (stock <= 10 units)
    inventory_alerts = [
        {"name": p["name"], "stock": p["stock"], "category": p["category"]}
        for p in products
        if p["stock"] <= 10
    ]

    metrics = {
        "total_revenue": round(total_revenue, 2),
        "units_sold": units_sold,
        "order_count": order_count,
        "average_order_value": aov
    }

    return {
        "metrics": metrics,
        "top_products": top_products,
        "low_products": low_products,
        "inventory_alerts": inventory_alerts
    }


# --------------------------------------------------------------------
# 3. Node 3: Strategic Business Advisor (Gemini AI Synthesis)
# --------------------------------------------------------------------
def generate_ai_advice(state: WeeklyAnalysisState) -> Dict[str, Any]:
    """
    Synthesizes executive performance analysis and 3-4 actionable
    strategic business recommendations using Google Gemini AI.
    """
    if state.get("error"):
        return {}

    metrics = state.get("metrics", {})
    top_prods = state.get("top_products", [])
    low_prods = state.get("low_products", [])
    alerts = state.get("inventory_alerts", [])
    business_name = state.get("business_name", "Vendor Store")

    # Format summaries for the prompt
    top_summary = ", ".join(f"{p['name']} ({p['units_sold']} units, ${p['revenue']:,.2f})" for p in top_prods) or "None"
    low_summary = ", ".join(f"{p['name']} (Stock: {p['stock']} units)" for p in low_prods) or "None"
    alert_summary = ", ".join(f"{a['name']} ({a['stock']} units remaining)" for a in alerts) or "All inventory levels sufficient"

    prompt = f"""You are the ShopSense Senior E-Commerce Business Advisor.
Analyze the following actual weekly sales and inventory data for '{business_name}' and provide strategic executive advice.

Weekly Performance Data:
- Total Revenue: ${metrics.get('total_revenue', 0):,.2f}
- Units Sold: {metrics.get('units_sold', 0)}
- Total Orders: {metrics.get('order_count', 0)}
- Average Order Value (AOV): ${metrics.get('average_order_value', 0):,.2f}
- Top-Selling Products: {top_summary}
- Low-Performing Products: {low_summary}
- Inventory Stock Alerts: {alert_summary}

Instructions:
1. Provide a concise 2-paragraph Executive Performance Summary explaining revenue velocity, top driver products, and inventory risks.
2. Provide exactly 3 actionable, numbered recommendations formatted as:
   1. [Action title]: [Specific tactical advice on pricing, bundling, restock, or marketing]
   2. [Action title]: [Specific tactical advice]
   3. [Action title]: [Specific tactical advice]

Ensure all numbers directly align with the provided data. Do not hallucinate external products. Keep the tone professional, motivating, and actionable.
"""

    ai_response = ""
    try:
        from main import call_gemini
        ai_response = call_gemini(prompt).strip()
    except Exception as e:
        print(f"[AI AGENT] Gemini API call fallback triggered: {e}")
        # Deterministic fallback advice based on real calculated metrics
        ai_response = f"""{business_name} achieved a total revenue of ${metrics.get('total_revenue', 0.0):,.2f} across {metrics.get('order_count', 0)} customer orders this week, averaging ${metrics.get('average_order_value', 0.0):,.2f} per order. Sales performance was anchored primarily by top-selling catalog items, demonstrating healthy customer interest in core offerings.

However, inventory velocity requires strategic balance. Products with limited traction should be paired with higher-performing items to accelerate stock turnover and preserve working capital.

1. Cross-Product Bundling: Bundle low-moving inventory items with your top seller ({top_prods[0]['name'] if top_prods else 'core catalog'}) at an attractive 10-15% discount to increase basket size.
2. Proactive Inventory Restocking: Immediately replenish inventory for critical stock-alert products ({alerts[0]['name'] if alerts else 'fast movers'}) to prevent stockouts and missed revenue.
3. Promotional Campaign Launch: Introduce a limited-time flash promotion on underperforming catalog items to stimulate initial review generation and improve search ranking.
"""

    # Extract 3 numbered recommendations from text
    recommendations = []
    lines = ai_response.splitlines()
    for line in lines:
        line_clean = line.strip()
        if re.match(r"^\d+\.\s+", line_clean):
            # Strip number prefix
            rec_text = re.sub(r"^\d+\.\s+", "", line_clean)
            recommendations.append(rec_text)

    if not recommendations:
        recommendations = [
            f"Cross-sell top performer '{top_prods[0]['name'] if top_prods else 'flagship products'}' with complementary catalog accessories to drive up AOV.",
            "Replenish inventory promptly for products nearing minimum safety stock thresholds.",
            "Run a targeted weekend promotional flash sale on zero-sales catalog listings to spur conversion."
        ]

    return {
        "ai_insights": ai_response,
        "recommendations": recommendations[:4]
    }


# --------------------------------------------------------------------
# 4. Node 4: Executive HTML Compilation & SMTP Email Dispatch
# --------------------------------------------------------------------
def dispatch_email_report(state: WeeklyAnalysisState) -> Dict[str, Any]:
    """
    Renders the executive HTML report and dispatches it directly to the
    vendor's registered email address via SMTP (or fallback archive).
    """
    if state.get("error"):
        return {"email_status": {"status": "skipped", "reason": state["error"]}}

    vendor_email = state.get("vendor_email")
    vendor_name = state.get("vendor_name", "Vendor")
    business_name = state.get("business_name", "ShopSense Store")
    period_start = state.get("period_start", "")
    period_end = state.get("period_end", "")
    metrics = state.get("metrics", {})
    top_products = state.get("top_products", [])
    low_products = state.get("low_products", [])
    inventory_alerts = state.get("inventory_alerts", [])
    ai_insights = state.get("ai_insights", "")
    recommendations = state.get("recommendations", [])

    # Compile executive HTML email template
    html_content = render_weekly_report_html(
        vendor_name=vendor_name,
        business_name=business_name,
        period_start=period_start,
        period_end=period_end,
        metrics=metrics,
        top_products=top_products,
        low_products=low_products,
        inventory_alerts=inventory_alerts,
        ai_insights=ai_insights,
        recommendations=recommendations
    )

    # Compile plain text fallback
    plain_text = f"""ShopSense Weekly Business Report: {business_name}
Period: {period_start} - {period_end}

Metrics Overview:
- Total Revenue: ${metrics.get('total_revenue', 0):,.2f}
- Units Sold: {metrics.get('units_sold', 0)}
- Orders: {metrics.get('order_count', 0)}
- Average Order Value: ${metrics.get('average_order_value', 0):,.2f}

AI Strategic Insights:
{ai_insights}

Actionable Recommendations:
""" + "\n".join(f"- {r}" for r in recommendations)

    subject = f"ShopSense Weekly Business Report & AI Insights - {business_name}"

    # Transmit via SMTP to the vendor's actual registered email
    delivery_result = send_weekly_report_email(
        to_email=vendor_email,
        subject=subject,
        html_content=html_content,
        text_content=plain_text
    )

    return {
        "html_report": html_content,
        "email_status": delivery_result
    }


# --------------------------------------------------------------------
# 5. LangGraph StateGraph Construction
# --------------------------------------------------------------------
def build_agent_graph():
    """
    Constructs and compiles the LangGraph StateGraph workflow.
    Uses langgraph if installed; otherwise provides a lightweight
    deterministic StateGraph execution runner with identical interfaces.
    """
    try:
        from langgraph.graph import StateGraph, END
        workflow = StateGraph(WeeklyAnalysisState)

        # Register Agent Nodes
        workflow.add_node("extract_data", extract_vendor_data)
        workflow.add_node("analyze_metrics", analyze_sales_metrics)
        workflow.add_node("generate_advice", generate_ai_advice)
        workflow.add_node("dispatch_report", dispatch_email_report)

        # Define Deterministic Flow
        workflow.set_entry_point("extract_data")
        workflow.add_edge("extract_data", "analyze_metrics")
        workflow.add_edge("analyze_metrics", "generate_advice")
        workflow.add_edge("generate_advice", "dispatch_report")
        workflow.add_edge("dispatch_report", END)

        return workflow.compile()
    except Exception as e:
        print(f"[LANGGRAPH] Notice: Operating in direct graph runner mode ({e})")

        # Deterministic StateGraph Runner Fallback
        class FallbackGraphApp:
            def invoke(self, initial_state: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
                state = dict(initial_state)

                # Step 1: Data Extraction
                n1_out = extract_vendor_data(state)
                state.update(n1_out)
                if state.get("error"):
                    return state

                # Step 2: Analytics
                n2_out = analyze_sales_metrics(state)
                state.update(n2_out)

                # Step 3: AI Advice
                n3_out = generate_ai_advice(state)
                state.update(n3_out)

                # Step 4: Dispatch
                n4_out = dispatch_email_report(state)
                state.update(n4_out)

                return state

        return FallbackGraphApp()


# Compile global workflow runner
agent_workflow_app = build_agent_graph()


# --------------------------------------------------------------------
# 6. High-Level Invocation Functions
# --------------------------------------------------------------------
def run_weekly_vendor_analysis(vendor_email: str, db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Executes the complete LangGraph AI Agent Workflow for a single vendor.
    The vendor's registered email address is dynamically resolved and used.
    """
    initial_state = {
        "vendor_email": vendor_email
    }

    # If an active DB session is supplied (e.g. from FastAPI dependency), pass it to extract node
    if db is not None:
        extracted = extract_vendor_data(initial_state, db=db)
        initial_state.update(extracted)

    final_state = agent_workflow_app.invoke(initial_state)
    return final_state


def run_all_approved_vendors_analysis(db: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    Executes the LangGraph AI Agent Workflow for ALL approved vendors dynamically
    retrieved from the MySQL database.
    """
    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    results = []
    try:
        # Dynamically query all approved vendors from MySQL
        approved_vendors = db.query(models.Vendor).filter(models.Vendor.status == "Approved").all()
        print(f"[AI WORKFLOW] Found {len(approved_vendors)} approved vendor(s) in MySQL database.")

        for vendor in approved_vendors:
            print(f"[AI WORKFLOW] Processing weekly report for: {vendor.full_name} ({vendor.email})...")
            res = run_weekly_vendor_analysis(vendor.email, db=db)
            results.append(res)

        return results
    finally:
        if session_created:
            db.close()
