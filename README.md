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
base.py        -- shared foundation (Django, DRF, Celery, db-backed sessions)
  ├── _deployed.py -- shared Railway config (Sentry, Mailgun, SSL, Redis cache, cached_db sessions); not selected directly
  │     ├── prod.py  -- production (hardcoded hosts/origins, Lax apex cookies)
  │     └── dev.py   -- dev (hardcoded hosts/origins, SameSite=None cookies for cross-site preview/localhost)
  ├── local.py     -- local development (DEBUG, console email, eager Celery)
  └── test.py      -- test runner (MD5 hasher, in-memory email)
```

Deployed hosts, CORS/CSRF origins, DB pool sizes, cookie policy, and the Mailgun
sender domain / from-address are hardcoded in `dev.py`/`prod.py` -- edit them there.
Only secrets and Railway-injected connection strings come from the environment.

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

Admin is available at `/admin`.

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
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` (production) or `config.settings.dev` (dev environment) |
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | PostgreSQL connection URL referenced from Railway Postgres |
| `REDIS_URL` | Redis connection URL referenced from Railway Redis |


#### Optional secrets

| Variable | Description |
|----------|-------------|
| `SENTRY_DSN` | Enables Sentry error tracking when set |
| `MAILGUN_API_KEY` | Enables Anymail/Mailgun transactional email when set |
| `SENTRY_RELEASE` | Overrides the Sentry release (defaults to the Railway commit SHA) |

#### Railway service references

Reference the database and Redis service variables from both application services,
for example `DATABASE_URL=${{Postgres.DATABASE_URL}}` and
`REDIS_URL=${{Redis.REDIS_URL}}`.

These secrets are required by deployed settings. WSGI and Celery also require an
explicit `DJANGO_SETTINGS_MODULE`; they fail at startup instead of silently using
local settings. Everything else (hosts, CORS/CSRF origins, DB pool sizes, cookie
policy, Mailgun sender domain, from-address) is hardcoded in `dev.py`/`prod.py`.

#### Service tuning (set on the relevant Railway service)

| Variable | Default | Description |
|----------|---------|-------------|
| `WEB_CONCURRENCY` | `2` | Gunicorn gevent worker processes |
| `WEB_WORKER_CONNECTIONS` | `100` | Connections accepted per Gunicorn worker |
| `CELERY_WORKER_CONCURRENCY` | `100` | Celery worker greenlets |

#### CI (GitHub Actions)

`DATABASE_URL` and `REDIS_URL` are set in `.github/workflows/ci.yml` to point at the service containers.

### Domains and CORS

Hosts, CORS/CSRF origins, and cookie policy are **hardcoded** in `config/settings/prod.py`
and `config/settings/dev.py` (search for `# TODO` to find the placeholders to replace).
Railway's deployment healthcheck hostname is included automatically.

Cookie policy differs by environment. **Production** (`prod.py`) uses `SameSite=Lax`
cookies with `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` set to the apex domain (e.g.
`.luci.app`) so the frontend and API subdomains share the session. **Dev** (`dev.py`)
uses `SameSite=None; Secure` cookies so a `localhost` frontend and Firebase Hosting
preview URLs (matched by `CORS_ALLOWED_ORIGIN_REGEXES`) can authenticate cross-site.
Both require `credentials: "include"` on the frontend's fetch calls, and the
`csrftoken` from `GET /auth/csrf` echoed as the `X-CSRFToken` header on unsafe requests.

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

#### 3. Set environment variables on both services

Use `config.settings.prod` on the production environment and `config.settings.dev`
on the dev environment. Reference the backing-service secrets so they stay in one
place:

```
DJANGO_SETTINGS_MODULE=config.settings.prod   # config.settings.dev on the dev environment
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
SECRET_KEY=<generate one: python -c "import secrets; print(secrets.token_urlsafe(64))">
SENTRY_DSN=<from Sentry project settings; optional>
MAILGUN_API_KEY=<from Mailgun dashboard; optional>
```

Hosts, CORS/CSRF origins, and the Mailgun sender domain / from-address are not env
vars -- edit the `# TODO` placeholders in `config/settings/prod.py` and
`config/settings/dev.py` to match your real domains before deploying.

#### 4. Deploy

- Deploy the **web** service first. Its pre-deploy command runs
  `python manage.py migrate --noinput` and stops the deployment if it fails.
  `collectstatic` runs in the web container before Gunicorn starts (intentionally
  not in Railway's pre-deploy container, whose filesystem is not persisted).
- Deploy the **worker** service. It does not run migrations. Use backward-compatible
  expand/contract migrations because independently deployed services can briefly run
  different code versions. See [`ops/MIGRATIONS.md`](ops/MIGRATIONS.md) for the playbook
  and the CI checks that enforce it.

#### 5. Create a superuser

Run a one-off command via the Railway CLI or dashboard shell on the web service:

```bash
python manage.py createsuperuser
```

#### 6. Verify

- Hit `https://<your-domain>/health` -- should return `{"status": "ok"}`.
- Log into `https://<your-domain>/admin` with the superuser account.
- Check Sentry for the deployment release.

### Notes

- **Celery Beat**: If you add periodic tasks to `CELERY_BEAT_SCHEDULE`, run beat as
  a third Railway service or as a one-off cron. Do not run multiple beat instances --
  they will schedule duplicate tasks.
- **Connection budget**: Gunicorn defaults to 2 workers x 4 pool connections = 8
  database connections. Celery adds up to 4 more. Railway's PostgreSQL starter plan
  has a connection limit -- check your plan and tune the pool `max_size`
  (`configure_db_pool` in `dev.py`/`prod.py`) and `WEB_CONCURRENCY` accordingly.
  See [`ops/SCALING.md`](ops/SCALING.md)
  for the full model (the two concurrency dials, the connection-budget inequality, and how to tune).
- **Custom domains**: Add custom domains in Railway's service settings, then add them
  to `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` in
  `config/settings/prod.py` (or `dev.py`).

## Authentication

The default is **Django session authentication** (DRF's `SessionAuthentication`),
backed by the `cached_db` session engine on deployed environments: sessions are read
from the Redis cache first and fall back to the database on a miss, while writes go to
both. This gives you fast, cache-speed reads without making Redis a source of truth --
sessions survive a cache flush by reloading from the database. For the large majority
of web apps this scales just fine out of the box.

Because sessions ride on cookies, unsafe requests are CSRF-protected. A decoupled SPA
bootstraps the token from `GET /auth/csrf`, which sets the `csrftoken` cookie and returns
the token to echo as the `X-CSRFToken` header on POST/PUT/PATCH/DELETE. The cookie is
intentionally not `HttpOnly` so the frontend can read it (the CSRF token is not a secret
in the double-submit model). See [Domains and CORS](#domains-and-cors) for the per-environment
cookie policy.

Consider a different strategy when session cookies stop fitting:

- **Fully cross-site frontend** (no shared apex domain, or a third-party embed) where
  `SameSite=None` cookies are awkward or blocked.
- **Native mobile / non-browser clients** that have no cookie jar and want a bearer token.

In those cases reach for a token strategy such as
[django-rest-knox](https://github.com/jazzband/django-rest-knox) (server-side, revocable
tokens -- a good middle ground) or JWTs via
[djangorestframework-simplejwt](https://github.com/jazzband/djangorestframework-simplejwt)
(stateless, but revocation and rotation are on you). Pick based on whether you need
server-side revocation and how much token lifecycle you want to own.

## API

- `GET /` -- index (public)
- `GET /health` -- database readiness check (public)
- `GET /auth/csrf` -- set the CSRF cookie and return the token (public)
- `GET /schema` -- OpenAPI schema (admin only)
- `GET /docs` -- Swagger UI (admin only)
- `GET /admin` -- Django admin

Unmatched URLs return a JSON 404 using the same response shape as
`drf-standardized-errors`. Errors raised within API views are handled by
`drf-standardized-errors` directly.

## License

Released under the [MIT License](LICENSE).
