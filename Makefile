.PHONY: dev dev-infra stop build test lint clean logs

# ──────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────

dev: dev-infra  ## Start everything (infra + backend + frontend)
	@echo "Starting backend..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting frontend..."
	cd frontend && npm run dev &
	@echo ""
	@echo "✓ Backend:  http://localhost:8000"
	@echo "✓ Frontend: http://localhost:3000"
	@echo "✓ Qdrant:   http://localhost:6333/dashboard"

dev-infra:  ## Start only Qdrant + Postgres via Docker
	docker compose up -d qdrant postgres
	@echo "Waiting for Postgres..."
	@sleep 3
	@echo "✓ Infrastructure ready"

stop:  ## Stop everything
	docker compose down
	-pkill -f "uvicorn app.main:app" 2>/dev/null || true
	-pkill -f "next dev" 2>/dev/null || true

# ──────────────────────────────────────────────
# Docker (full stack)
# ──────────────────────────────────────────────

build:  ## Build all Docker images
	docker compose build

up:  ## Start all services via Docker
	docker compose up -d
	@echo ""
	@echo "✓ Frontend: http://localhost:3000"
	@echo "✓ Backend:  http://localhost:8000"
	@echo "✓ Qdrant:   http://localhost:6333/dashboard"

down:  ## Stop all Docker services
	docker compose down

logs:  ## Tail logs from all services
	docker compose logs -f

# ──────────────────────────────────────────────
# Testing & Quality
# ──────────────────────────────────────────────

test:  ## Run backend tests
	cd backend && python -m pytest tests/ -v

lint:  ## Lint backend + frontend
	cd backend && python -m ruff check .
	cd frontend && npm run lint

# ──────────────────────────────────────────────
# Setup
# ──────────────────────────────────────────────

setup:  ## First-time setup: install deps
	cd backend && pip install -r requirements.txt
	cd frontend && npm install
	@echo ""
	@echo "✓ Dependencies installed"
	@echo "→ Copy backend/.env.example to backend/.env and add your API keys"

clean:  ## Remove volumes and build artifacts
	docker compose down -v
	rm -rf frontend/.next frontend/node_modules
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"

# ──────────────────────────────────────────────

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
