# Intelligent Decision Support for Delayed Vaccination: An Expert System for the Brazilian National Immunization Program

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Framework: Flask](https://img.shields.io/badge/Framework-Flask-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Database: PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker Supported](https://img.shields.io/badge/Docker-Supported-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Standard: HL7 FHIR](https://img.shields.io/badge/Standard-HL7_FHIR-firebrick.svg)](https://hl7.org/fhir/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/FBRosito/vaccines_expert_api/graphs/commit-activity)

This repository contains the source code for the RESTful Application Programming Interface (API) and the underlying Expert System (ES) associated with the research paper: **"Apoio inteligente à decisão em atrasos vacinais: um sistema especialista para o Programa Nacional de Imunizações"**.

## 📌 Project Overview

In the Primary Health Care (APS) environment, nursing professionals face the complex task of evaluating vaccination statuses and making decisions based on multiple variables, such as intervals between doses and simultaneous administration rules. Managing incomplete or delayed vaccination schedules is challenging and can lead to programmatic errors.

This project proposes a **Knowledge-Based Expert System** accessible via a RESTful API to support decision-making in situations involving delays in the National Technical Vaccination Calendar (CTNV).

* **Accuracy:** It correctly recommends on-time schedules and resolves both simple and complex vaccination delays.

* **Transparency:** It mitigates the algorithmic "black-box" effect by generating explicit clinical justifications based on the CTNV rules for every generated recommendation.

* **Interoperability:** It adheres to standard protocols to allow seamless integration with Electronic Health Records (EHR) and mHealth applications.

## 📂 Repository Structure

```text
vaccines_expert_api
├── app/
│   ├── api/                   # REST Controllers (Vaccination Plan, Audit)
│   ├── expert_system/         # Inference Engine & Knowledge Base
│   │   └── rules/             # 15 rule modules (BCG, HPV, Covid19, Hepatite, Dengue, etc.)
│   ├── repositories/          # Database interaction (Models, Logs)
│   ├── schemas/               # Data validation schemas (e.g., vaccination_plan_schema)
│   ├── services/              # Business logic (Audit, Vaccination Plan)
│   ├── static/ & templates/   # Frontend assets and interface (HTML, CSS, JS)
│   └── utils/                 # Helper functions
├── migrations/                # Alembic database migrations
├── tests/                     # Test suite
├── docker-compose.yml         # Docker orchestration for app and database
├── Dockerfile                 # Container definition
├── entrypoint.sh              # Startup script for the container
└── requirements.txt           # Python dependencies
```

## 🚀 Key Features & Methodology

### 1. The Inference Engine & Knowledge Base

* **Technology:** Built using Python and the `Experta` library.

* **Declarative Rules:** The knowledge base is modularized into 15 rule modules, translating the Brazilian PNI guidelines into 168 executable logical rules spanning over 2,500 lines of code.

* **Conflict Resolution:** Utilizes the salience feature to prioritize execution, which is crucial for handling simultaneous administration conflicts between live attenuated virus vaccines (e.g., prioritizing MMR over Yellow Fever in children under 2 years old).

### 2. Clinical Interoperability

* **Standardization:** The API consumes and returns data using the international HL7 FHIR standard, specifically utilizing the `Patient` and `Immunization` resources.

* **National Integration:** Adheres to the Brazilian National Health Data Network (RNDS) standards and utilizes official SIPNI vaccination codes.

### 3. Traceability and Auditing

* **Persistence Layer:** A PostgreSQL database is implemented to record transaction logs. This allows for the future auditing of the generated recommendations.

* **Normative Traceability:** The `traceability/` directory contains a traceability matrix that maps 28 IN 2026 clauses to implemented rules and test cases (25 fully covered, 3 documented extensions beyond the normative text).

### 4. Validation & Testing

The inference engine was validated using a four-layer strategy:

| Layer | Description | Result |
|-------|-------------|--------|
| CE+VL | 142 deterministic equivalence-class and boundary-value test cases across 15 rule modules | 100% pass |
| Property-based | 10 clinical invariants × 800 random examples = 8,000 executions (Hypothesis) | 0 counterexamples |
| Synthetic cohort | N=5,000 age-distributed patients vs. independent reference oracle | F1=1.000, κ=1.000 for 6 vaccines |
| Baseline comparison | Motor SE vs. naïve literal IN 2026 implementation | SE dominant on Influenza (κ 0.056→1.000) and COVID-19 (κ 0.180→1.000) |

Additional metrics: 90% line coverage (875 statements); median inference latency 47 ms (p95: 117 ms; throughput: 19.1 req/s, isolated engine).

```bash
# Run the full test suite (requires .venv — see CLAUDE.md)
PYTHONPATH=tests .venv/bin/pytest tests/ -q
```

## 🛠️ Installation & Usage

The project is fully containerized. To run the API, the Expert System, and the PostgreSQL database locally, you only need Docker and Docker Compose installed.

### 1. Clone the Repository

```bash
git clone https://github.com/FBRosito/vaccines_expert_api.git
cd vaccines_expert_api
```

### 2. Build and Run via Docker

Run the following command in the root directory:

```bash
docker-compose up --build
```

This command will:

1. Build the Flask application image.
1. Spin up the PostgreSQL database container.
1. Apply any pending Alembic database migrations automatically via `entrypoint.sh`.
1. Expose the application (usually on `http://localhost:5000` or the port defined in your Caddyfile/Docker config).

### 3. Test the API

You can send HTTP POST requests with FHIR-compliant JSON payloads to the configured endpoint (e.g., `/plano-vacinal`) to receive calculated vaccination schedules, or access the frontend interface via the browser if configured in `app/templates/index.html`.

## 🔒 Limitations & Clinical Disclaimer

* **Complementary Tool:** This technological solution is designed to optimize workflows and support decision-making, not to replace the clinical judgment and ethical autonomy of nursing professionals.

* **Data Dependency:** The system is deterministic; the accuracy of its recommendations depends entirely on the correct input of the patient's prior vaccination history.

* **Scope:** The current rule modules apply to immunocompetent individuals and routine demands; it does not currently handle post-exposure prophylaxis or schemes for immunosuppressed populations.

## 👥 Authors

* **Fernando Barcelos Rosito**
* Muriel Figueredo Franco
* Juliana Silva Herbert
* **Adriana Aparecida Paz**

**Affiliation:** Federal University of Health Sciences of Porto Alegre (UFCSPA), Brazil. University of Zurich (UZH), Switzerland.
