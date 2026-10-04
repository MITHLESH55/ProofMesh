# ProofMesh — Development Guide (Phase 1)

## 1. Prerequisites
- Python 3.11+
- Node.js 20+ & npm 10+
- Docker & Docker Compose
- PostgreSQL 15+ & Redis 7+ (or use Docker Compose)

---

## 2. Quickstart with Docker Compose

To start the entire containerized ProofMesh stack:

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Build and start services (Postgres, Redis, Backend, Worker, Frontend)
docker compose up --build
```

- **Frontend**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000/api/v1`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

---

## 3. Local Development (Without Docker)

### 3.1 Backend Setup
```bash
cd backend
python -m venv .venv
# Activate virtual environment
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run migrations & seed demo data
alembic upgrade head
python -m scripts.seed

# Start FastAPI API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In a separate terminal, start the background worker
python -m app.workers.worker
```

### 3.2 Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 4. Default Seed Credentials
- **Admin User**: `demo@example.com`
- **Password**: `Password123!`
- **Organization**: `ProofMesh Demo Enterprise`
- **Demo Repository**: `proofmesh-demo-org/demo-enterprise` (GitHub ID: `987654321`)
