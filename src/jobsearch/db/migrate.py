from pathlib import Path
import sqlite3
from jobsearch.config import DEFAULT_DB_PATH

def connect(db_path=DEFAULT_DB_PATH):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def migrate(db_path=DEFAULT_DB_PATH):
    con = connect(db_path)
    schema = Path(__file__).with_name("schema.sql").read_text()
    con.executescript(schema); con.commit(); con.close()
