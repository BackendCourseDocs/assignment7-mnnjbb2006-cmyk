<!-- .github/copilot-instructions.md -->

# Assistant instructions for this repository

This repository is a minimal FastAPI service that manages a single `books` table in PostgreSQL and stores cover images on disk. The goal of these instructions is to make an AI coding assistant productive quickly by surfacing the project-specific architecture, conventions, and run/debug commands.

Key facts (quick):
- Main app: `main.py` — single FastAPI app, procedural style (no routers or packages).
- Database: PostgreSQL via `psycopg_pool.ConnectionPool`. Connection pool is created at startup and closed at shutdown.
- Storage: Book covers are written to `covers/<book_id>` on the filesystem.
- Models: Pydantic models are defined inline (`BookBase`, `Book`, `BookUpdate`).

What the assistant should know about architecture and patterns:
- `main.py` contains all request handlers. Expect dependencies via `Depends(get_db)` which yields a psycopg connection from the global `pool`.
- SQL is executed with raw SQL strings and `%s` placeholders (psycopg param style). Use `conn.cursor()` and sometimes `row_factory=dict_row` for dict rows.
- Table creation SQL runs on startup if the `books` table does not exist. Field constraints mirror Pydantic validators (e.g. title length, year range).
- Cover uploads: `UploadFile` is read and written directly to `covers/<book_id>`; the DB stores the `cover_path` text.

Indexes and case-insensitive substring search (pg_trgm)
- The app enables the PostgreSQL `pg_trgm` extension and creates GIN trigram indexes on the lowercased `title` and `author` columns during startup. These expression indexes use `lower(title)` and `lower(author)` with `gin_trgm_ops` to accelerate case-insensitive substring searches using `ILIKE '%...%'` or `lower(column) LIKE '%%...%%'` patterns.
- Important: creating extensions requires appropriate database privileges. On many hosted DB services you need a superuser or an admin role to run `CREATE EXTENSION pg_trgm`. If your environment doesn't allow creating extensions from the application, create the extension and indexes manually as part of your DB provisioning process (for example in a migration or the DB admin console).

Where in the code the indexes are created
- The `CREATE EXTENSION` and `CREATE INDEX` statements are executed in `startup()` in `main.py` immediately after the `CREATE TABLE ...` statement and before `conn.commit()` is called. This ensures the table exists when indexes are created. It's acceptable to run the extension/index creation in the same transaction as the table creation; alternatively you may run them after commit or separately during DB provisioning.

Environment and run/debug commands (discoverable from code):
- Required environment variables: `PGHOST` (default `localhost`), `PGPORT` (default `5432`), `PGDATABASE` (default `books`), `PGUSER`, `PGPASSWORD`.
- To run locally (common): use `uvicorn main:app --reload --host 0.0.0.0 --port 8000`.
- The app will attempt to create the `books` table on startup. If DB connection fails, startup raises a RuntimeError.

Project-specific conventions and gotchas:
- Single-file app: avoid introducing packages or multiple app instances without updating `startup()`/`shutdown()` pool lifecycle.
- SQL style: always use parameterized queries with `%s` placeholders. Do not interpolate user input directly into SQL.
- Cursor usage: sometimes handlers use `row_factory=dict_row`; when reading rows and later updating, the code expects `cur.fetchone()` to be callable after a prior `execute` — preserve that flow when editing.
- Cover path creation uses `os.makedirs(os.path.dirname(cover_path), exist_ok=True)`. Note `cover_path` is `covers/<book_id>` (no file extension). If changing to store files with extensions, update both filesystem logic and DB column expectations.

Examples to reference when making edits:
- Search endpoint: `find(q: str)` — demonstrates `row_factory=dict_row` and ILIKE search with `%{q}%`.
- Add endpoint: `add_book(book: BookBase)` — inserts and returns the new `id` via `RETURNING id`.
- Update cover: `update_book_cover(book_id: int, cover_image: UploadFile)` — reads UploadFile.file and writes bytes to disk, updates DB `cover_path`.

Testing and verification notes:
- There are no automated tests in the repository. To validate behavior locally:
  - Start a local PostgreSQL instance with a database named by `PGDATABASE` or set `PGDATABASE`.
  - Export `PGUSER`/`PGPASSWORD` (or use a trust local DB for dev).
  - Run uvicorn as above and exercise endpoints via curl or the interactive docs at `/docs`.
- When changing DB schema or SQL, run the app to allow the startup table-creation to run and verify the constraints match Pydantic validators.

What the assistant should not do:
- Do not assume additional packages or frameworks are present — edits should keep dependencies minimal and visible in imports (e.g., FastAPI, psycopg_pool, pydantic).
- Don't introduce background workers or multiple processes without updating the ConnectionPool usage in `startup()` and `shutdown()`.

Files to inspect for context when making changes:
- `main.py` — primary and authoritative source for behavior.
- `covers/` — storage location for uploaded cover images.

If you need clarification from the human:
- If you plan to split `main.py` into modules, ask whether to preserve the existing global `pool` lifecycle or switch to FastAPI routers with lifespan managers.
- Ask whether cover files should keep their original filenames or add extensions; current code uses `covers/<book_id>` without an extension.

If you update this file, keep the content concise and concrete. After edits, run the app locally and confirm the startup table creation works and that basic CRUD endpoints operate.
