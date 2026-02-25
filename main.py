from fastapi import FastAPI, Depends, HTTPException, UploadFile
import asyncpg
import os
import aiofiles
from pydantic import BaseModel, Field
from typing import Optional, Annotated

class BookBase(BaseModel):
    title: Annotated[str, Field(min_length=3, max_length=255)]
    author: Annotated[str, Field(min_length=3, max_length=255)]
    year: Annotated[int, Field(gt=1000, le=2026)]
    publisher: Annotated[str, Field(min_length=3, max_length=255)]


class Book(BookBase):
    id: int
    cover_path: Optional[str] = None


class BookUpdate(BaseModel):
    title: Optional[Annotated[str, Field(min_length=3, max_length=255)]] = None
    author: Optional[Annotated[str, Field(
        min_length=3, max_length=255)]] = None
    year: Optional[Annotated[int, Field(gt=1000, le=2026)]] = None
    publisher: Optional[Annotated[str, Field(
        min_length=3, max_length=255)]] = None

app = FastAPI()

@app.on_event("startup")
async def startup():
    try:
        PGHOST = os.environ.get("PGHOST", "localhost")
        PGPORT = int(os.environ.get("PGPORT", "5432"))
        PGDATABASE = os.environ.get("PGDATABASE", "books")
        PGUSER = os.environ.get("PGUSER")
        PGPASSWORD = os.environ.get("PGPASSWORD")
        app.state.pool = await asyncpg.create_pool(
            host=PGHOST,
            port=PGPORT,
            database=PGDATABASE,
            user=PGUSER,
            password=PGPASSWORD,
            min_size=1,
            max_size=100
        )
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL CHECK (char_length(title) >= 3),
            author VARCHAR(255) NOT NULL CHECK (char_length(author) >= 3),
            year INT NOT NULL CHECK (year > 1000 AND year <= 2026),
            publisher VARCHAR(255) NOT NULL CHECK (char_length(publisher) >= 3),
            cover_path VARCHAR(255) NULL
        );
        """

        async with app.state.pool.acquire() as conn:
            await conn.execute(create_table_sql)
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS books_title_trgm_idx ON books USING gin (lower(title) gin_trgm_ops);"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS books_author_trgm_idx ON books USING gin (lower(author) gin_trgm_ops);"
            )
    except Exception as e:
        raise RuntimeError(f"Connection to database failed: {e}")

@app.get("/")
async def find(q: Annotated[str, Field(min_length=3, max_length=255)]) -> dict:
    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM books WHERE title ILIKE $1 OR author ILIKE $1 LIMIT 10", f"%{q}%")
        books = [Book(**dict(r)) for r in rows]
        return {"books": books}

@app.post("/add/")
async def add_book(book: BookBase) -> dict:
    async with app.state.pool.acquire() as conn:
        book_id = await conn.fetchval(
            "INSERT INTO books (title, author, year, publisher) VALUES ($1, $2, $3, $4) RETURNING id",
            book.title, book.author, book.year, book.publisher
        )
        return {"id": book_id}

@app.delete("/delete/{book_id}/")
async def delete_book(book_id: int) -> dict:
    async with app.state.pool.acquire() as conn:
        result = await conn.execute("DELETE FROM books WHERE id = $1", book_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Book not found")
        return {"status": "success"}

@app.put("/update/{book_id}/", response_model=Book)
async def update_book(book_id: int, book: BookUpdate) -> Book:
    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM books WHERE id = $1", book_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Book not found")
        
        updated_book_dict = dict(row)
        if book.title is not None:
            updated_book_dict["title"] = book.title
        if book.author is not None:
            updated_book_dict["author"] = book.author
        if book.year is not None:
            updated_book_dict["year"] = book.year
        if book.publisher is not None:
            updated_book_dict["publisher"] = book.publisher
            
        await conn.execute(
            "UPDATE books SET title = $1, author = $2, year = $3, publisher = $4 WHERE id = $5",
            updated_book_dict["title"], updated_book_dict["author"], updated_book_dict["year"], 
            updated_book_dict["publisher"], book_id
        )
    return Book(**updated_book_dict)

@app.put("/cover/{book_id}/", response_model=Book)
async def update_book_cover(book_id: int, cover_image: UploadFile) -> Book:
    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM books WHERE id = $1", book_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Book not found")
        
        cover_path = f"covers/{book_id}"
        os.makedirs(os.path.dirname(cover_path), exist_ok=True)
        
        async with aiofiles.open(cover_path, "wb") as f:
            await f.write(await cover_image.read())
            
        updated_book_dict = dict(row)
        updated_book_dict["cover_path"] = cover_path
        
        await conn.execute("UPDATE books SET cover_path = $1 WHERE id = $2", cover_path, book_id)
    return Book(**updated_book_dict)

# get number of books written by searched author
@app.get("/author_count/")
async def author_count(q: Annotated[str, Field(min_length=3, max_length=255)]) -> dict:
    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch("SELECT author, COUNT(*) FROM books WHERE author ILIKE $1 GROUP BY author", f"%{q}%")
        d = {k:v for k,v in rows}
        return d

@app.on_event("shutdown")
async def shutdown():
    app.state.pool.close()