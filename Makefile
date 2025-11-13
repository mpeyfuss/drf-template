#####################################
### RUFF
#####################################
fmt:
	uv run ruff format .

# lint code
lint: fmt
	uv run ruff check --fix .

#####################################
### DJANGO
#####################################
migrations:
	uv run python manage.py makemigrations

migrate:
	uv run python manage.py migrate

superuser:
	uv run python manage.py createsuperuser

run-infra:
	docker compose -f docker-compose.local.yaml up -d

stop-infra:
	docker compose -f docker-compose.local.yaml down

run-server:
	uv run gunicorn app.wsgi -k gevent --bind localhost:8000 --reload

#####################################
### TESTING
#####################################
test:
	uv run pytest

unit-test:
	uv run pytest tests/unit

func-test:
	uv run pytest tests/functional