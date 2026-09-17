import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv

# Ensure environment variables are loaded
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def send_weekly_report_email(to_email: str, subject: str, html_content: str, text_content: str = "") -> dict:
    """
    Dispatches the weekly vendor performance report.
    - If SMTP credentials (SMTP_HOST, SMTP_USER) are configured in .env, transmits real email via SMTP.
    - If SMTP credentials are not configured, executes safe fallback by archiving to reports/ directory.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = "".join(c for c in to_email if c.isalnum() or c in "._-")
    archived_file_path = os.path.join(REPORTS_DIR, f"{safe_filename}_weekly_report_{timestamp}.html")

    # Always archive a local copy of the HTML report for audit and verification
    try:
        with open(archived_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception as e:
        print(f"[EMAIL SERVICE] Warning: Could not write archive report: {e}")

    # Read SMTP configuration from environment variables
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_tls = os.getenv("SMTP_USE_TLS", "True").lower() in ("true", "1", "yes")
    email_from = os.getenv("EMAIL_FROM", smtp_user or "reports@shopsense.com").strip()

    # Check if real SMTP delivery is configured
    if not smtp_host or not smtp_user:
        print(f"[EMAIL SERVICE] SMTP not configured in .env. Safe fallback: Report archived to {archived_file_path}")
        return {
            "status": "simulated",
            "recipient": to_email,
            "subject": subject,
            "delivery_channel": "local_archive",
            "archived_path": archived_file_path,
            "message": "SMTP credentials not configured in .env. Report compiled and saved for audit."
        }

    # Construct MIME multipart email message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = email_from
    message["To"] = to_email

    if text_content:
        message.attach(MIMEText(text_content, "plain", "utf-8"))
    message.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        if smtp_port == 465:
            # SSL Connection
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=25)
        else:
            # Standard connection with optional STARTTLS
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=25)
            if smtp_tls:
                server.starttls()

        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)

        server.sendmail(email_from, [to_email], message.as_string())
        server.quit()

        print(f"[EMAIL SERVICE] Successfully sent weekly report to registered email: {to_email}")
        return {
            "status": "sent",
            "recipient": to_email,
            "subject": subject,
            "delivery_channel": "smtp",
            "archived_path": archived_file_path,
            "message": f"Weekly report successfully transmitted via SMTP to {to_email}"
        }

    except Exception as e:
        err_msg = f"SMTP delivery failed: {str(e)}"
        print(f"[EMAIL SERVICE] {err_msg}. Report archived to {archived_file_path}")
        return {
            "status": "failed",
            "recipient": to_email,
            "subject": subject,
            "delivery_channel": "smtp_error_fallback",
            "archived_path": archived_file_path,
            "error": err_msg
        }


def render_weekly_report_html(
    vendor_name: str,
    business_name: str,
    period_start: str,
    period_end: str,
    metrics: dict,
    top_products: list,
    low_products: list,
    inventory_alerts: list,
    ai_insights: str,
    recommendations: list
) -> str:
    """
    Renders a responsive, executive-styled HTML email template for the weekly vendor report.
    """
    total_rev = metrics.get("total_revenue", 0.0)
    units_sold = metrics.get("units_sold", 0)
    order_count = metrics.get("order_count", 0)
    aov = metrics.get("average_order_value", 0.0)

    # Top products table rows
    top_rows = ""
    if top_products:
        for idx, p in enumerate(top_products, 1):
            top_rows += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px; font-weight: bold; color: #4a5568;">#{idx}</td>
                <td style="padding: 10px; color: #2d3748;">{p.get('name', 'N/A')}</td>
                <td style="padding: 10px; color: #718096;">{p.get('category', 'General')}</td>
                <td style="padding: 10px; text-align: center; color: #2d3748; font-weight: 600;">{p.get('units_sold', 0)}</td>
                <td style="padding: 10px; text-align: right; color: #2b6cb0; font-weight: bold;">${p.get('revenue', 0.0):,.2f}</td>
            </tr>
            """
    else:
        top_rows = '<tr><td colspan="5" style="padding: 12px; text-align: center; color: #a0aec0;">No top products recorded this week.</td></tr>'

    # Low products table rows
    low_rows = ""
    if low_products:
        for p in low_products:
            low_rows += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px; color: #2d3748;">{p.get('name', 'N/A')}</td>
                <td style="padding: 10px; color: #718096;">{p.get('category', 'General')}</td>
                <td style="padding: 10px; text-align: center; color: #e53e3e; font-weight: 600;">{p.get('units_sold', 0)} sold</td>
                <td style="padding: 10px; text-align: right; color: #718096;">{p.get('stock', 0)} in stock</td>
            </tr>
            """
    else:
        low_rows = '<tr><td colspan="4" style="padding: 12px; text-align: center; color: #a0aec0;">All listed products recorded active sales.</td></tr>'

    # Inventory alerts HTML
    alerts_html = ""
    if inventory_alerts:
        for alert in inventory_alerts:
            alerts_html += f"""
            <div style="background-color: #fffaf0; border-left: 4px solid #dd6b20; padding: 10px 14px; margin-bottom: 8px; border-radius: 4px; font-size: 14px; color: #7b341e;">
                <strong>⚠️ {alert.get('name')}:</strong> Only {alert.get('stock')} units left in stock! (Threshold: &le;10 units)
            </div>
            """
    else:
        alerts_html = '<p style="color: #38a169; font-size: 14px; margin: 0;">✅ All catalog inventory levels are healthy.</p>'

    # Recommendations HTML list
    rec_html = ""
    if recommendations:
        for idx, rec in enumerate(recommendations, 1):
            rec_html += f"""
            <li style="margin-bottom: 10px; color: #2d3748; line-height: 1.5;">
                <strong>Recommendation {idx}:</strong> {rec}
            </li>
            """
    else:
        rec_html = '<li style="color: #718096;">Maintain current pricing and inventory velocity.</li>'

    # Clean formatted paragraphs for AI insights
    insights_paragraphs = "".join(f"<p style='margin: 0 0 10px 0; line-height: 1.6; color: #2d3748;'>{para.strip()}</p>" for para in ai_insights.split("\n") if para.strip())

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>ShopSense Weekly Vendor Report</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f7fafc; margin: 0; padding: 20px;">
        <div style="max-width: 680px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #e2e8f0;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #3182ce 0%, #2b6cb0 100%); padding: 24px; color: #ffffff;">
                <h1 style="margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">ShopSense Marketplace</h1>
                <p style="margin: 6px 0 0 0; opacity: 0.9; font-size: 14px;">Weekly Business Performance & AI Strategic Insights</p>
            </div>

            <div style="padding: 24px;">
                <!-- Greeting & Overview -->
                <div style="margin-bottom: 20px;">
                    <h2 style="font-size: 18px; color: #2d3748; margin: 0 0 6px 0;">Hello {vendor_name} ({business_name}),</h2>
                    <p style="color: #718096; font-size: 14px; margin: 0;">Here is your automated weekly business analysis for <strong>{period_start}</strong> to <strong>{period_end}</strong>.</p>
                </div>

                <!-- KPI Metric Cards Grid -->
                <table style="width: 100%; border-collapse: separate; border-spacing: 10px 0; margin-bottom: 24px;">
                    <tr>
                        <td style="width: 25%; background-color: #ebf8ff; border-radius: 6px; padding: 14px; text-align: center; border: 1px solid #bee3f8;">
                            <div style="font-size: 11px; text-transform: uppercase; color: #2b6cb0; font-weight: 700;">Revenue</div>
                            <div style="font-size: 18px; font-weight: 800; color: #2b6cb0; margin-top: 4px;">${total_rev:,.2f}</div>
                        </td>
                        <td style="width: 25%; background-color: #f0fff4; border-radius: 6px; padding: 14px; text-align: center; border: 1px solid #c6f6d5;">
                            <div style="font-size: 11px; text-transform: uppercase; color: #22543d; font-weight: 700;">Units Sold</div>
                            <div style="font-size: 18px; font-weight: 800; color: #22543d; margin-top: 4px;">{units_sold}</div>
                        </td>
                        <td style="width: 25%; background-color: #faf5ff; border-radius: 6px; padding: 14px; text-align: center; border: 1px solid #e9d8fd;">
                            <div style="font-size: 11px; text-transform: uppercase; color: #553c9e; font-weight: 700;">Orders</div>
                            <div style="font-size: 18px; font-weight: 800; color: #553c9e; margin-top: 4px;">{order_count}</div>
                        </td>
                        <td style="width: 25%; background-color: #fffaf0; border-radius: 6px; padding: 14px; text-align: center; border: 1px solid #feebc8;">
                            <div style="font-size: 11px; text-transform: uppercase; color: #7b341e; font-weight: 700;">Avg Order</div>
                            <div style="font-size: 18px; font-weight: 800; color: #7b341e; margin-top: 4px;">${aov:,.2f}</div>
                        </td>
                    </tr>
                </table>

                <!-- Top Products Section -->
                <div style="margin-bottom: 24px;">
                    <h3 style="font-size: 16px; color: #2d3748; margin: 0 0 10px 0; border-bottom: 2px solid #edf2f7; padding-bottom: 6px;">🏆 Top Performing Products</h3>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <thead>
                            <tr style="background-color: #edf2f7; color: #4a5568; text-align: left;">
                                <th style="padding: 8px 10px;">Rank</th>
                                <th style="padding: 8px 10px;">Product</th>
                                <th style="padding: 8px 10px;">Category</th>
                                <th style="padding: 8px 10px; text-align: center;">Units</th>
                                <th style="padding: 8px 10px; text-align: right;">Sales</th>
                            </tr>
                        </thead>
                        <tbody>
                            {top_rows}
                        </tbody>
                    </table>
                </div>

                <!-- Underperforming Products Section -->
                <div style="margin-bottom: 24px;">
                    <h3 style="font-size: 16px; color: #2d3748; margin: 0 0 10px 0; border-bottom: 2px solid #edf2f7; padding-bottom: 6px;">📉 Low-Performing Catalog Products</h3>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <thead>
                            <tr style="background-color: #edf2f7; color: #4a5568; text-align: left;">
                                <th style="padding: 8px 10px;">Product</th>
                                <th style="padding: 8px 10px;">Category</th>
                                <th style="padding: 8px 10px; text-align: center;">Sales This Week</th>
                                <th style="padding: 8px 10px; text-align: right;">Current Stock</th>
                            </tr>
                        </thead>
                        <tbody>
                            {low_rows}
                        </tbody>
                    </table>
                </div>

                <!-- Inventory Health Alerts -->
                <div style="margin-bottom: 24px;">
                    <h3 style="font-size: 16px; color: #2d3748; margin: 0 0 10px 0; border-bottom: 2px solid #edf2f7; padding-bottom: 6px;">📦 Inventory Health & Restock Alerts</h3>
                    {alerts_html}
                </div>

                <!-- AI Strategic Business Advisor Section -->
                <div style="background-color: #f7fafc; border: 1px solid #cbd5e0; border-radius: 6px; padding: 18px; margin-bottom: 20px;">
                    <h3 style="font-size: 16px; color: #2b6cb0; margin: 0 0 12px 0; display: flex; align-items: center;">
                        🤖 ShopSense AI Strategic Advisor Insights
                    </h3>
                    <div style="font-size: 14px;">
                        {insights_paragraphs}
                    </div>

                    <h4 style="font-size: 14px; color: #2d3748; margin: 16px 0 8px 0; text-transform: uppercase; letter-spacing: 0.5px;">Actionable Business Recommendations</h4>
                    <ol style="margin: 0; padding-left: 20px; font-size: 14px;">
                        {rec_html}
                    </ol>
                </div>

                <!-- Footer -->
                <div style="border-top: 1px solid #e2e8f0; padding-top: 14px; text-align: center; color: #a0aec0; font-size: 12px;">
                    <p style="margin: 0 0 4px 0;">This weekly report was automatically generated and delivered by the ShopSense AI Agent Workflow.</p>
                    <p style="margin: 0;">ShopSense Marketplace &copy; 2026. All rights reserved.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_template
