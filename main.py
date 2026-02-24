from fastapi import FastAPI, Depends, HTTPException, UploadFile
from psycopg_pool import ConnectionPool
import os
from pydantic import BaseModel, Field
from typing import Optional, Annotated
from psycopg.rows import dict_row

pool: Optional[ConnectionPool] = None

class BookBase(BaseModel):
     title: Annotated[str, Field(min_length=3, max_length=50)]
     author: Annotated[str, Field(min_length=3, max_length=50)]
     year: Annotated[int, Field(gt=1000, le=2026)]
     publisher: Annotated[str, Field(min_length=3, max_length=50)]


class Book(BookBase):
    id: int
    cover_path: Optional[str] = None


class BookUpdate(BaseModel):
     title: Optional[Annotated[str, Field(min_length=3, max_length=50)]] = None
     author: Optional[Annotated[str, Field(
          min_length=3, max_length=50)]] = None
     year: Optional[Annotated[int, Field(min=1000, max=2026)]] = None
     publisher: Optional[Annotated[str, Field(
          min_length=3, max_length=50)]] = None

app = FastAPI()

def get_db():
    global pool
    with pool.connection() as conn:
        yield conn

@app.on_event("startup")
def startup():
    global pool
    try:
        PGHOST = os.environ.get("PGHOST", "localhost")
        PGPORT = int(os.environ.get("PGPORT", "5432"))
        PGDATABASE = os.environ.get("PGDATABASE", "books")
        PGUSER = os.environ.get("PGUSER")
        PGPASSWORD = os.environ.get("PGPASSWORD")
        pool = ConnectionPool(
            conninfo=f"dbname={PGDATABASE} user={PGUSER} password={PGPASSWORD} host={PGHOST} port={PGPORT}",
            min_size=1,
            max_size=10,
            open=True
        )
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title VARCHAR(50) NOT NULL CHECK (char_length(title) >= 3),
            author VARCHAR(50) NOT NULL CHECK (char_length(author) >= 3),
            year INT NOT NULL CHECK (year > 1000 AND year <= 2026),
            publisher VARCHAR(50) NOT NULL CHECK (char_length(publisher) >= 3),
            cover_path TEXT
        );
        """

        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
            conn.commit()
    except Exception as e:
        raise RuntimeError(f"Connection to database failed: {e}")

@app.get("/")
def find(q: Annotated[str, Field(min_length=3, max_length=50)], conn=Depends(get_db)) -> dict:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM books WHERE title ILIKE %s OR author ILIKE %s LIMIT 10", (f"%{q}%", f"%{q}%",))
        rows = cur.fetchall()

    books = [Book(**dict(r)) for r in rows]

    return {"books": books}

@app.post("/add/")
def add_book(book: BookBase, conn=Depends(get_db)) -> dict:
    with conn.cursor() as cur:
        cur.execute("INSERT INTO books (title, author, year, publisher) VALUES (%s, %s, %s, %s) RETURNING id",
                    (book.title, book.author, book.year, book.publisher))
        book_id = cur.fetchone()[0]
    return {"id": book_id}

@app.delete("/delete/{book_id}/")
def delete_book(book_id: int, conn=Depends(get_db)) -> dict:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM books WHERE id = %s", (book_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Book not found")
        return {"status": "success"}

@app.put("/update/{book_id}/", response_model=Book)
def update_book(book_id: int, book: BookUpdate, conn=Depends(get_db)) -> Book:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Book not found")
        updated_book = Book(**dict(cur.fetchone()))
        if book.title:
            updated_book.title = book.title
        if book.author:
            updated_book.author = book.author
        if book.year:
            updated_book.year = book.year
        if book.publisher:
            updated_book.publisher = book.publisher
        cur.execute("UPDATE books SET title = %s, author = %s, year = %s, publisher = %s WHERE id = %s",
                    (updated_book.title, updated_book.author, updated_book.year, updated_book.publisher, book_id))
        return updated_book

@app.put("/cover/{book_id}/", response_model=Book)
def update_book_cover(book_id: int, cover_image: UploadFile, conn=Depends(get_db)) -> Book:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Book not found")
        cover_path = f"covers/{book_id}"
        os.makedirs(os.path.dirname(cover_path), exist_ok=True)
        with open(cover_path, "wb") as f:
            f.write(cover_image.file.read())
        updated_book = Book(**dict(cur.fetchone()))
        updated_book.cover_path = cover_path
        cur.execute("UPDATE books SET cover_path = %s WHERE id = %s",
                    (updated_book.cover_path, book_id))
        return updated_book

@app.on_event("shutdown")
def shutdown():
    global pool
    if pool:
        pool.close()