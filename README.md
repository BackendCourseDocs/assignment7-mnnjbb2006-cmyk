# Library API (FastAPI + PostgreSQL)

Minimal FastAPI service managing a single `books` table in PostgreSQL and storing cover images on disk.

Quick start
1. Create a Python venv and install deps:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Ensure PostgreSQL is reachable and set env vars (defaults shown):
```bash
   export PGHOST=localhost
   export PGPORT=5432
   export PGDATABASE=books
   export PGUSER=your_db_user
   export PGPASSWORD=your_db_password
```
replace your_db_user with your PostgreSQL username

replace your_db_password with you PostgreSQL password

3. Run the app:
   fastapi dev main.py

Notes
- On startup the app will attempt to create the `books` table if it does not exist.
- The app also attempts to enable the `pg_trgm` extension and create GIN trigram indexes on `lower(title)` and `lower(author)` to accelerate case-insensitive substring searches (queries using `ILIKE '%...%'`). Creating the extension requires appropriate DB privileges; if your managed/hosted database does not allow `CREATE EXTENSION` from the application, create the extension and indexes as part of provisioning or run them manually as a DB admin.
- Cover images are written to `covers/<book_id>` (no extension by default).
- Keep `main.py` as a single app entrypoint unless you intentionally refactor lifecycle (pool created on startup, closed on shutdown).

Primary endpoints (examples)
- Search (title or author):
  curl "http://localhost:8000/?q=searchterm"

- Add book:
  curl -X POST "http://localhost:8000/add/" -H "Content-Type: application/json" \
    -d '{"title":"My Book","author":"An Author","year":2020,"publisher":"Pub"}'

- Update book metadata:
  curl -X PUT "http://localhost:8000/update/1/" -H "Content-Type: application/json" \
    -d '{"title":"New Title"}'

- Upload/replace cover:
  curl -X PUT "http://localhost:8000/cover/1/" -F "cover_image=@/path/to/file.jpg"

- Delete book:
  curl -X DELETE "http://localhost:8000/delete/1/"

Repository specifics / gotchas
- DB access uses psycopg_pool.ConnectionPool and raw SQL with `%s` placeholders. Do not interpolate user input into SQL strings.
- Many handlers use conn.cursor(row_factory=dict_row) and expect cur.fetchone() after executing a SELECT. Preserve this pattern when editing handlers.
- If you change how covers are stored (extensions, directories), update both filesystem logic and DB `cover_path` usage.
- Required packages are listed in requirements.txt; add only minimal dependencies.

Testing locally
- Start a local PostgreSQL instance with the DB named by PGDATABASE, or set PGDATABASE accordingly.
- Visit interactive docs at http://localhost:8000/docs to exercise endpoints.
