.PHONY: install dev test lint format migrate seed clean docker-up docker-down

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-worker:
	cd backend && python -m app.workers.worker

dev-frontend:
	cd frontend && npm run dev

dev:
	docker compose up --build

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

test-backend:
	cd backend && pytest ../tests/backend -v

test-frontend:
	cd frontend && npm test -- --run

test-e2e:
	cd backend && pytest ../tests/e2e -v

test: test-backend test-e2e

lint-backend:
	cd backend && flake8 app ../tests || true
	cd backend && mypy app || true

lint-frontend:
	cd frontend && npm run lint || true

lint: lint-backend lint-frontend

format:
	cd backend && black app ../tests || true
	cd backend && isort app ../tests || true

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m scripts.seed

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache frontend/dist frontend/node_modules backend/.venv
