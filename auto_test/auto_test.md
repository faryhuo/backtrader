# auto_test folder guide

Purpose: hold automated integration/smoke/system test cases that exercise the app end‑to‑end or via public APIs. Unit tests should live alongside the code they cover (e.g., `backend/tests` or module-local `test_*.py`), not here.

What belongs here
- FastAPI/API contract tests using TestClient or HTTP smoke
- Live/CCXT adapter stubs and other high-level workflow checks
- Regression suites runnable in CI without real exchange credentials

What does not belong
- Fine-grained unit tests for individual functions/classes
- Large fixtures or generated assets; keep payloads minimal and deterministic

Conventions
- Name files `test_*.py`; prefer pytest/unittest with no side effects
- Avoid network calls; stub or mock external services (see ccxt stubs in existing cases)
- Keep environments self-contained: no writes outside repo, no real keys required

How to run
- From repo root: `python -m pytest auto_test -q`
- For a single case: `python -m pytest auto_test/test_live_routes.py -q`

Adding new cases
- Document any required stubs/mocks in the test file header
- If setup is non-trivial, add a short note to this file so future contributors know the contract
