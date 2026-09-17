# ShopSense Cloud Deployment Guide (Vercel)

This guide provides step-by-step instructions to deploy the existing **ShopSense** FastAPI application to **Vercel** with a free, persistent **Cloud MySQL** database.

---

## 1. Architecture Overview

```
ShopSense Codebase (GitHub)
       │
       ▼
Vercel Serverless Platform (@vercel/python runtime via api/index.py)
       │
       ├─► Public HTTPS URL: https://<project-name>.vercel.app
       ├─► Jinja2 SSR Templates & Static Files
       ├─► Interactive Swagger UI API Docs (/docs)
       ├─► Multi-role Auth (Admin & Vendor session cookies)
       └─► AI Services (Gemini Data Analyst & RAG Shopping Assistant)
       │
       ▼
Cloud MySQL Database (TiDB Cloud Serverless / Aiven / AWS RDS)
       │
       ├─► Auto-initialized tables (Base.metadata.create_all)
       └─► Auto-seeded baseline vendors, customers, products, and orders
```

---

## 2. Step 1: Set Up Free Cloud MySQL (60 Seconds)

Vercel functions execute in the cloud and cannot connect to your computer's `localhost:3306`. You need a free cloud-hosted MySQL database:

### Recommended: TiDB Cloud Serverless (Free Forever, No Credit Card)
1. Go to [TiDB Cloud](https://tidbcloud.com/) and sign in with GitHub or Google.
2. Click **Create Cluster** and choose **Serverless (Free)**.
3. Once provisioned (~20 seconds), click **Connect**.
4. Copy your connection parameters:
   - **Host**: e.g., `gateway01.us-east-1.prod.aws.tidbcloud.com`
   - **Port**: `4000`
   - **User**: e.g., `2XxX...root`
   - **Password**: Your cluster password
   - **Database**: `test` (or create `shopsense_new_db`)
   - **SSL**: `true`

*(Alternative: You can use [Aiven for MySQL](https://aiven.io/), [Clever Cloud](https://www.clever-cloud.com/), or any remote MySQL 8.0 instance).*

---

## 3. Step 2: Deploy to Vercel

### Option A: Using Vercel Web Dashboard (Recommended)
1. Push your latest code to your GitHub repository (`vasanth2006-git/infosys-springboard-project`).
2. Open the [Vercel Dashboard](https://vercel.com/dashboard) and click **Add New... → Project**.
3. Import your GitHub repository (`infosys-springboard-project`).
4. In the configuration screen:
   - **Framework Preset**: Leave as **Other** (Vercel automatically detects `vercel.json` and `@vercel/python`).
   - **Root Directory**: `./`
5. Expand **Environment Variables** and add the variables listed below in Step 3.
6. Click **Deploy**.

---

### Option B: Using Vercel CLI
If you have Vercel CLI installed:
```bash
npm install -g vercel
vercel
```
Follow the prompts to link the project and set environment variables.

---

## 4. Step 3: Configure Vercel Environment Variables

In the Vercel Dashboard under **Settings → Environment Variables**, add the following:

| Variable Name | Value | Purpose |
| :--- | :--- | :--- |
| `MYSQL_HOST` | `gateway01.us-east-1.prod.aws.tidbcloud.com` | Cloud MySQL host |
| `MYSQL_PORT` | `4000` | Cloud MySQL port (4000 for TiDB, 3306 for standard) |
| `MYSQL_USER` | `2XxX...root` | Cloud MySQL username |
| `MYSQL_PASSWORD` | `YourClusterPassword` | Cloud MySQL password |
| `MYSQL_DB` | `test` (or `shopsense_new_db`) | Database name |
| `MYSQL_SSL` | `true` | Enables TLS encryption for cloud MySQL |
| `GEMINI_API_KEY` | `AIzaSy...` | Your Google Gemini API Key |

*(Optional Email Configuration):*
- `SMTP_HOST`: `smtp.gmail.com`
- `SMTP_PORT`: `587`
- `SMTP_USER`: `your_email@gmail.com`
- `SMTP_PASSWORD`: `your_app_password`
- `SMTP_USE_TLS`: `True`
- `EMAIL_FROM`: `reports@shopsense.com`

---

## 5. Step 4: Verification Checklist

Once the Vercel build finishes and shows **Ready**:

1. **Access the Public URL**:
   - Open: `https://<project-name>.vercel.app`
   - Verify the ShopSense login page loads over HTTPS.

2. **Access Swagger UI API Docs**:
   - Open: `https://<project-name>.vercel.app/docs`
   - Verify all endpoints and schemas are documented.

3. **Verify Authentication**:
   - **Admin Login**: `admin@gmail.com` / `admin123` → Admin Dashboard loads.
   - **Vendor Login**: `vendor@gmail.com` / `vendor123` → Vendor Dashboard loads.

4. **Verify AI Services**:
   - In Vendor Dashboard, ask the AI Data Analyst a question.
   - Test the RAG Shopping Assistant with a product query.

---

## 6. Serverless Behavioral Notes

- **WebSockets**: Vercel Serverless Functions terminate after each HTTP response and do not support persistent bi-directional WebSockets. Dashboards operate fully with normal HTTP requests and page refreshes.
- **Background Scheduler**: Infinite background loops do not run continuously in serverless functions. Weekly AI vendor analysis can be triggered on demand via `POST /vendor/api/weekly-report/generate`.
- **Cold Starts**: The first request after a period of inactivity may take 3–5 seconds as AWS Lambda initializes the Python environment. Subsequent requests are fast.
