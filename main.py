from fastapi import FastAPI, Depends, HTTPException
from psycopg_pool import ConnectionPool
import os
from pydantic import BaseModel, Field
from typing import Optional, Annotated
from psycopg.rows import dict_row

pool: Optional[ConnectionPool] = None

class BookBase(BaseModel):
     title: Annotated[str, Field(min_length=3, max_length=100)]
     author: Annotated[str, Field(min_length=3, max_length=100)]
     year: Annotated[int, Field(gt=1000, le=2026)]
     publisher: Annotated[str, Field(min_length=3, max_length=100)]


class Book(BookBase):
    id: int
    coverPath: Optional[str] = None


class BookUpdate(BaseModel):
     title: Optional[Annotated[str, Field(min_length=3, max_length=100)]] = None
     author: Optional[Annotated[str, Field(
          min_length=3, max_length=100)]] = None
     year: Optional[Annotated[int, Field(min=1000, max=2026)]] = None
     publisher: Optional[Annotated[str, Field(
          min_length=3, max_length=100)]] = None

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
    except Exception as e:
        return {"Connection to database failed":e}

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

@app.delete("/delete/{book_id}")
def delete_book(book_id: int, conn=Depends(get_db)) -> dict:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM books WHERE id = %s", (book_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Book not found")
        return {"status": "success"}