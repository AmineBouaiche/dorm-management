# Dorm Management System

[![CI](https://github.com/AmineBouaiche/dorm-management/actions/workflows/ci.yml/badge.svg)](https://github.com/AmineBouaiche/dorm-management/actions/workflows/ci.yml)

A backend-first dormitory management platform built with FastAPI and PostgreSQL. The project models residences, rooms, students and bookings, with transaction-safe booking constraints, JWT authentication and role-based authorization.

## Stack

- Python 3.13
- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Alembic
- Pydantic
- PyJWT
- pytest
- Docker / Docker Compose

## Current capabilities

### Public
- Register a student account
- Log in and receive a JWT bearer token
- Browse active residences and rooms
- Query active room availability for a date range

### Student
- Read own profile
- Create bookings using authenticated identity
- Read own booking history
- Cancel own bookings

The booking request deliberately does not accept a student identifier. The backend derives the student from the authenticated user.

### Admin
- Create and update residences
- Create and update rooms
- Activate/deactivate residences and rooms without deleting history
- List all inventory, including inactive records
- List students
- List all bookings
- Confirm bookings
- Cancel any booking
- Read occupancy, booking-status and confirmed-revenue analytics

## Weekly pricing

Rooms now store `weekly_rate`, not an ambiguous `price` field. Booking totals are calculated by the backend:

```text
billable_weeks = ceil(number_of_days / 7)
booking_amount = weekly_rate * billable_weeks
```

A partial week is billed as a full week.

Migration `20260820_0003` renames the old `price` column and normalizes existing synthetic development rooms to representative weekly rates because the old whole-booking values are not semantically convertible to weekly pricing.

## Inventory lifecycle

Rooms and residences are never hard-deleted in v1. Both have an `is_active` flag.

- active residence + active room: visible and bookable
- inactive residence or room: hidden from public room discovery and cannot receive new bookings
- historical bookings remain readable

A residence also has an optional `image_url`, intended to point to its representative frontend image.

## Booking integrity

Pending and confirmed bookings block overlapping room/date ranges. A student also cannot hold overlapping active bookings across different rooms. PostgreSQL exclusion constraints are the final concurrency-safe enforcement layer; service-level checks provide readable API errors.


## Continuous integration

GitHub Actions runs on pushes and pull requests targeting `main`. The CI job provisions PostgreSQL 17, installs Python 3.13 dependencies, applies Alembic migrations, executes the full pytest suite, and runs Ruff.

## Local setup

Copy `.env.example` to `.env` and replace `JWT_SECRET_KEY` with a long random value for anything beyond local development.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
docker compose up -d
alembic upgrade head
pytest
```

After the Phase 5A update, `alembic current` should report:

```text
20260820_0003 (head)
```

## Create the first admin

With PostgreSQL running and the virtual environment active:

```powershell
python scripts/create_admin.py
```

## Run the API

```powershell
uvicorn app.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Main API surface

```text
POST  /api/auth/register
POST  /api/auth/login
GET   /api/auth/me

GET   /api/buildings
POST  /api/buildings                    ADMIN
PATCH /api/buildings/{building_id}      ADMIN

GET   /api/rooms
GET   /api/rooms/available
GET   /api/rooms/{room_id}
POST  /api/rooms                        ADMIN
PATCH /api/rooms/{room_id}              ADMIN

GET   /api/students/me                  STUDENT

POST  /api/bookings                     STUDENT
GET   /api/bookings/me                  STUDENT
PATCH /api/bookings/{id}/cancel         STUDENT (owner only)

GET   /api/admin/buildings              ADMIN (includes inactive)
GET   /api/admin/rooms                  ADMIN (includes inactive)
GET   /api/admin/students               ADMIN
GET   /api/admin/bookings               ADMIN
PATCH /api/admin/bookings/{id}/confirm  ADMIN
PATCH /api/admin/bookings/{id}/cancel   ADMIN
GET   /api/admin/analytics              ADMIN
```

## Test database isolation

The automated test suite uses a separate PostgreSQL instance on port `5433` (`db_test`). It does not read from or modify the persistent development database on port `5432`.

Start both services with:

```powershell
docker compose up -d
```

Then run:

```powershell
pytest
```

At the beginning of each test session, Alembic rebuilds the test schema from the migration history. Each individual test runs inside an outer transaction/savepoint and is rolled back afterward, so test data cannot leak between tests.

## Frontend foundation

The first frontend milestone is intentionally framework-free and establishes the shared interface system before feature pages are implemented.

- Source Sans 3 typography with system fallbacks
- centralized color, typography, spacing, radius, layout, and motion tokens
- responsive 1240 px content container
- primary top navigation with a text-based mobile menu
- secondary administration navigation primitives
- shared buttons, fields, panels, status indicators, messages, tables, skeletons, and dialog styles
- FastAPI static-file serving from `frontend/`
- `/style-guide` visual reference for the foundation components

Run the application and open `http://127.0.0.1:8000/style-guide` to inspect the current frontend foundation.

## Frontend authentication milestone

The framework-free frontend now includes real registration and login flows backed by the FastAPI API. Access tokens are held in browser `sessionStorage`, attached as bearer tokens by a centralized API client, and cleared when an authenticated API request returns `401`. Role resolution uses `GET /api/auth/me`; student and administrator session checkpoints reject the wrong role and redirect to the correct authenticated area.

Development routes:

- `/login` - student/admin sign in
- `/register` - student registration
- `/session` - temporary student authentication checkpoint
- `/admin/session` - temporary administrator authentication checkpoint
- `/style-guide` - frontend foundation reference

The session checkpoint pages are intentionally temporary. They validate authentication infrastructure without pre-empting the locked student dashboard and admin interface designs.

## Student room discovery milestone

The student-facing room discovery flow is available at `/rooms` and remains framework-free. It includes arrival/departure availability search, room type and residence filters, responsive residence-image cards, room detail pages, weekly-rate presentation, estimated totals, and explicit loading/empty/error handling. Room detail carries a selected stay to `/booking/confirm`, but Phase 5B.3 deliberately does not submit bookings yet.

The repository includes four local representative residence assets and an idempotent development seed script. With the development database running and migrations applied, populate the catalogue with:

```powershell
python scripts/seed_demo_data.py
```

This creates or refreshes North Hall, West Court, Riverside House, and Clifton Lodge with approximately 32 synthetic rooms using realistic weekly rates. The data is for local development/demo use only.


## Phase 5B.4 booking workflow

The student room-detail handoff now continues through an authenticated confirmation page and submits to the real `POST /api/bookings` endpoint. The confirmation page rechecks availability, displays billable weeks and an estimated total, disables duplicate submissions, and maps booking conflicts to domain-specific messages. Successful requests route to `/booking/submitted`, where the persisted booking is reloaded from `/api/bookings/me` and shown with its server-calculated amount and pending status.

## Phase 5B.5 student experience

The student frontend now includes the real dashboard, My Bookings, booking details, cancellation flow, and account page. The dashboard prioritises an active booking and otherwise the nearest upcoming pending or confirmed booking. Cancellation is ownership-protected by the backend and requires a custom destructive confirmation dialog in the frontend.


## Admin interface

Authenticated administrators use `/admin` for the operational interface. It includes the accommodation overview, room and residence inventory management, student records, booking management, and confirmed-revenue analytics. Inventory is retired through active/inactive state rather than hard deletion so historical bookings remain intact.

## Production hardening

The application distinguishes development and production configuration through `ENVIRONMENT`.
Production startup rejects placeholder or short JWT secrets, API documentation is disabled, and the
development-only style guide is not routed. JWTs validate issuer, audience, issue time, and expiry
claims in addition to the user subject.

Every HTTP response receives baseline browser security headers including a Content Security Policy,
clickjacking protection, MIME-sniffing protection, a restrictive permissions policy, and a referrer
policy. The frontend and API are intentionally same-origin, so permissive CORS is not enabled.

Before production deployment, set at least:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg://...
JWT_SECRET_KEY=<unique-random-secret-at-least-32-characters>
```

Development helpers such as `/docs`, `/redoc`, `/openapi.json`, and `/style-guide` are available only
outside production where applicable.

### Code quality

Ruff configuration is included in `pyproject.toml`. Run:

```powershell
ruff check .
pytest
```

before committing a milestone.

## Production container

The production Docker image uses a multi-stage build, runs the application as a non-root user, applies Alembic migrations before startup, and exposes a container health check at `/health`.

Build locally:

```bash
docker build -t dorm-management:local .
```

The runtime requires at least `DATABASE_URL` and a strong `JWT_SECRET_KEY`. `ENVIRONMENT=production` is set by the image. The hosting platform should provide `PORT` when it does not use port 8000.

The entrypoint runs `alembic upgrade head` before starting Uvicorn. This is appropriate for the current single-instance deployment target; migration orchestration should be separated if the service is later scaled to multiple concurrent application instances.

Local production-image smoke test:

```powershell
$env:JWT_SECRET_KEY=(python -c "import secrets; print(secrets.token_urlsafe(48))")
docker compose --profile production up --build -d app
docker compose ps
```

The `app` service is behind the `production` Compose profile, so normal `docker compose up -d` continues to start only the development databases.

## Security model

The browser frontend authenticates with a short-lived JWT stored only in a Secure/HttpOnly/SameSite cookie in production. A separate readable CSRF cookie is used with an `X-CSRF-Token` header on state-changing requests. The bearer-token login remains available for development tooling and API clients, but the browser never persists or reads the JWT. New passwords are hashed with Argon2id; legacy PBKDF2 hashes are transparently upgraded after a successful login.

Frontend dynamic values are HTML-escaped before template insertion, and the production CSP remains a defense-in-depth control rather than the primary XSS mitigation. Passwords require 12 to 128 characters.

### Abuse and request-size controls

The API enforces a 64 KiB request-body ceiling because the application has no upload endpoints. Authentication failures are throttled with sliding windows keyed by both client IP and normalized account identifier, while registration is throttled by client IP. Rate-limit responses use HTTP 429 and include `Retry-After`.

The current limiter is intentionally process-local and is valid for the single-Uvicorn-worker deployment profile in this repository. A multi-instance deployment must replace it with a shared limiter store before scaling out.


## Security 6.S2B: API and data resilience

Collection endpoints are bounded with `page` and `per_page` query parameters. The maximum page size is 100 and responses include `X-Total-Count`, `X-Page`, and `X-Per-Page` headers. Ordering is deterministic. Production assigns an `X-Request-ID` correlation identifier to responses and converts unhandled application exceptions into a generic JSON 500 response while logging only request metadata and the server-side exception.

## Security 6.S2C: observability and accountability

The application keeps operational request logs intentionally sparse. Each HTTP request is logged with only its correlation ID, method, path, response status, and duration. Query strings, request bodies, cookies, authorization headers, passwords, tokens, and user-agent data are not included by the application request logger.

Successful privileged mutations create persistent database audit records. The audit trail currently covers residence creation/updates, room creation/updates, and admin booking confirmation/cancellation. Records contain the acting admin user ID, action, resource type and ID, correlation ID, timestamp, and only minimal non-sensitive metadata such as the names of fields changed. Audit records are available to administrators through the paginated `GET /api/admin/audit-logs` endpoint.

## Supply-chain security

The repository uses layered dependency monitoring and CI enforcement:

- Dependabot checks Python dependencies, GitHub Actions, and the Docker base image weekly.
- CI installs `pip-audit` with the development toolchain and fails when the resolved Python environment contains a known vulnerability reported by the audit service.
- The workflow keeps the default `GITHUB_TOKEN` read-only and disables persisted checkout credentials because the CI job never pushes changes.
- Dependency update pull requests still run the full PostgreSQL migration, pytest, Ruff, vulnerability-audit, and production-container build gates before merge.

`pip-audit` requires network access to query vulnerability data. A transient advisory-service outage should be treated as an infrastructure failure rather than bypassed by disabling the security gate.
