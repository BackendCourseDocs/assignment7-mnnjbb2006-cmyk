```instructions
# Project Guidelines

This repository is a small Python API project. The instructions below help AI coding agents be productive here.

## Code Style
- Language: Python (single-module app in [main.py](main.py)).
- Follow existing file patterns in [main.py](main.py): simple, synchronous script-style layout.
- Keep names in snake_case and prefer clear, short functions. Add type hints where helpful.

## Architecture
- Single-process API application (see [main.py](main.py)). There is no large framework scaffolding in this repo.
- Data persistence: PostgreSQL is used (repository folder name references PostgreSQL). Connection/configuration is expected to be provided via environment variables.

## Build and Test
- Install dependencies: `python -m pip install -r requirements.txt` ([requirements.txt](requirements.txt)).
- Run the app locally for quick checks: `python main.py`.
- There are currently no automated tests discovered. If tests are added, run them with `pytest`.

## Project Conventions
- Small, focused module: prefer minimal, easily-reviewable changes.
- Configuration: do not hardcode secrets. Use environment variables (for example `DATABASE_URL`).
- Logging and errors: prefer explicit, simple logging increments in the existing style rather than adding heavy frameworks.

## Integration Points
- PostgreSQL: expect to read DB connection from an env var such as `DATABASE_URL`.
- If new services are added, document their required env vars in `README.md` or `.env.example`.

## Security
- Never commit credentials or connection strings. Use environment variables and secret stores.
- Sanitize inputs before using them in DB queries; prefer parameterized queries (no string interpolation into SQL).

## Where to Look
- Main application: [main.py](main.py)
- Dependencies: [requirements.txt](requirements.txt)

If anything here is unclear or incomplete, tell me which area to expand and I will update this file.

## API Endpoints
- **`/author_count/`**: GET — search authors and return counts.
  - **Query param**: `q` (string, min length 3) — partial, case-insensitive match against `author`.
  - **Behavior**: returns JSON with a top-level `author_counts` mapping where keys are author names and values are integer counts. Example: {"author_counts": {"Agatha Christie": 12, "Arthur Conan Doyle": 5}}.
  - **Implementation notes for agents**: Use a parameterized SQL query (e.g. `SELECT author, COUNT(*) FROM books WHERE author ILIKE $1 GROUP BY author`) and return a Python dict mapping author -> count. Keep validation aligned with `main.py` (min length 3).

```
