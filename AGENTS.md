# Repository Guidelines

## Project Structure & Module Organization

- `backend/`: Python/FastAPI service and Backtrader engine. Entry points are `backend/main.py` (ASGI server) and `backend/api.py` (exports app).
- `backend/src/`: main backend modules, organized by layer: `routes/` (HTTP API), `service/` (business orchestration), `brokers/` (CCXT/IBKR adapters), `db/` (SQLAlchemy models), `config/` and `utils/`.
- `backend/strategy/`: strategy templates loaded dynamically by name (e.g., `sma_cross.py`).
- `backend/resources/`: runtime assets, configs, and built frontend copy at `backend/resources/frontend/`.
- `frontend/`: React 18 + Vite SPA. Source is under `frontend/src/`, built output in `frontend/dist/`.

Before changing files, check for any `*.md` “directory description” in that folder (e.g., `backend/src/src.md`) and follow its scoped conventions.

## Build, Test, and Development Commands

- `build.bat`: full build; installs deps and builds frontend, then copies `frontend/dist/` into backend resources.
- `start_dev.bat`: starts backend (port 8000) and Vite dev server (port 5173) with proxying.
- Backend only: `cd backend; pip install -r requirements.txt; python main.py`.
- Frontend only: `cd frontend; npm install; npm run dev | build | lint | preview`.
- Docker: `docker-compose up --build` (serves app on port 8020).


## **Working Rules**

- Before modifying any file, check whether the file’s current folder contains a `*.md` “directory description” document. If it exists, **read it first** and follow its stated responsibilities, conventions, and non‑functional requirements when making changes.

## Coding Style & Naming Conventions

- Python: follow PEP 8, 4-space indentation, type hints where practical. Keep API validation in `routes/`, logic in `service/`.
- JavaScript/React: 2-space indentation, functional components, hooks-first patterns. Run `npm run lint` before PRs.
- Strategies: one class per file inheriting `bt.Strategy`; filenames use snake_case and match API strategy names.

## Testing Guidelines

There is no committed test suite yet. If adding tests, prefer `pytest` for backend and colocate under `backend/tests/`, naming files `test_*.py`. For frontend, follow Vite/React testing norms and document any new scripts in `frontend/package.json`.

## Commit & Pull Request Guidelines

- Commits use Conventional Commits (`feat:`, `fix:`, `chore:`, etc.) in present tense.
- PRs should include: brief summary, linked issue (if any), key screenshots for UI changes, and notes on migrations/config updates.

## Security & Configuration Tips

- Secrets must live in env files/variables only; update `backend/.env.template` when introducing new keys.
- Strategy names and file paths must remain sanitized; do not bypass existing validation.
