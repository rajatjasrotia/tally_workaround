# Tally Workaround - Inventory & Invoicing

This repository contains a minimal scaffold for an inventory and invoicing web app.

Stack:
- Backend: FastAPI (Python) with SQLModel (SQLite by default)
- Frontend: Plain JavaScript + HTML served by the backend
- Run: Docker or local Python environment

What's included:
- backend/: FastAPI app, models, seed script, Dockerfile
- frontend/: simple JS UI to list inventory and create invoices
- docker-compose.yml: runs the backend service

Quick start (local, without Docker):

1. Create and activate a Python venv

   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows

2. Install dependencies

   pip install -r backend/requirements.txt

3. Run the app (it will create database and seed sample items)

   cd backend
   python -m app.main

   # or
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

4. Open browser: http://127.0.0.1:8000/

Docker (optional):

  docker-compose up --build

Notes:
- The backend serves the frontend static files. API root is under /api.
- Database: SQLite file backend/database.db (suitable for demo). You can switch to Postgres later by updating database URL in environment.
