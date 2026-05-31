VENV     := .venv
PYTHON   := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip
PYTEST   := $(VENV)/bin/pytest
FLASK    := $(VENV)/bin/flask

TESTS_DIR := tests
RULES_DIR := app/expert_system/rules

.PHONY: help venv install migrate run test test-rules test-invariants test-cohort \
        test-baseline test-performance test-coverage docker-up docker-down clean

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Setup"
	@echo "  venv          Create .venv"
	@echo "  install       Install dependencies into .venv"
	@echo "  migrate       Apply database migrations"
	@echo ""
	@echo "Run"
	@echo "  run           Start Flask dev server (port 5000)"
	@echo "  docker-up     Start full stack via Docker Compose"
	@echo "  docker-down   Stop Docker Compose stack"
	@echo ""
	@echo "Tests"
	@echo "  test          Full test suite"
	@echo "  test-rules    CE+VL deterministic tests only (~5 s)"
	@echo "  test-invariants  Property-based invariants (~30 s)"
	@echo "  test-cohort   Synthetic cohort N=5000 (~60 s)"
	@echo "  test-baseline Baseline comparison vs. IN 2026 (~60 s)"
	@echo "  test-performance  Latency benchmark N=200 (~30 s)"
	@echo "  test-coverage Rule module coverage report"

# ── Setup ─────────────────────────────────────────────────────────────────────

venv:
	python3 -m venv $(VENV)
	@echo "venv created at $(VENV)"

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

migrate:
	FLASK_APP=run.py $(FLASK) db upgrade

# ── Run ───────────────────────────────────────────────────────────────────────

run:
	FLASK_APP=run.py FLASK_ENV=development $(FLASK) run

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

# ── Tests ─────────────────────────────────────────────────────────────────────

test:
	PYTHONPATH=$(TESTS_DIR) $(PYTEST) $(TESTS_DIR)/ -q

test-rules:
	PYTHONPATH=$(TESTS_DIR) $(PYTEST) $(TESTS_DIR)/test_rules_*.py -q

test-invariants:
	PYTHONPATH=$(TESTS_DIR) $(PYTEST) $(TESTS_DIR)/test_invariants.py -v

test-cohort:
	PYTHONPATH=$(TESTS_DIR) $(PYTEST) $(TESTS_DIR)/test_cohort.py -v -s

test-baseline:
	PYTHONPATH=$(TESTS_DIR) $(PYTEST) $(TESTS_DIR)/test_baseline_comparison.py -v -s

test-performance:
	PYTHONPATH=$(TESTS_DIR) $(PYTEST) $(TESTS_DIR)/test_performance.py -v -s

test-coverage:
	PYTHONPATH=$(TESTS_DIR) $(PYTEST) $(TESTS_DIR)/test_rules_*.py \
		--cov=$(RULES_DIR) --cov-report=term-missing -q

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
