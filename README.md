# DRF Template

An opinionated template repository for building REST APIs with [Django Rest Framework](https://www.django-rest-framework.org/).

## Getting Started
- Get started by cloning the repo.
- Use [uv](https://docs.astral.sh/uv/getting-started/installation/) to install the dependencies by running `uv sync`.
- Create a `.env` file copying `.env.example` and fill out the values you need.
- Initialize the git repository (if needed) by running `git init`
- Install the pre-commit hooks by running `uv run pre-commit install`
- Find all `TODO` comments to see what needs to be updated

## Opinions
- The python version set in `.python-version`. Update to whatever you want.
- The main configuration is in the `api` folder. Settings are set per environment. Names are self-explanatory.
- Expects a postgres database outside of unit testing.
- DRF is setup to use a custom standardized error response that is useful for 400 validation errors.
- It is expected to use synchronous python and gunicorn + gevent workers at deployment.
- There is a custom user model based on `AbstractUser` from django.
- Testing uses `pytest` instead of `unittest`.
- If you want to run things locally, run `make run-infra` and then `make run-server`.
- It is setup for simple [Railway](https://railway.com) deployment but easily adaptable to any cloud provider really.
- Common commands are in the Makefile. Use them.

## Adding more
- Background tasks can be built using [celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) or [huey](https://huey.readthedocs.io/en/latest/). I recommend huey for a simpler experience. Both can use a Redis or KeyVal broker.
- 