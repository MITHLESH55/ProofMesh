# ProofMesh

> **AI-Native Software Change Assurance & Reliability Platform**

[![Phase 1 Status](https://img.shields.io/badge/Phase%201-VERIFIED-success.svg)](#phase-status)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-teal.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue.svg)](https://typescriptlang.org)

---

## 1. Problem & Overview

Modern engineering organizations deploy software at unprecedented velocity. Yet, answering fundamental questions about what changed, what it impacts, and whether all invariants remain preserved is often manual and fragmented.

**ProofMesh** is an AI-Native Software Change Assurance Platform.

While the complete product answers:
> *What changed, why did it change, what can it affect, what must remain true, what evidence verifies it, and what happened after deployment?*

**Phase 1 establishes the trustworthy boundary around software-change ingestion**:
# WHAT CHANGED?

---

## 2. Phase 1 Architecture & Flow

```text
Developer
    ↓
GitHub Pull Request Event
    ↓
POST /api/v1/webhooks/github
    ↓
HMAC-SHA256 Verification & Idempotency Check
    ↓
Atomic DB Persistence (Repo / PR / Change / AnalysisRun / AuditLog)
    ↓
Redis Analysis Queue
    ↓
Background Analysis Worker (Ingestion Validation)
    ↓
Real-Time Status & Audit Trail
    ↓
React + TypeScript Dashboard
```

---

## 3. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, React Router v6
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic
- **Persistence & Queue**: PostgreSQL 15+, Redis 7+
- **Security**: Timing-safe HMAC-SHA256 signature verification, bcrypt password hashing, JWT authentication, RBAC (`ADMIN`, `ENGINEER`, `VIEWER`)
- **Containerization**: Docker, Docker Compose

---

## 4. Quickstart with Docker Compose

Run the entire containerized environment with a single command:

```bash
# 1. Clone & enter repository
cd ProofMesh

# 2. Copy environment configuration
cp .env.example .env

# 3. Start stack (Postgres, Redis, Backend, Worker, Frontend)
docker compose up --build
```

Access points:
- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 5. Development Credentials & Seed Data

The database initializes with seed demo fixtures:
- **Email**: `demo@example.com`
- **Password**: `Password123!`
- **Role**: `ADMIN`
- **Demo Organization**: `ProofMesh Demo Enterprise`
- **Demo Repository**: `proofmesh-demo-org/demo-enterprise` (GitHub ID: `987654321`)

---

## 6. GitHub Webhook Setup Guide

To connect a GitHub repository or organization to ProofMesh:

1. **Payload URL**: `https://<your-domain-or-tunnel>/api/v1/webhooks/github`
2. **Content type**: `application/json`
3. **Secret**: Set to the value of `GITHUB_WEBHOOK_SECRET` in your `.env`
4. **Events to trigger**:
   - `Pull requests` (`opened`, `synchronize`, `reopened`, `closed`)

---

## 7. Running Automated Tests

Run the complete test suite across Unit, API, Integration, and End-to-End flows:

```bash
# Run all backend & E2E tests
python -m pytest tests -v

# Run frontend build & typecheck
cd frontend && npm run build
```

---

## 8. Repository Structure

```text
proofmesh/
├── frontend/             # React 18 + TypeScript + Vite UI
├── backend/              # FastAPI + SQLAlchemy + Redis Worker
│   ├── app/
│   │   ├── api/v1/       # REST API endpoints
│   │   ├── core/         # Config, security, logging, errors
│   │   ├── db/           # Session & engine setup
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic v2 schemas
│   │   ├── repositories/ # Data access layer
│   │   ├── services/     # Ingestion, Auth, Changes, Jobs
│   │   └── workers/      # Background analysis worker
│   └── alembic/          # Database migrations
├── tests/                # Unit, API, Integration, E2E tests
├── infrastructure/       # Dockerfiles and web server configs
├── docs/                 # Complete architectural documentation
└── docker-compose.yml    # Full-stack composition
```

---

## 9. Documentation Index

- [Master System Specification](docs/MASTER_SPEC.md)
- [Phase 1 Specification](docs/PHASE_1.md)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [REST API Reference](docs/API.md)
- [Security & Threat Model](docs/SECURITY.md)
- [Development Workflow](docs/DEVELOPMENT.md)
- [Testing Strategy](docs/TESTING.md)
- [Phase Status Report](docs/PHASE_STATUS.md)

---

## 10. Phase Status

- **Phase 1 (Foundation & Ingestion)**: **`STATUS: VERIFIED`**
- **Phase 2 (Semantic Change Analysis)**: **`NOT STARTED`**
