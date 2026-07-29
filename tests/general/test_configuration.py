import os
import subprocess
import sys


def _run_django(code: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        env=env,
        text=True,
    )


def _deployed_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "DJANGO_SETTINGS_MODULE": "config.settings.deployed",
            "DJANGO_READ_DOT_ENV_FILE": "False",
            "SECRET_KEY": (
                "test-only-secret-key-with-more-than-fifty-unique-characters-123456789"
            ),
            "DATABASE_URL": "sqlite://:memory:",
            "REDIS_URL": "redis://localhost:6379/0",
            "SENTRY_DSN": "",
            "MAILGUN_API_KEY": "placeholder",
            "MAILGUN_DOMAIN": "example.com",
            "DEFAULT_FROM_EMAIL": "API <noreply@example.com>",
            "DJANGO_ALLOWED_HOSTS": "example.com",
        },
    )
    return env


def test_wsgi_requires_explicit_settings_module() -> None:
    env = os.environ.copy()
    env.pop("DJANGO_SETTINGS_MODULE", None)

    result = _run_django("import config.wsgi", env)

    assert result.returncode != 0
    assert "DJANGO_SETTINGS_MODULE must be set" in result.stderr


def test_deployed_settings_require_database_url() -> None:
    env = _deployed_env()
    env.pop("DATABASE_URL")

    result = _run_django("import django; django.setup()", env)

    assert result.returncode != 0
    assert "DATABASE_URL" in result.stderr


def test_deployed_settings_require_redis_url() -> None:
    env = _deployed_env()
    env.pop("REDIS_URL")

    result = _run_django("import django; django.setup()", env)

    assert result.returncode != 0
    assert "REDIS_URL" in result.stderr
