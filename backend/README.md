# AgriVision AI v3.2 – Backend & API Documentation

AI-powered agricultural marketplace backend built with Django, Django REST Framework, SimpleJWT, and Pillow for Build Beyond'26 (Problem Statement 4.2).

---

## 🛠 Tech Stack
- **Framework**: Django 5.x / 6.x & Django REST Framework (DRF)
- **Authentication**: JWT (JSON Web Tokens) via `djangorestframework-simplejwt`
- **Database**: SQLite3 (zero-configuration local development) / PostgreSQL compatible
- **Image Processing**: Pillow (RGB distribution feature heuristic for quality grading)
- **CORS**: `django-cors-headers` (configured for frontend origin integration)
- **Configuration**: `python-dotenv` for environment secrets

---

## 🚀 Quick Setup & Run

### 1. Prerequisites
- Python 3.10+ (tested and verified on Python 3.13)
- PowerShell, Bash, or Terminal

### 2. Virtual Environment & Dependencies
```powershell
# Navigate to the backend directory
cd backend

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Default `.env`:
```ini
SECRET_KEY=django-insecure-agrivision-v3-secret-key-change-in-production-2026
DEBUG=True
ALLOWED_HOSTS=*
DATABASE_URL=sqlite:///db.sqlite3
CORS_ALLOW_ALL_ORIGINS=True
```

### 4. Database Migrations
```powershell
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed Demonstration Data
Seeds 10 Farmers, 10 Buyers, 1 Superuser Admin, 20 Listings, 9 Bids, and simulated Market Prices:
```powershell
python manage.py seed_demo_data
```

### 6. Run the Backend Server
```powershell
python manage.py runserver 127.0.0.1:8000
```
The backend API is now live at `http://127.0.0.1:8000/api/`.

### 7. Run Automated Tests
```powershell
python manage.py test apps.users apps.products apps.bids apps.admin_api
```
All 16 unit & integration tests verify:
- Authentication & JWT token issuance
- Role-based permissions & account suspension
- Product listing validation & owner authorization
- In-memory image quality assessment
- Buyer verification requirements for bidding
- Database transactions preventing overselling & double acceptance
- Quantity deductions and automatic closure of unfulfillable bids
- Admin analytics, moderation, and model monitoring transparency

To run the live workflow test:
```powershell
python test_live_workflow.py
```

---

## 👥 Demonstration Accounts

| Role | Email | Password | Location / Business |
| :--- | :--- | :--- | :--- |
| **Farmer** | `ramesh@demo.in` | `farmer123` | Ramesh Vegetable Farm, Kolar, Karnataka |
| **Buyer (Verified)** | `buyer@demo.in` | `buyer123` | FreshMart Wholesale, Bengaluru Urban, Karnataka |
| **Admin** | `admin@demo.in` | `admin123` | Platform Admin (Full Moderation & Analytics) |

---

## 📡 REST API Reference

### 🔐 Authentication (`/api/auth/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register/` | Register as Farmer or Buyer | No |
| `POST` | `/api/auth/login/` | Sign in, receive access + refresh JWT | No |
| `POST` | `/api/auth/logout/` | Blacklist refresh token / logout | Yes |
| `GET` | `/api/auth/profile/` | Fetch current user & nested profile | Yes |
| `PATCH`| `/api/auth/profile/` | Update profile details / preferences | Yes |
| `POST` | `/api/auth/token/refresh/` | Refresh expired access token | No |

### 🌾 Products (`/api/products/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/products/` | Filter listings (`crop`, `district`, `grade`, `min_price`, `max_price`) | Public / Yes |
| `POST` | `/api/products/` | Create produce listing (Farmers only, multipart image upload) | Yes (Farmer) |
| `GET` | `/api/products/{id}/` | Get single listing detail | Public / Yes |
| `PATCH`| `/api/products/{id}/` | Modify listing (Own listings only) | Yes (Owner/Admin) |
| `DELETE`| `/api/products/{id}/`| Delete listing (Only if no active orders) | Yes (Owner/Admin) |

### 🔍 AI Quality Assessment (`/api/ai/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/ai/quality-assessment/` | Upload produce image for RGB pixel heuristic evaluation. Returns grade (`A`/`B`/`C`), confidence, uniformity, defects, ripeness. Labeled `pixel_heuristic_demo`. | Yes |

### 🤝 Bidding System (`/api/bids/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/bids/` | View bids (Farmers see incoming; buyers see outgoing) | Yes |
| `POST` | `/api/bids/` | Place bid (Verified buyers) or make offer (Farmers) | Yes |
| `GET` | `/api/bids/{id}/` | View specific bid details | Yes (Parties/Admin) |
| `POST` | `/api/bids/{id}/accept/` | **Atomic Transaction**: Creates Order, deducts quantity, marks listing `sold` if stock reaches 0, auto-closes unfulfillable bids. | Yes (Recipient) |
| `POST` | `/api/bids/{id}/reject/` | Reject bid/offer | Yes (Recipient) |
| `POST` | `/api/bids/{id}/counter/`| Send counter offer with new price/quantity | Yes (Recipient) |

### 📦 Orders (`/api/orders/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/orders/` | List orders for farmer/buyer | Yes |
| `GET` | `/api/orders/{id}/` | Get order status and detail | Yes (Parties) |
| `POST` | `/api/orders/{id}/dispatch/` | Mark order dispatched | Yes (Farmer) |
| `POST` | `/api/orders/{id}/deliver/` | Confirm delivery | Yes (Buyer/Farmer) |
| `POST` | `/api/orders/{id}/payment-status/` | Update demonstration payment record | Yes (Parties) |

### 📍 Buyers & Discovery (`/api/buyers/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/buyers/` | List registered wholesale buyers & crop interests | Yes |
| `GET` | `/api/buyers/nearby/` | Sort buyers by distance from farmer's coordinates (only if sharing is enabled) | Yes |
| `GET` | `/api/buyers/{id}/` | Get single buyer business profile | Yes |

### 📈 Market Intelligence (`/api/market/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/market/prices/` | Filter historical mandi prices (Clearly marked demo data) | Public |
| `GET` | `/api/market/recommendations/`| Recommended price rule ($1.04 \times$ 3-month rolling average) + historical series | Public |
| `GET` | `/api/market/demand/` | Relative crop demand indicator index | Public |
| `POST` | `/api/market/contact/` | Submit platform inquiries | Public |

### 🛡 Admin APIs (`/api/admin/`)
*Enforces server-side administrator permission (`role == 'admin'` or `is_staff == True`)*
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/admin/analytics/` | Database aggregates (User counts, GMV, orders, active listings) | Yes (Admin) |
| `GET` | `/api/admin/users/` | List all users across roles | Yes (Admin) |
| `PATCH`| `/api/admin/users/{id}/verify/` | Toggle buyer/farmer verification badge | Yes (Admin) |
| `PATCH`| `/api/admin/users/{id}/suspend/` | Suspend user account | Yes (Admin) |
| `PATCH`| `/api/admin/users/{id}/reactivate/`| Reactivate suspended account | Yes (Admin) |
| `GET` | `/api/admin/products/` | Moderate and manage all listings | Yes (Admin) |
| `GET` | `/api/admin/transactions/`| View all marketplace orders & bids | Yes (Admin) |
| `GET` | `/api/admin/models/` | AI model transparency & inspection audit logs | Yes (Admin) |

---

## 🔒 Security Architecture
1. **Password Hashing**: PBKDF2 with SHA-256 (Django default). Plain text passwords are never stored.
2. **Access Control**: Role-based access control (RBAC) enforced server-side on all sensitive endpoints.
3. **Transaction Safety**: `select_for_update()` and `transaction.atomic()` during bid acceptance eliminate race conditions and double-spending/overselling.
4. **Data Isolation**: Farmers can only modify their own listings. Buyers cannot alter orders. Suspended accounts are immediately blocked at authentication.
5. **Transparency**: All simulated prices and demonstration metrics are explicitly flagged with `is_demo_data: true` to prevent fraudulent representation.
