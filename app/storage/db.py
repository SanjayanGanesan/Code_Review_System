import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent.parent / "reviews.db"


SCHEMA = """ 
CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    language TEXT NOT NULL,
    code TEXT NOT NULL,
    score INTEGER NOT NULL,
    summary_json TEXT NOT NULL,
    findings_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at DESC);
"""

def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path,check_same_thread = False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Path = DB_PATH) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()