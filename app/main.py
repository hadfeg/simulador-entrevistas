from pathlib import Path
from uuid import uuid4
import json

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .interviewer import (
    InterviewConfigurationError,
    InterviewServiceError,
    generate_reply,
)
from .evaluator import (
    EvaluationConfigurationError,
    EvaluationServiceError,
    evaluate_interview,
)
from .storage import (
    create_simulation,
    get_simulation,
    init_db,
    list_simulations,
)

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
CASE_DIR = ROOT / "casos" / "retailnova"
CONFIG_DIR = ROOT / "config"

with open(CASE_DIR / "caso.json", encoding="utf-8") as f:
    CASE = json.load(f)

with open(CASE_DIR / "bodega.json", encoding="utf-8") as f:
    BODEGA = json.load(f)

with open(CASE_DIR / "simulacion_bodega.json", encoding="utf-8") as f:
    DEFAULT_SIMULATION = json.load(f)

with open(CONFIG_DIR / "pedagogia.json", encoding="utf-8") as f:
    PEDAGOGY = json.load(f)

CHARACTERS = {
    BODEGA["id"]: BODEGA,
}

init_db(DEFAULT_SIMULATION)

app = FastAPI(title="Simulador de Entrevistas v0.4")

STATE = {
    "messages": [],
    "question_count": 0,
    "simulation": None,
    "character": None,
}


class MessageIn(BaseModel):
    text: str


class CustomObjectiveIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    descripcion: str = Field(min_length=5, max_length=600)
    evidencia_suficiente: str = Field(min_length=5, max_length=600)


class SimulationCreate(BaseModel):
    nombre: str = Field(min_length=3, max_length=160)
    personaje: str
    objetivo_actividad: str = Field(min_length=10, max_length=1200)
    instrucciones_estudiante: str = Field(min_length=10, max_length=1800)
    objetivos_evaluados: list[str] = []
    objetivos_personalizados: list[CustomObjectiveIn] = []


def reset_interview():
    STATE["messages"] = []
    STATE["question_count"] = 0


def objective_catalog() -> dict[str, dict]:
    return {item["id"]: item for item in PEDAGOGY["objetivos"]}


def selected_objective_names(simulation: dict) -> list[dict]:
    catalog = objective_catalog()
    selected = []

    for objective_id in simulation.get("objetivos_evaluados", []):
        item = catalog.get(objective_id)
        if item:
            selected.append({"id": item["id"], "nombre": item["nombre"]})

    for custom in simulation.get("objetivos_personalizados", []):
        selected.append({"id": custom["id"], "nombre": custom["nombre"]})

    return selected


def character_summary(character: dict) -> dict:
    return {
        "id": character["id"],
        "name": character["nombre"],
        "role": character["cargo"],
        "company": character["empresa"],
    }


def simulation_summary(simulation: dict, teacher: bool = False) -> dict:
    character = CHARACTERS.get(simulation["personaje"])

    result = {
        "id": simulation["id"],
        "nombre": simulation["nombre"],
        "modo": simulation.get("modo", "entrenamiento"),
        "objetivo_actividad": simulation["objetivo_actividad"],
        "instrucciones_estudiante": simulation["instrucciones_estudiante"],
        "character": character_summary(character) if character else None,
        "cantidad_objetivos": (
            len(simulation.get("objetivos_evaluados", []))
            + len(simulation.get("objetivos_personalizados", []))
        ),
    }

    if teacher:
        result["objetivos"] = selected_objective_names(simulation)
        result["objetivos_personalizados"] = simulation.get(
            "objetivos_personalizados", []
        )

    return result


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/catalog")
def catalog():
    return {
        "objetivo_general": PEDAGOGY["objetivo_general"],
        "objetivos": PEDAGOGY["objetivos"],
        "personajes": [
            character_summary(character)
            for character in CHARACTERS.values()
        ],
    }


@app.get("/api/simulations")
def simulations():
    return [
        simulation_summary(simulation, teacher=True)
        for simulation in list_simulations()
    ]


@app.get("/api/simulations/{simulation_id}")
def simulation_detail(simulation_id: int):
    simulation = get_simulation(simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulación no encontrada.")

    return simulation_summary(simulation, teacher=True)


@app.post("/api/simulations")
def new_simulation(data: SimulationCreate):
    if data.personaje not in CHARACTERS:
        raise HTTPException(
            status_code=400,
            detail="El entrevistado seleccionado no está disponible.",
        )

    catalog = objective_catalog()
    invalid = [
        objective_id
        for objective_id in data.objetivos_evaluados
        if objective_id not in catalog
    ]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail="Uno o más objetivos seleccionados no existen en el catálogo.",
        )

    custom_objectives = []
    for custom in data.objetivos_personalizados:
        custom_objectives.append(
            {
                "id": f"custom_{uuid4().hex[:10]}",
                "nombre": custom.nombre.strip(),
                "descripcion": custom.descripcion.strip(),
                "que_observar": custom.descripcion.strip(),
                "evidencia_suficiente": custom.evidencia_suficiente.strip(),
                "evidencia_insuficiente": (
                    "No se observa evidencia suficiente y consistente de la "
                    "conducta definida por el docente."
                ),
            }
        )

    if not data.objetivos_evaluados and not custom_objectives:
        raise HTTPException(
            status_code=400,
            detail="Selecciona al menos un objetivo para evaluar.",
        )

    simulation = {
        "nombre": data.nombre.strip(),
        "caso": CASE["id"],
        "personaje": data.personaje,
        "modo": "entrenamiento",
        "objetivo_actividad": data.objetivo_actividad.strip(),
        "instrucciones_estudiante": data.instrucciones_estudiante.strip(),
        "objetivos_evaluados": data.objetivos_evaluados,
        "objetivos_personalizados": custom_objectives,
    }

    created = create_simulation(simulation)
    return simulation_summary(created, teacher=True)


@app.post("/api/simulations/{simulation_id}/start")
def start(simulation_id: int):
    simulation = get_simulation(simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulación no encontrada.")

    character = CHARACTERS.get(simulation["personaje"])
    if not character:
        raise HTTPException(
            status_code=400,
            detail="El entrevistado configurado no está disponible.",
        )

    reset_interview()
    STATE["simulation"] = simulation
    STATE["character"] = character

    opening = (
        f"Hola, soy {character['nombre']}, {character['cargo']} de "
        f"{character['empresa']}. ¿En qué te puedo ayudar?"
    )
    STATE["messages"].append({"role": "assistant", "text": opening})

    return {
        "simulation": simulation_summary(simulation),
        "character": character_summary(character),
        "message": opening,
    }


@app.post("/api/message")
def message(data: MessageIn):
    simulation = STATE["simulation"]
    character = STATE["character"]

    if not simulation or not character:
        raise HTTPException(
            status_code=409,
            detail="Primero debes comenzar una simulación.",
        )

    text = data.text.strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail="La pregunta no puede estar vacía.",
        )

    try:
        answer = generate_reply(
            case=CASE,
            character=character,
            history=STATE["messages"],
            question=text,
        )
    except InterviewConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except InterviewServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    STATE["question_count"] += 1
    STATE["messages"].append({"role": "user", "text": text})
    STATE["messages"].append({"role": "assistant", "text": answer})

    return {"message": answer}


@app.post("/api/end")
def end():
    simulation = STATE["simulation"]
    character = STATE["character"]

    if not simulation or not character:
        raise HTTPException(
            status_code=409,
            detail="No hay una simulación activa.",
        )

    try:
        evaluation = evaluate_interview(
            pedagogy=PEDAGOGY,
            simulation=simulation,
            case=CASE,
            character=character,
            transcript=STATE["messages"],
        )
    except EvaluationConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except EvaluationServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    payload = evaluation.model_dump()
    catalog = objective_catalog()

    for item in payload["resultados"]:
        objective = catalog.get(item["objetivo_id"])
        if objective:
            item["nombre"] = objective["nombre"]
            continue

        custom = next(
            (
                obj
                for obj in simulation.get("objetivos_personalizados", [])
                if obj["id"] == item["objetivo_id"]
            ),
            None,
        )
        item["nombre"] = custom["nombre"] if custom else item["objetivo_id"]

    return {
        "questions": STATE["question_count"],
        "simulation": simulation_summary(simulation),
        "evaluation": payload,
        "transcript": STATE["messages"],
    }


app.mount("/static", StaticFiles(directory=STATIC), name="static")
