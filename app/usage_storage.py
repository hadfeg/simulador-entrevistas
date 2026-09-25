from pathlib import Path
import json
import sqlite3

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "simulador.db"


def _connect():
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_usage_db():
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attempt_usage (
                attempt_id INTEGER PRIMARY KEY,
                usage_json TEXT NOT NULL,
                estimated_cost_usd REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (attempt_id) REFERENCES attempts(id)
            )
            """
        )


def save_attempt_usage(attempt_id: int, usage: dict):
    cost = float(
        usage.get("summary", {}).get("estimated_cost_usd", 0.0) or 0.0
    )

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO attempt_usage (
                attempt_id,
                usage_json,
                estimated_cost_usd
            )
            VALUES (?, ?, ?)
            ON CONFLICT(attempt_id) DO UPDATE SET
                usage_json = excluded.usage_json,
                estimated_cost_usd = excluded.estimated_cost_usd
            """,
            (
                attempt_id,
                json.dumps(usage, ensure_ascii=False),
                cost,
            ),
        )


def get_attempt_usage(attempt_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT usage_json
            FROM attempt_usage
            WHERE attempt_id = ?
            """,
            (attempt_id,),
        ).fetchone()

    if not row:
        return None

    return json.loads(row["usage_json"])
