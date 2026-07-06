.PHONY: install lint typecheck monetary-float-guard refactor-quality-thresholds workflow-action-runtime agent-quality-evidence demo-certification openapi-gate migration-smoke migration-apply test test-unit test-integration test-coverage test-e2e test-e2e-live security-audit check ci ci-local ci-local-docker ci-local-docker-down run run-canonical clean docker-up docker-down e2e-up e2e-down

install:
	python -m pip install -e ".[dev]"

lint:
	python -m ruff check .
	python -m ruff format --check .
	$(MAKE) monetary-float-guard
	$(MAKE) refactor-quality-thresholds
	$(MAKE) workflow-action-runtime
	$(MAKE) agent-quality-evidence

monetary-float-guard:
	python scripts/check_monetary_float_usage.py

refactor-quality-thresholds:
	python scripts/check_refactor_quality_thresholds.py

workflow-action-runtime:
	python scripts/check_workflow_action_runtime.py

agent-quality-evidence:
	python scripts/check_agent_quality_evidence.py

demo-certification:
	python scripts/certify_demo_readiness.py

typecheck:
	python -m mypy src

openapi-gate:
	python -m pytest tests/contract/test_workbench_contract.py -q

migration-smoke:
	python scripts/migration_contract_check.py --mode no-schema

migration-apply:
	python scripts/migration_contract_check.py --mode no-schema

security-audit:
	# PYSEC-2026-161 is tracked as a governed temporary exception: FastAPI still
	# constrains Starlette below the fixed 1.0.1 line, so no compatible upgrade is
	# available for this service yet. Remove this ignore when FastAPI supports it.
	python -m pip_audit --ignore-vuln PYSEC-2026-161 -r requirements-audit.txt

test:
	$(MAKE) test-unit

test-unit:
	python -m pytest tests/unit tests/contract

test-integration:
	python -m pytest tests/integration

test-coverage:
	python -m pytest tests/unit tests/contract tests/integration --cov=src/app --cov-branch --cov-report=term-missing --cov-fail-under=84

test-e2e:
	python -m pytest tests/e2e -q

e2e-up:
	docker compose -f docker-compose.e2e.yml up -d --build

e2e-down:
	docker compose -f docker-compose.e2e.yml down -v --remove-orphans

test-e2e-live:
	python -m pytest tests/e2e/test_platform_capabilities_live.py -q

check: lint typecheck openapi-gate test

ci: lint typecheck openapi-gate migration-smoke test-integration test-coverage security-audit

ci-local: check test-integration

ci-local-docker:
	docker compose -f docker-compose.ci-local.yml up --build --abort-on-container-exit --exit-code-from ci-local ci-local

ci-local-docker-down:
	docker compose -f docker-compose.ci-local.yml down -v --remove-orphans

run:
	uvicorn app.main:app --reload --app-dir src --port 8100

run-canonical:
	uvicorn app.main:app --reload --app-dir src --host 0.0.0.0 --port 8111

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

clean:
	python scripts/clean_generated_artifacts.py
