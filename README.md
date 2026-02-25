# Library API (PostgreSQL)

Small FastAPI-based library API that stores book records in PostgreSQL.

## Repo contents
- [main.py](main.py) — application entry and API (see [`BookBase`](main.py), [`Book`](main.py), [`BookUpdate`](main.py), [`startup`](main.py), [`find`](main.py), [`add_book`](main.py), [`delete_book`](main.py), [`update_book`](main.py), [`update_book_cover`](main.py), [`shutdown`](main.py))
- [requirements.txt](requirements.txt) — Python deps
- [LICENSE](LICENSE)
- [.gitignore](.gitignore)
- [.github/copilot-instructions.md](.github/copilot-instructions.md)

## Requirements
- Python 3.9+
- PostgreSQL accessible via environment variables

Install dependencies:
```bash
python -m pip install -r requirements.txt
```

## Configuration
Provide DB connection via environment variables (used in [main.py](main.py)):
- `PGHOST` (default: localhost)
- `PGPORT` (default: 5432)
- `PGDATABASE` (default: books)
- `PGUSER`
- `PGPASSWORD`

Do not commit credentials.

### Setting environment variables

Linux / macOS (temporary for current shell):

```bash
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=books
export PGUSER=myuser
export PGPASSWORD=mypassword
```

Linux / macOS (load from `.env` file):

Create a `.env` file with the variables (example below), then run:

```bash
set -o allexport; source .env; set +o allexport
```

Windows PowerShell (current session):

```powershell
$env:PGHOST = "localhost"
$env:PGPORT = "5432"
$env:PGDATABASE = "books"
$env:PGUSER = "myuser"
$env:PGPASSWORD = "mypassword"
```

Example `.env` file contents:

```
# .env (DO NOT COMMIT)
PGHOST=localhost
PGPORT=5432
PGDATABASE=books
PGUSER=myuser
PGPASSWORD=mypassword
```

Add `.env` to your `.gitignore` to avoid accidentally committing secrets.

## Run
Quick local run (development):
```bash
fastapi dev main.py
```

## API (brief)
- GET /?q=term — search by title or author (min length 3) — implemented by [`find`](main.py)
- POST /add/ — add book JSON body matching [`BookBase`](main.py)
- DELETE /delete/{book_id}/ — delete a book — [`delete_book`](main.py)
- PUT /update/{book_id}/ — partial update with [`BookUpdate`](main.py)
- PUT /cover/{book_id}/ — upload cover image (multipart) — [`update_book_cover`](main.py)

Examples:
```bash
# search
curl "http://127.0.0.1:8000/?q=tolkien"

# add
curl -X POST "http://127.0.0.1:8000/add/" -H "Content-Type: application/json" \
  -d '{"title":"My Book","author":"A Author","year":2020,"publisher":"Pub"}'

# upload cover (multipart)
curl -X PUT "http://127.0.0.1:8000/cover/1/" -F "cover_image=@cover.jpg"
```

## Database notes
- Schema created on startup by [`startup`](main.py)
- Uses parameterized queries (asyncpg) in [main.py](main.py)
- Creates pg_trgm indexes for efficient text search

## Security & conventions
- Uses environment variables for DB config
- Input validation via Pydantic models in [main.py](main.py)
- Do not commit secrets; refer to [.gitignore](.gitignore)

## Development
Follow patterns in [.github/copilot-instructions.md](.github/copilot-instructions.md). Install deps from [requirements.txt](requirements.txt) and run locally. No automated tests present currently.

## License
MIT — see [LICENSE](LICENSE)