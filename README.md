# DRF Template
A production-oriented JSON API starter built with Django REST Framework and designed
for Railway.

## Documentation

- [`ops/MIGRATIONS.md`](ops/MIGRATIONS.md) -- expand/contract migration playbook and the
  CI checks that enforce backward-compatible schema changes.
- [`ops/SCALING.md`](ops/SCALING.md) -- how to size the web/worker concurrency dials
  against CPU and the database connection budget.

## Settings

Settings are split across multiple files in `config/settings/`:

```
base.py        -- shared foundation (Django, DRF, Celery config)
  ├── deployed.py  -- Railway config (Sentry, Mailgun, SSL, Redis cache, WhiteNoise)
  ├── local.py     -- local development (DEBUG, console email, eager Celery)
  └── test.py      -- test runner (MD5 hasher, in-memory email)
```

The active settings file is selected via `DJANGO_SETTINGS_MODULE`.

## Local Development

### Prerequisites

- Python 3.14 (see `.python-version`)
- [uv](https://docs.astral.sh/uv/)

### Setup

```bash
uv sync
cp .env.example .env
uv run python manage.py migrate
```

`manage.py` loads `.env` automatically with local settings. The example uses SQLite
and local Redis; update the URLs if you run those services elsewhere.

### Running the dev server

```bash
uv run python manage.py runserver
```

### Creating a superuser

```bash
uv run python manage.py createsuperuser
```

Admin is available at `/sadmin/`.

### Running tests

```bash
uv run pytest
```

Set `DATABASE_URL` explicitly to run the suite against PostgreSQL. CI does this.

### Linting and formatting

```bash
uv run ruff check .       # lint
uv run ruff check --fix .  # lint and auto-fix
uv run ruff format .       # format
```

### Type checks

```bash
uv run mypy .
```

### Celery (local)

Tasks run eagerly in local/test settings. To run a real worker against local Redis:

```bash
DJANGO_SETTINGS_MODULE=config.settings.local \
DJANGO_READ_DOT_ENV_FILE=True \
CELERY_TASK_ALWAYS_EAGER=False \
uv run celery -A config worker -l info --pool gevent --concurrency 100
```

Periodic tasks are defined in `CELERY_BEAT_SCHEDULE` in `base.py`. To run the beat
scheduler:

```bash
DJANGO_SETTINGS_MODULE=config.settings.local \
DJANGO_READ_DOT_ENV_FILE=True \
CELERY_TASK_ALWAYS_EAGER=False \
uv run celery -A config beat -l info
```

Celery tasks are acknowledged after execution and may be delivered more than once if
a worker is lost. Tasks should therefore be idempotent. Configure automatic retries
on individual tasks for the transient exceptions that are safe to retry.

The deployed worker uses gevent for high I/O concurrency. Tasks must use
gevent-compatible libraries and explicit network/database timeouts. Celery's gevent
pool does not reliably enforce soft or hard task time limits for blocking calls.

## Deployment (Railway)

The app is deployed on Railway with separate web and Celery worker services created
from the same repository. Each service uses its own checked-in Railway configuration
file so its start command and migration responsibilities are unambiguous.

### Services

| Service | Railway config | Description |
|---------|----------------|-------------|
| Web | `/railway.web.toml` | Migrations, static files, gevent Gunicorn, and readiness |
| Worker | `/railway.worker.toml` | Celery gevent worker |

Set each service's Config-as-Code file path in Railway's service settings. The web
service is the only migration owner: Railway runs `python manage.py migrate --noinput`
as its pre-deploy command and stops the deployment if it fails. The worker service
does not run migrations concurrently.

Gunicorn defaults to two gevent worker processes with 100 connections each. Celery
defaults to 100 greenlets. Tune these values against memory, outbound-service limits,
and PostgreSQL connection capacity.

### Environment Variables

#### Required (Railway dev & production)

| Variable | Description |
|----------|-------------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.deployed` |
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | PostgreSQL connection URL referenced from Railway Postgres |
| `REDIS_URL` | Redis connection URL referenced from Railway Redis |
| `SENTRY_DSN` | Sentry DSN for error tracking |
| `MAILGUN_API_KEY` | Mailgun API key for transactional email |
| `MAILGUN_DOMAIN` | Mailgun sender domain |
| `DEFAULT_FROM_EMAIL` | Verified sender, such as `API <api@example.com>` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated public/custom domains |

#### Railway service references

Reference the database and Redis service variables from both application services,
for example `DATABASE_URL=${{Postgres.DATABASE_URL}}` and
`REDIS_URL=${{Redis.REDIS_URL}}`. Set `DJANGO_ALLOWED_HOSTS` to the web service's
generated Railway domain and any custom domains.

These values are required by deployed settings. WSGI and Celery also require an
explicit `DJANGO_SETTINGS_MODULE`; they fail at startup instead of silently using
local settings.

#### Optional tuning

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ALLOWED_ORIGINS` | empty | Comma-separated frontend origins |
| `CSRF_TRUSTED_ORIGINS` | empty | Comma-separated trusted CSRF origins |
| `WEB_CONCURRENCY` | `2` | Gunicorn gevent worker processes |
| `WEB_WORKER_CONNECTIONS` | `100` | Connections accepted per Gunicorn worker |
| `CELERY_WORKER_CONCURRENCY` | `100` | Celery worker greenlets |
| `DATABASE_POOL_MIN_SIZE` | `0` | Connections created eagerly per process |
| `DATABASE_POOL_MAX_SIZE` | `4` | Maximum database connections per process |
| `DATABASE_POOL_TIMEOUT` | `10` | Seconds to wait for a pooled connection |
| `SENTRY_ENVIRONMENT` | Railway environment name | Override the Sentry environment |
| `SENTRY_RELEASE` | Railway commit SHA | Override the Sentry release |

#### CI (GitHub Actions)

`DATABASE_URL` and `REDIS_URL` are set in `.github/workflows/ci.yml` to point at the service containers.

### Domains and CORS

Configure domains through `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and
`CSRF_TRUSTED_ORIGINS`. Railway's deployment healthcheck hostname is added
automatically.

### Railway Setup Checklist

#### 1. Create the project and backing services

- Create a new Railway project.
- Add a **PostgreSQL** plugin (this provides `DATABASE_URL`).
- Add a **Redis** plugin (this provides `REDIS_URL`).

#### 2. Create application services

Create two services from this repository (GitHub or linked repo):

| Service name | Config-as-Code path |
|--------------|---------------------|
| `web` | `/railway.web.toml` |
| `worker` | `/railway.worker.toml` |

Set the Config-as-Code path under each service's **Settings > General > Config as
Code**. Railway reads the start command, pre-deploy command, and healthcheck from
these files.

#### 3. Set shared environment variables on both services

Use Railway variable references so secrets stay in one place:

```
DJANGO_SETTINGS_MODULE=config.settings.deployed
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
SECRET_KEY=<generate one: python -c "import secrets; print(secrets.token_urlsafe(64))">
SENTRY_DSN=<from Sentry project settings>
MAILGUN_API_KEY=<from Mailgun dashboard>
MAILGUN_DOMAIN=<your Mailgun sending domain>
DEFAULT_FROM_EMAIL=API <api@yourdomain.com>
```

#### 4. Set web-only environment variables

```
DJANGO_ALLOWED_HOSTS=<railway-generated-domain>,<custom-domain-if-any>
```

If a frontend will call the API cross-origin, also set on the web service:

```
CORS_ALLOWED_ORIGINS=https://your-frontend.com
CSRF_TRUSTED_ORIGINS=https://your-frontend.com
```

#### 5. Deploy

- Deploy the **web** service first. Its pre-deploy command runs
  `python manage.py migrate --noinput` and stops the deployment if it fails.
  `collectstatic` runs in the web container before Gunicorn starts (intentionally
  not in Railway's pre-deploy container, whose filesystem is not persisted).
- Deploy the **worker** service. It does not run migrations. Use backward-compatible
  expand/contract migrations because independently deployed services can briefly run
  different code versions. See [`ops/MIGRATIONS.md`](ops/MIGRATIONS.md) for the playbook
  and the CI checks that enforce it.

#### 6. Create a superuser

Run a one-off command via the Railway CLI or dashboard shell on the web service:

```bash
python manage.py createsuperuser
```

#### 7. Verify

- Hit `https://<your-domain>/health` -- should return `{"status": "ok"}`.
- Log into `https://<your-domain>/sadmin/` with the superuser account.
- Check Sentry for the deployment release.

### Notes

- **Celery Beat**: If you add periodic tasks to `CELERY_BEAT_SCHEDULE`, run beat as
  a third Railway service or as a one-off cron. Do not run multiple beat instances --
  they will schedule duplicate tasks.
- **Connection budget**: Gunicorn defaults to 2 workers x 4 pool connections = 8
  database connections. Celery adds up to 4 more. Railway's PostgreSQL starter plan
  has a connection limit -- check your plan and tune `DATABASE_POOL_MAX_SIZE` and
  `WEB_CONCURRENCY` accordingly. See [`ops/SCALING.md`](ops/SCALING.md) for the full
  model (the two concurrency dials, the connection-budget inequality, and how to tune).
- **Custom domains**: Add custom domains in Railway's service settings, then add them
  to `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS`.

## API

- `GET /` -- index (public)
- `GET /health` -- database readiness check (public)
- `GET /schema` -- OpenAPI schema (admin only)
- `GET /docs` -- Swagger UI (admin only)
- `GET /sadmin/` -- Django admin

Unmatched URLs return a JSON 404 using the same response shape as
`drf-standardized-errors`. Errors raised within API views are handled by
`drf-standardized-errors` directly.
