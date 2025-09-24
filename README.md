# Fresh Cart API

Async Django + Django-Ninja backend for an e‑commerce store. The API is versioned under /api/v1/, uses PostgreSQL, JWT authentication, Stripe payments, and is containerized with Docker. Nginx serves as a reverse proxy and serves static/media files.

## Features
- Async Django-Ninja API (Swagger UI at /api/v1/docs)
- JWT auth (access/refresh/verify)
- Catalog: products, categories, brands
- Customers: addresses
- Carts with coupons/discounts
- Orders with Stripe Checkout payment
- Docker Compose stack: Postgres, Web (Gunicorn+Uvicorn), Nginx

## Tech stack
- Python 3.13, Django 5.2
- django-ninja, django-ninja-jwt
- PostgreSQL
- Stripe
- Gunicorn + Uvicorn workers (ASGI)
- Nginx

## Project structure (apps)
- catalog: Product, Category, Brand
- users: Address and related endpoints
- carts: Cart, CartItem, Coupon
- orders: Order, OrderItem
- payments: Payment + Stripe webhook
- fresh_cart: project settings, API aggregator

Routers from each app are aggregated under /api/v1/ via fresh_cart/api.py.

## Prerequisites
- Docker and Docker Compose installed
- Stripe account (for testing payments) or Stripe CLI for local webhook forwarding

## 1) Configuration
Copy .env.example to .env and adjust values as needed.

```bash
cp .env.example .env
```

Important variables:
- Django: DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS
- Postgres: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
  - In docker-compose, POSTGRES_HOST is db
- Stripe: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

For local testing with Stripe CLI you can set a temporary STRIPE_WEBHOOK_SECRET from the CLI output later.

## 2) Run with Docker Compose (recommended)
Build and start the stack:

```bash
docker compose up --build -d
```

This will:
- Start Postgres
- Build the web image and run migrations/collectstatic automatically
- Start Gunicorn (ASGI) with Uvicorn workers
- Start Nginx on host port 8000

Useful commands:
- View logs: docker compose logs -f
- Create superuser: docker compose exec web python manage.py createsuperuser
- Run migrations (manual): docker compose exec web python manage.py migrate

Open in browser:
- API docs (Swagger): http://localhost:8000/api/v1/docs
- Admin: http://localhost:8000/admin

## 3) Authentication (JWT)
Obtain tokens:
- POST /api/v1/auth/token/pair  → { access, refresh }
- POST /api/v1/auth/token/refresh
- POST /api/v1/auth/token/verify

Use the access token in Authorization header:

```
Authorization: Bearer <ACCESS_TOKEN>
```

## 4) Core endpoints (high level)
Public:
- GET /api/v1/products
- GET /api/v1/products/{id}
- GET /api/v1/categories
- GET /api/v1/brands

Authenticated (Bearer token):
- Cart: GET/POST /api/v1/cart, /api/v1/cart/add, /api/v1/cart/update, /api/v1/cart/remove, /api/v1/cart/apply-coupon
- Orders: POST /api/v1/orders, GET /api/v1/orders, GET /api/v1/orders/{id}
- Stripe Checkout: POST /api/v1/orders/{order_id}/pay/stripe → returns checkout_url
- Stripe webhook (Nginx -> app): POST /api/v1/payments/stripe/webhook

Explore all request/response schemas in Swagger UI.

## 5) Stripe setup (local)
Option A: Use Stripe test keys in .env and set a webhook endpoint in the Stripe Dashboard to:

```
http://localhost:8000/api/v1/payments/stripe/webhook
```

Option B (recommended for local): Stripe CLI forwarding

1. Login and listen:
```bash
stripe login
stripe listen --forward-to localhost:8000/api/v1/payments/stripe/webhook
```
2. The CLI prints a webhook signing secret (starts with whsec_). Put it into .env as STRIPE_WEBHOOK_SECRET and restart the web container (or docker compose up -d).

Create and pay an order:
- Create an order: POST /api/v1/orders
- Get a Stripe Checkout URL: POST /api/v1/orders/{order_id}/pay/stripe
- Open the returned checkout_url in a browser and complete payment using Stripe test cards
- The webhook will mark the order as paid

## 6) Development without Docker (optional)
You can run the app directly if you have Python and Postgres locally.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit DB creds to your local Postgres
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Open http://localhost:8000/api/v1/docs

Note: For the async stack in production we use Gunicorn+Uvicorn; Django's runserver is fine for development.

## 7) Static & media
- Static files are collected to ./staticfiles (mounted to Nginx)
- Media files are stored in ./media (mounted to Nginx)

## Troubleshooting
- Database connection errors: Ensure .env Postgres values match docker-compose (POSTGRES_HOST=db) and that the db container is healthy.
- 400 on Stripe webhook: STRIPE_WEBHOOK_SECRET mismatches the secret used by Stripe Dashboard/CLI. Update .env and restart.
- 401/403 on protected endpoints: Acquire JWT via /api/v1/auth/token/pair and include Bearer token.
- Swagger not loading: Check Nginx logs (docker compose logs -f nginx) and web logs.

## Notes
- The entrypoint runs migrations automatically. A harmless line tries `makemigrations shop` and is ignored if the app does not exist.
- API base path is /api/v1/
