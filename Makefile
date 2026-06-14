.PHONY: dev backend frontend install clean

# Run both backend and frontend
dev: backend frontend

# Start backend
backend:
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Start frontend
frontend:
	cd frontend && npm run dev

# Install dependencies
install:
	cd backend && python3.12 -m venv venv && source venv/bin/activate && pip install -r <(python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))")
	cd frontend && npm install

# Clean
clean:
	rm -rf backend/token_monitor.db backend/__pycache__ frontend/node_modules frontend/dist
