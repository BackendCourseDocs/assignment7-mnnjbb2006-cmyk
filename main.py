from fastapi import FastAPI
import psycopg
from psycopg_pool import ConnectionPool
import os
from pydantic import BaseModel, Field
from typing import Optional, Annotated

pool: Optional[ConnectionPool] = None

app = FastAPI()

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
def find(q: Annotated[str, Field(min_length=3, max_length=50)]):
    return {"Hello":q}