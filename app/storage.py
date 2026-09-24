from pathlib import Path
from datetime import datetime, timedelta, timezone
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


def init_db(default_simulation: dict):
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                caso TEXT NOT NULL,
                personaje TEXT NOT NULL,
                modo TEXT NOT NULL,
                objetivo_actividad TEXT NOT NULL,
                instrucciones_estudiante TEXT NOT NULL,
                objetivos_evaluados TEXT NOT NULL,
                objetivos_personalizados TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('teacher', 'student')),
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                simulation_id INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                question_count INTEGER NOT NULL DEFAULT 0,
                transcript TEXT NOT NULL DEFAULT '[]',
                evaluation TEXT,
                global_level TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (simulation_id) REFERENCES simulations(id)
            )
            """
        )

        total = conn.execute(
            "SELECT COUNT(*) AS total FROM simulations"
        ).fetchone()["total"]

        if total == 0:
            _insert_simulation(conn, default_simulation)


def _insert_simulation(conn, simulation: dict) -> int:
    cursor = conn.execute(
        """
        INSERT INTO simulations (
            nombre,
            caso,
            personaje,
            modo,
            objetivo_actividad,
            instrucciones_estudiante,
            objetivos_evaluados,
            objetivos_personalizados
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            simulation["nombre"],
            simulation["caso"],
            simulation["personaje"],
            simulation.get("modo", "entrenamiento"),
            simulation["objetivo_actividad"],
            simulation["instrucciones_estudiante"],
            json.dumps(
                simulation.get("objetivos_evaluados", []),
                ensure_ascii=False,
            ),
            json.dumps(
                simulation.get("objetivos_personalizados", []),
                ensure_ascii=False,
            ),
        ),
    )
    return cursor.lastrowid


def create_simulation(simulation: dict) -> dict:
    with _connect() as conn:
        simulation_id = _insert_simulation(conn, simulation)
        row = conn.execute(
            "SELECT * FROM simulations WHERE id = ?",
            (simulation_id,),
        ).fetchone()

    return _simulation_row_to_dict(row)


def list_simulations() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM simulations ORDER BY id DESC"
        ).fetchall()

    return [_simulation_row_to_dict(row) for row in rows]


def get_simulation(simulation_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM simulations WHERE id = ?",
            (simulation_id,),
        ).fetchone()

    return _simulation_row_to_dict(row) if row else None


def _simulation_row_to_dict(row) -> dict:
    data = dict(row)
    data["objetivos_evaluados"] = json.loads(data["objetivos_evaluados"])
    data["objetivos_personalizados"] = json.loads(
        data["objetivos_personalizados"]
    )
    return data


def user_count() -> int:
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM users"
        ).fetchone()
    return row["total"]


def create_user(
    username: str,
    display_name: str,
    role: str,
    password_salt: str,
    password_hash: str,
) -> dict:
    username = username.strip().lower()

    try:
        with _connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (
                    username,
                    display_name,
                    role,
                    password_salt,
                    password_hash
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    username,
                    display_name.strip(),
                    role,
                    password_salt,
                    password_hash,
                ),
            )
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise ValueError("Ese nombre de usuario ya existe.") from exc

    return _user_row_to_dict(row, include_secret=False)


def get_user_by_username(username: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username.strip().lower(),),
        ).fetchone()

    return _user_row_to_dict(row, include_secret=True) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    return _user_row_to_dict(row, include_secret=False) if row else None


def list_students() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, username, display_name, role, created_at
            FROM users
            WHERE role = 'student'
            ORDER BY display_name, username
            """
        ).fetchall()

    return [dict(row) for row in rows]


def _user_row_to_dict(row, include_secret: bool) -> dict:
    data = dict(row)
    if not include_secret:
        data.pop("password_salt", None)
        data.pop("password_hash", None)
    return data


def create_session(token: str, user_id: int, days: int = 7):
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=days)

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO sessions (token, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                token,
                user_id,
                now.isoformat(),
                expires.isoformat(),
            ),
        )


def get_user_by_session(token: str) -> dict | None:
    if not token:
        return None

    now = datetime.now(timezone.utc).isoformat()

    with _connect() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.username, u.display_name, u.role, u.created_at
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = ? AND s.expires_at > ?
            """,
            (token, now),
        ).fetchone()

    return dict(row) if row else None


def delete_session(token: str):
    if not token:
        return

    with _connect() as conn:
        conn.execute(
            "DELETE FROM sessions WHERE token = ?",
            (token,),
        )


def create_attempt(user_id: int, simulation_id: int) -> dict:
    started_at = datetime.now(timezone.utc).isoformat()

    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO attempts (
                user_id,
                simulation_id,
                started_at,
                transcript
            )
            VALUES (?, ?, ?, ?)
            """,
            (user_id, simulation_id, started_at, "[]"),
        )
        row = conn.execute(
            "SELECT * FROM attempts WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return _attempt_row_to_dict(row)


def save_attempt_progress(
    attempt_id: int,
    question_count: int,
    transcript: list[dict],
):
    with _connect() as conn:
        conn.execute(
            """
            UPDATE attempts
            SET question_count = ?, transcript = ?
            WHERE id = ?
            """,
            (
                question_count,
                json.dumps(transcript, ensure_ascii=False),
                attempt_id,
            ),
        )


def complete_attempt(
    attempt_id: int,
    question_count: int,
    transcript: list[dict],
    evaluation: dict,
):
    completed_at = datetime.now(timezone.utc).isoformat()

    with _connect() as conn:
        conn.execute(
            """
            UPDATE attempts
            SET completed_at = ?,
                question_count = ?,
                transcript = ?,
                evaluation = ?,
                global_level = ?
            WHERE id = ?
            """,
            (
                completed_at,
                question_count,
                json.dumps(transcript, ensure_ascii=False),
                json.dumps(evaluation, ensure_ascii=False),
                evaluation.get("nivel_global"),
                attempt_id,
            ),
        )


def list_attempts(user_id: int | None = None) -> list[dict]:
    query = """
        SELECT
            a.*,
            u.username,
            u.display_name,
            s.nombre AS simulation_name
        FROM attempts a
        JOIN users u ON u.id = a.user_id
        JOIN simulations s ON s.id = a.simulation_id
    """
    params = []

    if user_id is not None:
        query += " WHERE a.user_id = ?"
        params.append(user_id)

    query += " ORDER BY a.id DESC"

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()

    return [_attempt_row_to_dict(row) for row in rows]


def get_attempt(attempt_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT
                a.*,
                u.username,
                u.display_name,
                s.nombre AS simulation_name
            FROM attempts a
            JOIN users u ON u.id = a.user_id
            JOIN simulations s ON s.id = a.simulation_id
            WHERE a.id = ?
            """,
            (attempt_id,),
        ).fetchone()

    return _attempt_row_to_dict(row) if row else None


def _attempt_row_to_dict(row) -> dict:
    data = dict(row)
    data["transcript"] = json.loads(data.get("transcript") or "[]")
    data["evaluation"] = (
        json.loads(data["evaluation"])
        if data.get("evaluation")
        else None
    )
    return data
