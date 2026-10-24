# Django E-Commerce Store

A full-stack e-commerce application built with **Django 6**, **Django REST Framework** and **Bootstrap 5**.
Customers can browse products, manage a shopping cart, place orders and pay by bank transfer with proof upload.
Store staff get a separate dashboard to track sales, low stock and verify payments.
Everything is also available through a **token-authenticated REST API** with interactive **Swagger docs**.

Built by **Saneed Ullah** as a portfolio project after completing the
[Meta Back-End Developer Professional Certificate](https://coursera.org/verify/professional-cert/4W3OG3MVRKBW).

---

## Features

### Customers
- Sign up, log in, log out and view profile (custom user model with phone, address and profile picture)
- Browse the product catalogue and view product details with images
- Shopping cart: add items, change quantity, remove items, live total (quantities limited to available stock)
- Checkout with delivery details; prices are saved per order item at the time of purchase
- Stock is checked and deducted safely at checkout (database row locking), and restored if a payment is rejected
- Order history and order detail pages with status tracking
  (`pending → processing → shipped → delivered` or `cancelled`)
- Bank-transfer payment: submit a transaction reference and upload a payment screenshot

### Store staff
- Separate staff login page
- Admin dashboard: total products, total orders, pending orders, revenue, pending payments,
  low-stock alerts (< 5 items) and recent orders
- Add new products or restock existing ones from one page
- Payment requests dashboard: verify, reject or mark payments as not received
  - Verified → order moves to **processing**
  - Rejected → order is **cancelled**
- JSON endpoint with the number of pending payments (for live notification badges)
- Django admin with order items shown inline and a bulk "mark payments verified" action

### REST API
- Token authentication: register, log in, log out, view and edit your profile
- Products with search, ordering and pagination (staff-only create / edit / delete)
- Cart, checkout, order history and payment submission for customers
- Payment review and verification for staff
- Interactive documentation with Swagger UI and ReDoc (OpenAPI 3 schema)
- Business logic (checkout, payment status) lives in shared service functions used by both the website and the API
- 28 automated tests covering the API and the main website flows

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Django 6.1 |
| API | Django REST Framework 3.18, token authentication |
| API docs | drf-spectacular (OpenAPI 3, Swagger UI, ReDoc) |
| Database | SQLite (development) |
| Frontend | Django Templates, Bootstrap 5.3, Bootstrap Icons |
| Images | Pillow (product images, profile pictures, payment proofs) |
| Auth | Django authentication with a custom user model |

---

## Project Structure

```
ecommerce_project/
├── ecommerce_project/   # Project settings, root URLs and API URLs (api_urls.py)
├── accounts/            # Custom user model, signup, login, profile, staff login
├── products/            # Product model, catalogue, add / restock products
├── cart/                # Cart and cart items (one cart per user)
├── orders/              # Checkout, orders, order items, order history
├── payments/            # Bank-transfer payments, proof upload, staff verification
├── core/                # Home page, staff dashboard, base templates
│
│   Each app contains:
│   ├── models.py, views.py, urls.py, templates/   # website
│   ├── serializers.py, api_views.py               # REST API
│   ├── services.py                                # shared business logic (orders, payments)
│   └── tests.py
├── static/              # CSS and JavaScript
├── media/               # Uploaded files (not committed)
├── manage.py
├── requirements.txt
└── .env.example         # Environment variable template
```

## Data Model

```mermaid
erDiagram
    CustomUser ||--o| Cart : has
    CustomUser ||--o{ Order : places
    Cart ||--o{ CartItem : contains
    Product ||--o{ CartItem : "added as"
    Order ||--o{ OrderItem : contains
    Product ||--o{ OrderItem : "ordered as"
    Order ||--o| Payment : "paid by"
    CustomUser ||--o{ Payment : submits
```

---

## Getting Started

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd ecommerce_project
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Copy `.env.example` to `.env` and set your own secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Paste the output as `DJANGO_SECRET_KEY` in `.env`.

| Variable | Description | Example |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django secret key (required) | `k3$x...` |
| `DJANGO_DEBUG` | Debug mode | `True` for development |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names | `example.com,www.example.com` |

### 5. Create the database and an admin user
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Run the server
```bash
python manage.py runserver
```
- Website: http://127.0.0.1:8000/
- API docs (Swagger): http://127.0.0.1:8000/api/docs/

### 7. Run the tests
```bash
python manage.py test
```

---

## REST API

Base URL: `/api/`. Interactive docs: **`/api/docs/`** (Swagger UI) and **`/api/redoc/`** (ReDoc). Raw schema: `/api/schema/`.

### Authentication
Log in to get a token, then send it with every request:
```
Authorization: Token <your-token>
```
In Swagger UI, click **Authorize** and enter `Token <your-token>`.

### Endpoints

| Method | Endpoint | Who | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | Anyone | Create an account, returns a token |
| POST | `/api/auth/login/` | Anyone | Log in, returns a token |
| POST | `/api/auth/logout/` | User | Delete your token |
| GET / PATCH | `/api/auth/me/` | User | View / update your profile |
| GET | `/api/products/` | Anyone | List products (`?search=`, `?ordering=price`, `?page=`) |
| GET | `/api/products/{id}/` | Anyone | Product details |
| POST / PUT / PATCH / DELETE | `/api/products/` … | Staff | Manage products |
| GET / DELETE | `/api/cart/` | User | View / empty your cart |
| POST | `/api/cart/items/` | User | Add a product (`product_id`, `quantity`) |
| PATCH / DELETE | `/api/cart/items/{id}/` | User | Change quantity / remove item |
| POST | `/api/orders/checkout/` | User | Place an order from the cart |
| GET | `/api/orders/` | User | Your orders (staff see all, `?status=`) |
| GET | `/api/orders/{id}/` | User | Order details |
| POST | `/api/orders/{id}/payment/` | User | Submit payment proof (`bank_reference`, `proof_screenshot`) |
| GET | `/api/payments/` | Staff | All payments (`?status=pending`) |
| POST | `/api/payments/{id}/status/` | Staff | Set `verified`, `rejected` or `not_received` |

### Example: log in and add to cart
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
     -d "username=alice&password=your-password"
# {"token": "<your-token>", "user": {...}}

curl -X POST http://127.0.0.1:8000/api/cart/items/ \
     -H "Authorization: Token <your-token>" \
     -d "product_id=1&quantity=2"
```

---

## Main Pages

| Page | URL |
|---|---|
| Home | `/` |
| Products | `/products/` |
| Product detail | `/products/<id>/` |
| Cart | `/cart/` |
| Checkout | `/orders/checkout/` |
| My orders | `/orders/history/` |
| Sign up / Log in | `/accounts/signup/`, `/accounts/login/` |
| Staff login | `/accounts/admin-login/` |
| Staff dashboard | `/dashboard/` |
| Add / restock products | `/products/add/` |
| Payment requests | `/payments/dashboard/` |
| Django admin | `/admin/` |

---

## Order and Payment Flow

1. The customer adds products to the cart and checks out with delivery details.
2. An order is created with status **pending** and the cart is emptied.
3. The customer transfers the amount to the store's bank account and submits the
   transaction reference with a screenshot.
4. Staff review the request on the payment dashboard:
   - **Verify** → order becomes **processing**
   - **Reject** → order becomes **cancelled**
   - **Not received** → order stays as it is while staff investigate
5. Staff update the order to **shipped** and **delivered** from the Django admin.

---

## Roadmap

- [x] REST API with Django REST Framework (products, cart, orders, payments, token authentication)
- [x] Interactive API documentation (Swagger / OpenAPI)
- [x] Stock checks and deduction at checkout
- [x] Automated tests for the API and main website flows
- [ ] Product categories and price filters
- [ ] Online card payments (Stripe test mode)
- [ ] Deployment with PostgreSQL

---

## Author

**Saneed Ullah**: Django back-end developer and Data Science student
Meta Back-End Developer Professional Certificate (Coursera, 2026)
