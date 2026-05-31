# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Docker (recommended)
```bash
# Full stack: Flask API + PostgreSQL + Caddy HTTPS proxy
docker-compose up --build
```

### Manual development
```bash
pip install -r requirements.txt

# Requires a running PostgreSQL instance configured via .env
flask db upgrade       # apply migrations
flask run              # development server on :5000
```

### Database migrations
```bash
flask db migrate -m "description"
flask db upgrade
```

### Testing

The test suite lives in `tests/` and requires a `.venv` created at the project root (see CLAUDE.md setup notes). All tests run without a database — the inference engine is exercised in isolation via `unittest.mock`.

```bash
# Run the full suite (142 CE+VL + invariants + cohort + baseline + performance)
PYTHONPATH=tests .venv/bin/pytest tests/ -q

# CE+VL deterministic tests only (~5 s)
PYTHONPATH=tests .venv/bin/pytest tests/test_rules_*.py -q

# Property-based invariants (Hypothesis, 800 examples each, ~30 s)
PYTHONPATH=tests .venv/bin/pytest tests/test_invariants.py -v

# Synthetic cohort N=5,000 — reports F1 and κ per vaccine (~60 s)
PYTHONPATH=tests .venv/bin/pytest tests/test_cohort.py -v -s

# Baseline comparison Motor SE vs. literal IN 2026 (~60 s)
PYTHONPATH=tests .venv/bin/pytest tests/test_baseline_comparison.py -v -s

# Performance benchmark N=200 — reports latency distribution (~30 s)
PYTHONPATH=tests .venv/bin/pytest tests/test_performance.py -v -s

# Code coverage for rule modules
PYTHONPATH=tests .venv/bin/pytest tests/test_rules_*.py \
  --cov=app/expert_system/rules --cov-report=term-missing -q
```

**Expected outcomes:**
- CE+VL: 142 passed, 0 failed
- Invariants: 0 counterexamples across 8,000 executions
- Cohort: F1=1.000, κ=1.000 for BCG, Dengue, Influenza, COVID-19, Pneumocócica 23V, Febre Amarela
- Coverage: ≥ 90% of 875 statements in `app/expert_system/rules/`

To test the HTTP API manually:
```bash
curl -X POST http://localhost:5000/api/simulador/plano-vacinal \
  -H "Content-Type: application/json" \
  -d @<fhir_bundle.json>
```

## Architecture

**Layered structure:**
```
Controller (app/api/)
  → Service (app/services/)
    → Expert System (app/expert_system/)
  → Repository (app/repositories/)
```

**Application factory** in `app/__init__.py`; entry point is `run.py`. Flask blueprints register controllers under the `/api` prefix.

**Configuration** (`config.py`) is environment-driven via `.env`. PostgreSQL connection is assembled from `POSTGRES_*` env vars. Three environments: `default`, `development`, `production`.

**Entrypoint in Docker** (`entrypoint.sh`): waits for PostgreSQL, runs `flask db upgrade`, then starts Gunicorn.

## Expert System

The core logic lives in `app/expert_system/rules/`. It uses **Experta** (Python forward-chaining rule engine, similar to CLIPS).

**15 vaccine rule modules** (`bcg.py`, `hepatitis_b.py`, `penta_dtp.py`, `vip.py`, `rotavirus.py`, `pneumo10.py`, `pneumo23.py`, `meningo.py`, `covid19.py`, `hepatitis_a.py`, `hpv.py`, `influenza.py`, `dt_adult.py`, `dengue.py`, `live_attenuated_viruses.py`) plus `fatos.py` (fact class definitions).

**Dynamic engine assembly** — all 15 modules are merged into a single `KnowledgeEngine` at runtime:
```python
DynamicEngine = type('DynamicEngine', (*rule_modules, KnowledgeEngine), {})
```
This enables cross-vaccine interaction rules (e.g., live-virus spacing).

**Fact types:**

| Fact | Direction | Meaning |
|------|-----------|---------|
| `Paciente` | input | patient birth date |
| `Idade` | input | age in years/months/days |
| `DoseAplicada` | input | prior vaccination (code, date, dose number) |
| `RecomendacaoImediata` | output | apply this dose now |
| `AgendamentoFuturo` | output | schedule for a future date |
| `Contraindicacao` | output | do not apply (with reason) |
| `EsquemaCompleto` | output | vaccination scheme finished |
| `ConflitoResolvido` | internal | tracks resolved live-virus conflicts |

**Conflict resolution**: `live_attenuated_viruses.py` uses `salience=100` to prioritize MMR (SCR) over Yellow Fever when both are needed in children < 2 years, spacing them 30 days apart.

## FHIR & Vaccine Codes

The API speaks **HL7 FHIR** externally and a flat internal format internally. The translation happens in `app/api/vaccination_plan_controller.py`.

- **External codes**: SIPNI/RNDS codes (e.g., `"15"` = BCG, `"42"` = Penta)
- **Mapping tables**: `DE_PARA_SIPNI_INTERNO` (SIPNI → internal) in `vaccination_plan_controller.py`; `MAPA_NOME_PARA_SIPNI` (internal → SIPNI) in `vaccination_plan_service.py`

Input: FHIR Bundle with `Patient` + `Immunization` resources.
Output: FHIR `ImmunizationRecommendation` Bundle.

## Persistence

Single audit table `plano_vacinal_logs` (model in `app/repositories/models.py`) stores the full FHIR request and response as `JSONB` columns. All requests are logged — this is a non-destructive audit trail.

Rate limits (Flask-Limiter): 10 req/min on `POST /api/simulador/plano-vacinal`, 2000 req/day globally.
