from pathlib import Path
import json

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

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

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
CASE_DIR = ROOT / "casos" / "retailnova"
CONFIG_DIR = ROOT / "config"

with open(CASE_DIR / "caso.json", encoding="utf-8") as f:
    CASE = json.load(f)

with open(CASE_DIR / "bodega.json", encoding="utf-8") as f:
    CHARACTER = json.load(f)

with open(CASE_DIR / "simulacion_bodega.json", encoding="utf-8") as f:
    SIMULATION = json.load(f)

with open(CONFIG_DIR / "pedagogia.json", encoding="utf-8") as f:
    PEDAGOGY = json.load(f)

app = FastAPI(title="Simulador de Entrevistas RetailNova v0.3")

STATE = {
    "messages": [],
    "question_count": 0,
}


class MessageIn(BaseModel):
    text: str


def reset_state():
    STATE["messages"] = []
    STATE["question_count"] = 0


def selected_objective_names() -> list[dict]:
    catalog = {item["id"]: item for item in PEDAGOGY["objetivos"]}
    selected = []

    for objective_id in SIMULATION.get("objetivos_evaluados", []):
        item = catalog.get(objective_id)
        if item:
            selected.append({"id": item["id"], "nombre": item["nombre"]})

    for custom in SIMULATION.get("objetivos_personalizados", []):
        selected.append({"id": custom["id"], "nombre": custom["nombre"]})

    return selected


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/simulation")
def simulation():
    return {
        "id": SIMULATION["id"],
        "nombre": SIMULATION["nombre"],
        "modo": SIMULATION.get("modo", "entrenamiento"),
        "objetivo_general": PEDAGOGY["objetivo_general"],
        "objetivo_actividad": SIMULATION["objetivo_actividad"],
        "instrucciones_estudiante": SIMULATION["instrucciones_estudiante"],
        "objetivos": selected_objective_names(),
        "character": {
            "name": CHARACTER["nombre"],
            "role": CHARACTER["cargo"],
            "company": CHARACTER["empresa"],
        },
    }


@app.post("/api/start")
def start():
    reset_state()

    opening = (
        f"Hola, soy {CHARACTER['nombre']}, {CHARACTER['cargo']} de "
        f"{CHARACTER['empresa']}. ¿En qué te puedo ayudar?"
    )
    STATE["messages"].append({"role": "assistant", "text": opening})

    return {
        "character": {
            "name": CHARACTER["nombre"],
            "role": CHARACTER["cargo"],
            "company": CHARACTER["empresa"],
        },
        "message": opening,
    }


@app.post("/api/message")
def message(data: MessageIn):
    text = data.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía.")

    try:
        answer = generate_reply(
            case=CASE,
            character=CHARACTER,
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
    try:
        evaluation = evaluate_interview(
            pedagogy=PEDAGOGY,
            simulation=SIMULATION,
            case=CASE,
            character=CHARACTER,
            transcript=STATE["messages"],
        )
    except EvaluationConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except EvaluationServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    payload = evaluation.model_dump()
    catalog = {item["id"]: item for item in PEDAGOGY["objetivos"]}

    for item in payload["resultados"]:
        objective = catalog.get(item["objetivo_id"])
        if objective:
            item["nombre"] = objective["nombre"]
        else:
            custom = next(
                (
                    obj
                    for obj in SIMULATION.get("objetivos_personalizados", [])
                    if obj["id"] == item["objetivo_id"]
                ),
                None,
            )
            item["nombre"] = custom["nombre"] if custom else item["objetivo_id"]

    return {
        "questions": STATE["question_count"],
        "evaluation": payload,
        "transcript": STATE["messages"],
    }


app.mount("/static", StaticFiles(directory=STATIC), name="static")
