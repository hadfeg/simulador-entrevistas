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

        total = conn.execute("SELECT COUNT(*) AS total FROM simulations").fetchone()["total"]

        if total == 0:
            _insert(conn, default_simulation)


def _insert(conn, simulation: dict) -> int:
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
            json.dumps(simulation.get("objetivos_evaluados", []), ensure_ascii=False),
            json.dumps(simulation.get("objetivos_personalizados", []), ensure_ascii=False),
        ),
    )
    return cursor.lastrowid


def create_simulation(simulation: dict) -> dict:
    with _connect() as conn:
        simulation_id = _insert(conn, simulation)
        row = conn.execute(
            "SELECT * FROM simulations WHERE id = ?",
            (simulation_id,),
        ).fetchone()

    return _row_to_dict(row)


def list_simulations() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM simulations ORDER BY id DESC"
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def get_simulation(simulation_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM simulations WHERE id = ?",
            (simulation_id,),
        ).fetchone()

    return _row_to_dict(row) if row else None


def _row_to_dict(row) -> dict:
    data = dict(row)
    data["objetivos_evaluados"] = json.loads(data["objetivos_evaluados"])
    data["objetivos_personalizados"] = json.loads(data["objetivos_personalizados"])
    return data
