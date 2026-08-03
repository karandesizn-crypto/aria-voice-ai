.PHONY: help install-web install-api install-agent test-web test-api test-agent migrate

help:
	@echo "Targets: install-web install-api install-agent test-web test-api test-agent migrate"

install-web:
	cd apps/web && npm install

install-api:
	cd apps/api && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

install-agent:
	cd apps/agent && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

migrate:
	cd apps/api && . .venv/bin/activate && alembic upgrade head

test-web:
	cd apps/web && npm run test

test-api:
	cd apps/api && . .venv/bin/activate && pytest

test-agent:
	cd apps/agent && . .venv/bin/activate && pytest
