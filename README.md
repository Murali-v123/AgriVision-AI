# AgriVision AI v3.2 – AI-Powered Agricultural Marketplace

Developed for **Build Beyond'26 (Problem Statement 4.2)**.

AgriVision AI connects smallholder farmers directly with wholesale buyers and food processors, eliminating predatory intermediaries through AI quality assessment, price intelligence, transparent bidding, and order tracking.

---

## 🏗 Architecture & Project Structure

The project consists of an existing multi-page responsive frontend integrated with a Django REST Framework backend:

```
AgriVisionAI/
├── admin/                  # 11 Admin moderation & analytics pages
├── buyer/                  # 12 Buyer discovery, bidding & orders pages
├── farmer/                 # 11 Farmer produce, quality check & sales pages
├── assets/
│   ├── css/style.css       # Design tokens, components and responsive layout
│   └── js/
│       ├── icons.js        # SVG stroke icons
│       ├── data.js         # Base configuration, constants, location data
│       ├── api.js          # NEW Centralized API client & JWT token adapter
│       ├── ui.js           # Reusable UI components & chart registry
│       ├── views.js        # Page views for Farmer, Buyer, Admin
│       └── actions.js      # Form submissions & API bridges with fallback
├── index.html              # Landing page
├── login.html              # Sign in page
├── register.html           # Farmer / Buyer registration
├── forgot.html             # Password recovery
└── backend/                # NEW Django REST Framework Backend
    ├── agrivision/         # Django core settings, URLs, WSGI, ASGI
    ├── apps/
    │   ├── users/          # Custom User model, Profiles, Auth & Buyer discovery
    │   ├── products/       # Produce listings & AI Quality Assessment
    │   ├── bids/           # Bidding, Counter-offers & Atomic Acceptance
    │   ├── orders/         # Order tracking & delivery status
    │   ├── market/         # Mandi Price Intelligence & Demand Index
    │   └── admin_api/      # Admin Analytics, Moderation & AI Auditing
    ├── db.sqlite3          # Pre-seeded database with all demo accounts & listings
    ├── requirements.txt    # Python dependencies
    ├── .env.example        # Environment variables template
    ├── manage.py
    └── README.md           # In-depth Backend API reference
```

---

## ⚡ Quick Start Guide

### 1. Start the Backend Server (Port 8000)
```powershell
# Navigate to the backend directory
cd backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# source venv/bin/activate    # Linux/macOS

# Run migrations (already applied)
python manage.py migrate

# Seed demonstration accounts and listings (already seeded)
python manage.py seed_demo_data

# Start the server
python manage.py runserver 127.0.0.1:8000
```
Backend API will be running at `http://127.0.0.1:8000/api/`.

### 2. Open the Frontend
Open `index.html` or `login.html` directly in your browser, or serve using any static web server:
```powershell
# From the AgriVisionAI root directory
python -m http.server 5500
```
Then navigate to `http://localhost:5500/login.html`.

---

## 🔑 Demonstration Accounts

All demonstration accounts have been seeded into the backend database:

| Role | Email | Password | Details |
| :--- | :--- | :--- | :--- |
| **Farmer** | `ramesh@demo.in` | `farmer123` | Ramesh Vegetable Farm (Kolar, Karnataka) |
| **Buyer** | `buyer@demo.in` | `buyer123` | FreshMart Wholesale (Bengaluru, Karnataka) – Verified |
| **Admin** | `admin@demo.in` | `admin123` | Platform Admin (Full Moderation & Audit Privileges) |

---

## 🧪 Running Automated Tests

Run the full Django test suite (16 tests covering auth, bidding, partial orders, quality checks, permissions):
```powershell
cd backend
python manage.py test apps.users apps.products apps.bids apps.admin_api
```

Run the live end-to-end integration test:
```powershell
cd backend
python test_live_workflow.py
```
This tests:
1. Farmer sign-in & JWT generation
2. Buyer sign-in & verification check
3. Farmer produce listing creation
4. Buyer marketplace browsing with query filters
5. Buyer bid submission
6. Atomic transaction acceptance by Farmer
7. Stock deduction (500 kg $\rightarrow$ 300 kg remaining) & Order creation
8. Order dispatch & delivery lifecycle
9. Admin analytics aggregation & GMV calculation
10. AI model transparency & inspection disclosure

---

## 🛡 Security & Design Principles
- **No Client Trust**: Farmer and Buyer IDs are extracted from authenticated JWT tokens, never trusted from client payloads.
- **Concurrency & Transaction Safety**: Bid acceptance uses database row-level locking (`select_for_update()`) and atomic transactions to prevent double acceptance or overselling.
- **Role Isolation**: Strict permission checks prevent farmers from editing competitors' listings or unauthorized users accessing admin endpoints.
- **Truthful AI & Market Data**: The quality inspection uses an RGB pixel uniformity heuristic clearly labeled as demonstration data (`pixel_heuristic_demo`), avoiding deceptive claims of AGMARKNET certification.
