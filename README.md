# Fresh Cart API

Async Django + Django‑Ninja backend for an e‑commerce store. The API is versioned under `/api/v1/`, uses PostgreSQL, JWT authentication, Stripe payments, Redis cache, and Cloudinary for media. The container image includes Nginx (reverse proxy + static), Gunicorn (ASGI) with Uvicorn workers, and Redis.

Last updated: 2025-12-06

## Table of Contents
- [Features](#features)
- [Tech stack](#tech-stack)
- [Project structure (apps)](#project-structure-apps)
- [Prerequisites](#prerequisites)
- [1) Configuration](#1-configuration)
- [2) Run with Docker (single‑container, recommended)](#2-run-with-docker-single-container-recommended)
- [3) Docker Compose (optional)](#3-docker-compose-optional)
- [4) Development without Docker (optional)](#4-development-without-docker-optional)
- [5) Authentication (JWT)](#5-authentication-jwt)
- [6) Core endpoints (high level)](#6-core-endpoints-high-level)
- [7) Stripe setup (local)](#7-stripe-setup-local)
- [8) Static & media](#8-static--media)
- [Troubleshooting](#troubleshooting)
- [Notes](#notes)

## Features
- Async Django‑Ninja API with built‑in OpenAPI/Swagger UI at `/api/v1/docs`
- JWT auth (token pair/refresh/verify) via `django-ninja-jwt`
- Custom user model (email‑based) with signup/login and password reset flows
- Catalog: products, categories, brands, images, ratings
- User addresses
- Carts with coupons/discounts and totals
- Orders with Stripe Checkout payment + webhook
- Cloudinary media storage
- Redis cache
- Single‑image Docker deployment (Nginx + Gunicorn + Redis)

## Tech stack
- Python 3.13, Django 5.2
- django‑ninja, django‑ninja‑extra, django‑ninja‑jwt
- PostgreSQL
- Stripe
- Gunicorn + Uvicorn workers (ASGI)
- Nginx
- Redis
- Cloudinary (django‑cloudinary‑storage)

## Project structure (apps)
- `catalog`: Product, Category, Brand, ProductImage, ProductRating
- `users`: Custom `User` (email), `Address`, auth routes
- `carts`: Cart, CartItem, Coupon
- `orders`: Order, OrderItem
- `payments`: Payment + Stripe webhook
- `fresh_cart`: project settings, API aggregator

All routers are aggregated under `/api/v1/` via `fresh_cart/api.py`.

## Prerequisites
- Docker (and optionally Docker Compose)
- A PostgreSQL database URL (e.g., Neon, Supabase, local)
- Stripe account or Stripe CLI for local webhook forwarding
- Cloudinary account (for media)

## 1) Configuration
Copy `.env.example` to `.env` and set values.

```bash
cp .env.example .env
```

Important variables (see `.env.example` for the full list):
- Django: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_TIME_ZONE`
- Database: `DATABASE_URL` (e.g. `postgres://USER:PASS@HOST:5432/DB?sslmode=require`)
- Redis: `REDIS_URL` (default in‑container redis works: `redis://127.0.0.1:6379/1`)
- Stripe: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- Cloudinary: Either `CLOUDINARY_URL` or the split parts `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
- Email: `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL`

Notes:
- The project reads the database from `DATABASE_URL` (not separate `POSTGRES_*` vars).
- Media storage is configured to use Cloudinary by default; ensure Cloudinary vars are set.

## 2) Run with Docker (single‑container, recommended)
The image contains Nginx, Gunicorn, and Redis. This is the simplest way to run locally or in a VM.

```bash
docker build -t fresh-cart .
docker run -d --name fresh-cart \
  --env-file ./.env \
  -p 8000:80 \
  -v "$(pwd)/staticfiles:/app/staticfiles" \
  -v "$(pwd)/media:/app/media" \
  fresh-cart

# Create an admin user
docker exec -it fresh-cart python manage.py createsuperuser
```

Open:
- API docs (Swagger): http://localhost:8000/api/v1/docs
- Admin: http://localhost:8000/admin

## 3) Docker Compose (optional)
The repository includes a `docker-compose.yml`. The current image already bundles Nginx, so you can run only the `web` service and map its port 80 to the host, e.g. add:

```yaml
services:
  web:
    ports:
      - "8000:80"
```

Then run:

```bash
docker compose up --build -d web
```

Important:
- The additional `nginx` service in `docker-compose.yml` is not required for the current image. If you still want to use it, change its proxy upstream to point to `http://web:8000` (container‑to‑container), not `http://127.0.0.1:8000`.

Useful commands:
- View logs: `docker compose logs -f web`
- Create superuser: `docker compose exec web python manage.py createsuperuser`
- Run migrations: `docker compose exec web python manage.py migrate`

## 4) Development without Docker (optional)
Run the app directly if you have Python and PostgreSQL locally.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # set DATABASE_URL, Cloudinary, Stripe, etc.
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Open http://localhost:8000/api/v1/docs

## 5) Authentication (JWT)
Token endpoints (provided by `AsyncNinjaJWTDefaultController`):
- `POST /api/v1/token/pair` → `{ access, refresh }`
- `POST /api/v1/token/refresh`
- `POST /api/v1/token/verify`

Custom auth endpoints:
- `POST /api/v1/auth/signup` → returns token pair
- `POST /api/v1/auth/login` → returns token pair
- `POST /api/v1/auth/password/change` (auth)
- `POST /api/v1/auth/password/forgot`
- `POST /api/v1/auth/password/reset`

Send the access token in the `Authorization` header:

```
Authorization: Bearer <ACCESS_TOKEN>
```

## 6) Core endpoints (high level)
Public:
- `GET /api/v1/products`
- `GET /api/v1/products/{id}`
- `GET /api/v1/categories`
- `GET /api/v1/brands`

Authenticated (Bearer token):
- Cart: `GET /api/v1/cart`, `POST /api/v1/cart`, `PUT /api/v1/cart`, `DELETE /api/v1/cart`, `POST /api/v1/cart/apply-coupon`
- Orders: `POST /api/v1/orders`, `GET /api/v1/orders`, `GET /api/v1/orders/{id}`
- Stripe Checkout: `POST /api/v1/orders/{order_id}/pay/stripe` → returns `checkout_url`
- Webhook: `POST /api/v1/payments/stripe/webhook`

Explore all request/response schemas in Swagger UI.

## 7) Stripe setup (local)
Option A: Use Stripe test keys and set a webhook endpoint in the Stripe Dashboard to:

```
http://localhost:8000/api/v1/payments/stripe/webhook
```

Option B (recommended for local): Stripe CLI forwarding

1. Login and listen:
```bash
stripe login
stripe listen --forward-to localhost:8000/api/v1/payments/stripe/webhook
```
2. The CLI prints a signing secret (starts with `whsec_`). Put it in `.env` as `STRIPE_WEBHOOK_SECRET` and restart the container.

Create and pay an order:
- Create an order: `POST /api/v1/orders`
- Get a Checkout URL: `POST /api/v1/orders/{order_id}/pay/stripe`
- Open the returned `checkout_url` and complete payment using Stripe test cards
- The webhook will mark the order as paid

## 8) Static & media
- Static files are collected to `./staticfiles` (mounted in the container and served by Nginx)
- Media uploads use Cloudinary by default (configure credentials in `.env`). The `/media/` path in Nginx is left for backward compatibility for local files.

## Troubleshooting
- Database: ensure `DATABASE_URL` is correct and reachable (SSL params often required for hosted DBs).
- Cloudinary: missing or wrong credentials will cause upload errors; set `CLOUDINARY_URL` or split vars.
- JWT 401/403: obtain a token via `/api/v1/token/pair` or `/api/v1/auth/login` and send `Authorization: Bearer ...`.
- Docs not loading: check container logs (`docker logs fresh-cart`) or `docker compose logs -f web`.
- Stripe webhook 400: `STRIPE_WEBHOOK_SECRET` must match the Dashboard/CLI secret.
- Docker Compose nginx: if you enable the separate `nginx` service, update its upstream to `http://web:8000`; otherwise prefer mapping `web` port 80 directly.

## Notes
- API base path is `/api/v1/`
- Custom user model is `users.User`
