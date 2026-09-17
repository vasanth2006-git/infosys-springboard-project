import sys
import os
import argparse
from datetime import datetime

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"))

import models
from database import SessionLocal
from services.agent_workflow import run_weekly_vendor_analysis, run_all_approved_vendors_analysis


def print_report_summary(result: dict):
    """Prints an executive formatted summary of the agent workflow result."""
    print("\n" + "=" * 65)
    print("      SHOPSENSE AI AGENT WORKFLOW - WEEKLY BUSINESS REPORT      ")
    print("=" * 65)

    if result.get("error"):
        print(f"\n[ERROR] Analysis halted: {result['error']}\n")
        return

    print(f"Vendor Name   : {result.get('vendor_name', 'N/A')}")
    print(f"Business Name : {result.get('business_name', 'N/A')}")
    print(f"Vendor Email  : {result.get('vendor_email', 'N/A')} (Dynamically resolved from MySQL)")
    print(f"Period Window : {result.get('period_start', '')} to {result.get('period_end', '')}")

    metrics = result.get("metrics", {})
    print("\n[KEY PERFORMANCE INDICATORS]")
    print(f"  • Total Sales Revenue  : ${metrics.get('total_revenue', 0.0):,.2f}")
    print(f"  • Total Units Sold     : {metrics.get('units_sold', 0)} units")
    print(f"  • Total Orders         : {metrics.get('order_count', 0)} orders")
    print(f"  • Average Order Value  : ${metrics.get('average_order_value', 0.0):,.2f}")

    top_prods = result.get("top_products", [])
    print("\n[TOP-SELLING PRODUCTS]")
    if top_prods:
        for idx, p in enumerate(top_prods, 1):
            print(f"  {idx}. {p['name']} ({p['category']}) - {p['units_sold']} units | ${p['revenue']:,.2f}")
    else:
        print("  (No top-selling product recorded in period)")

    low_prods = result.get("low_products", [])
    print("\n[LOW-PERFORMING CATALOG PRODUCTS]")
    if low_prods:
        for p in low_prods:
            print(f"  • {p['name']} ({p['category']}) - {p['units_sold']} sold | Stock: {p['stock']} units")
    else:
        print("  (All catalog products recorded healthy sales)")

    alerts = result.get("inventory_alerts", [])
    print("\n[INVENTORY HEALTH ALERTS]")
    if alerts:
        for a in alerts:
            print(f"  ⚠️  {a['name']} - Only {a['stock']} units remaining in stock! (Threshold <= 10)")
    else:
        print("  ✅ All product stock levels are sufficient.")

    print("\n[AI STRATEGIC ADVISOR RECOMMENDATIONS]")
    recs = result.get("recommendations", [])
    for idx, r in enumerate(recs, 1):
        print(f"  {idx}. {r}")

    email_status = result.get("email_status", {})
    print("\n[EMAIL DELIVERY STATUS]")
    print(f"  • Recipient Email  : {email_status.get('recipient', result.get('vendor_email'))}")
    print(f"  • Delivery Channel : {email_status.get('delivery_channel', 'unknown')}")
    print(f"  • Status           : {email_status.get('status', 'unknown').upper()}")
    if email_status.get("archived_path"):
        print(f"  • Audit Copy       : {email_status.get('archived_path')}")
    if email_status.get("message"):
        print(f"  • Details          : {email_status.get('message')}")
    if email_status.get("error"):
        print(f"  • Warning/Error    : {email_status.get('error')}")

    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="ShopSense LangGraph Weekly AI Agent Workflow Runner")
    parser.add_argument("--email", type=str, default=None, help="Target specific vendor email dynamically from MySQL")
    parser.add_argument("--all", action="store_true", help="Run workflow for all approved vendors in MySQL database")

    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.email:
            # Run for specific vendor email
            print(f"[RUNNER] Querying MySQL for vendor: {args.email}...")
            result = run_weekly_vendor_analysis(args.email, db=db)
            print_report_summary(result)

        elif args.all:
            # Run for all approved vendors
            print("[RUNNER] Querying MySQL for all approved vendors...")
            results = run_all_approved_vendors_analysis(db=db)
            for res in results:
                print_report_summary(res)

        else:
            # Default behavior: look up first approved vendor dynamically from MySQL
            approved_vendor = db.query(models.Vendor).filter(models.Vendor.status == "Approved").first()
            if approved_vendor:
                print(f"[RUNNER] No arguments specified. Defaulting to first approved vendor in MySQL: {approved_vendor.email}")
                result = run_weekly_vendor_analysis(approved_vendor.email, db=db)
                print_report_summary(result)
            else:
                print("[RUNNER] No approved vendor found in MySQL. Please register or approve a vendor first.")
                sys.exit(1)

    except Exception as e:
        print(f"[RUNNER ERROR] Failed executing AI Agent Workflow: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
