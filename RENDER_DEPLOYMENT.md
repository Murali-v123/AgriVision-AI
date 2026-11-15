# 🚀 AgriVision AI – Render Deployment Guide

This guide explains how AgriVision AI is configured for seamless deployment on [Render](https://render.com), along with automatic provisioning of the **three demonstration accounts**.

---

## 📁 Required Deployment Files Added

The following production files have been added and configured in the project:

| File | Purpose |
| :--- | :--- |
| **`render.yaml`** | **Render Blueprint Specification** (Infrastructure-as-Code). Automates service creation, build command, start command, and environment variables on Render. |
| **`build.sh`** | **Render Build Script**. Automatically runs on Render during build: installs Python dependencies, runs Django migrations, seeds demo accounts, and compiles static assets. |
| **`start.sh`** | **Production Startup Script**. Automatically runs on web service boot/restart: ensures database schema is up-to-date, guarantees the 3 demo accounts exist, and launches Gunicorn WSGI HTTP server on port `$PORT`. |
| **`Procfile`** | Declares the web process (`web: bash start.sh`) for Render and other cloud container platforms. |
| **`requirements.txt`** | Updated with production dependencies: `gunicorn` (WSGI server), `whitenoise` (static file serving), `dj-database-url`, and `psycopg2-binary` (PostgreSQL adapter). |
| **`backend/agrivision/frontend_views.py`** | Production frontend view handler that allows the Django service to serve all HTML pages (`index.html`, `login.html`, `farmer/*`, `buyer/*`, `admin/*`) directly under a single Render URL with zero CORS issues. |
| **`assets/js/api.js` & `ml-client.js`** | Updated with dynamic API URL resolution: automatically connects to `https://<your-render-subdomain>.onrender.com/api` in production, while maintaining local compatibility (`http://127.0.0.1:8000/api`). |

---

## 🔑 Demonstration Accounts

On every deployment and restart, `start.sh` executes `python backend/manage.py seed_demo_data`. This guarantees that all three demonstration accounts are ready for immediate sign-in:

| Role | Email | Password | Details & Pre-seeded State |
| :--- | :--- | :--- | :--- |
| 🧑‍🌾 **Farmer** | `ramesh@demo.in` | `farmer123` | **Ramesh Kumar** (Ramesh Vegetable Farm, Kolar, Karnataka) – 6 acres, pre-seeded Tomato & Onion listings, active bids. |
| 🏢 **Buyer** | `buyer@demo.in` | `buyer123` | **FreshMart Wholesale** (Bengaluru, Karnataka) – Verified wholesale buyer, active purchase bids, delivery tracking. |
| 🛡️ **Administrator** | `admin@demo.in` | `admin123` | **Platform Admin** – Full access to Moderation, User Verification, Bidding Oversight, AI Monitoring, and Audit Logs. |

> **Quick Login Tip**: On the `login.html` page, you can either enter the credentials manually or click the pre-filled **Farmer**, **Buyer**, or **Administrator** demo quick-buttons, then click **Sign in**!

---

## 🛠️ Step-by-Step Deployment Instructions

### Step 1: Commit and Push Changes to GitHub
Push the new deployment files and updates to your GitHub repository:
```bash
git add .
git commit -m "Add Render deployment configuration and automated demo accounts seeding"
git push origin integration
# (or your main/master branch)
```

### Step 2: Deploy on Render

#### Option A: Using Render Blueprints (Recommended - 1 Click)
1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** in the top navigation bar and select **Blueprint**.
3. Select your GitHub repository (`AgriVision-AI`).
4. Render will automatically read `render.yaml` and configure:
   - **Service Type**: Web Service (Python)
   - **Build Command**: `bash build.sh`
   - **Start Command**: `bash start.sh`
   - **Environment Variables**: `PYTHON_VERSION=3.11.9`, `DEBUG=False`, `ALLOWED_HOSTS=*`, `CORS_ALLOW_ALL_ORIGINS=True`
5. Click **Apply**. Render will automatically build and deploy the app!

#### Option B: Manual Web Service Setup
If you prefer creating a Web Service manually without Blueprints:
1. In Render Dashboard, click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Configure the following fields:
   - **Name**: `agrivision-ai` (or your choice)
   - **Language**: `Python`
   - **Branch**: `integration` (or `main`)
   - **Build Command**: `bash build.sh`
   - **Start Command**: `bash start.sh`
   - **Plan**: `Free`
4. Under **Environment Variables**, add:
   - `PYTHON_VERSION`: `3.11.9`
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `*`
   - `CORS_ALLOW_ALL_ORIGINS`: `True`
5. Click **Create Web Service**.

---

## 🌐 Verifying the Deployment

1. Once the deployment status turns to **Live**, click your Render service URL (e.g., `https://agrivision-ai.onrender.com`).
2. You will see the **AgriVision AI Landing Page**.
3. Click **Log in** (or go to `https://<your-service>.onrender.com/login.html`).
4. Click on any of the **Demonstration accounts** buttons:
   - Click **Farmer** -> Form fills with `ramesh@demo.in` / `farmer123` -> Click **Sign in** -> Opens Farmer Dashboard!
   - Click **Buyer** -> Form fills with `buyer@demo.in` / `buyer123` -> Click **Sign in** -> Opens Buyer Dashboard!
   - Click **Administrator** -> Form fills with `admin@demo.in` / `admin123` -> Click **Sign in** -> Opens Admin Dashboard!
