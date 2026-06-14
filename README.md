# Token Monitor

Personal dashboard to monitor AI coding tool subscriptions and token usage.

## Overview

Token Monitor is a full-stack web application that helps you track and visualize token consumption across AI coding tools (e.g., Claude Code, OpenAI Codex). It provides:

- Real-time token usage dashboards with charts and trends
- Multi-account and multi-tool subscription management
- Historical data tracking and cost estimation
- Plugin-based architecture for adding new AI tool integrations

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy (async), SQLite, APScheduler
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Recharts, Zustand, React Query
- **Testing**: pytest + pytest-asyncio

## Project Structure

```
├── backend/              # FastAPI application
│   ├── alembic/          # Database migrations
│   ├── app/
│   │   ├── main.py       # Application entry point
│   │   ├── routers/      # API route handlers
│   │   ├── services/     # Business logic
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── plugins/      # AI tool integrations
│   │   └── scheduler/    # Background jobs
│   └── tests/
├── frontend/             # React + Vite frontend
│   ├── src/
│   │   ├── pages/        # Route pages
│   │   ├── components/   # Reusable UI components
│   │   ├── api/          # API client layer
│   │   ├── hooks/        # Custom React hooks
│   │   └── stores/       # Zustand state stores
│   └── dist/             # Built assets
└── Makefile              # Development shortcuts
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd token-monitor

# Install dependencies (backend + frontend)
make install
```

### Development

```bash
# Start both backend and frontend
make dev

# Or start individually
make backend   # API at http://127.0.0.1:8000
make frontend  # Dev server (port auto-assigned)
```

### Environment Setup

Copy and edit the backend environment file:

```bash
cp backend/.env.example backend/.env
```

## API Documentation

Once the backend is running, visit `http://127.0.0.1:8000/docs` for the interactive Swagger UI.

## License

MIT
