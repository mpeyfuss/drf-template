# Format code
fmt:
	uv run ruff format .

# lint code
lint:
	uv run ruff check --fix .

# Django
# Create a new app under apps/ with the correct AppConfig name.
# usage: make startapp name=<app_name>
startapp:
	mkdir -p apps/$(name)
	uv run python manage.py startapp $(name) apps/$(name) --template apps/_template

server:
	uv run python manage.py runserver

migrations:
	uv run python manage.py makemigrations

migrate:
	uv run python manage.py migrate

# Check migrations are complete and backward-compatible (expand/contract safe).
# Lints only migrations added since origin/dev (run `git fetch` first).
check-migrations:
	uv run python manage.py makemigrations --check --dry-run
	uv run python manage.py lintmigrations --project-root-path . --git-commit-id origin/dev

# Celery
worker:
	DJANGO_SETTINGS_MODULE=config.settings.local DJANGO_READ_DOT_ENV_FILE=True CELERY_TASK_ALWAYS_EAGER=False uv run celery -A config worker -l info --pool gevent --concurrency $${CELERY_WORKER_CONCURRENCY:-100}

beat:
	DJANGO_SETTINGS_MODULE=config.settings.local DJANGO_READ_DOT_ENV_FILE=True CELERY_TASK_ALWAYS_EAGER=False uv run celery -A config beat -l info

# Tests
test:
	uv run pytest

coverage:
	uv run coverage run -m pytest
	uv run coverage report
