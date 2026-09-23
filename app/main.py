from pathlib import Path
import json
import re
import unicodedata

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .interviewer import (
    InterviewConfigurationError,
    InterviewServiceError,
    generate_reply,
)

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
CASE_DIR = ROOT / "casos" / "retailnova"

with open(CASE_DIR / "caso.json", encoding="utf-8") as f:
    CASE = json.load(f)

with open(CASE_DIR / "bodega.json", encoding="utf-8") as f:
    CHARACTER = json.load(f)

app = FastAPI(title="Simulador de Entrevistas RetailNova v0.2")

STATE = {
    "messages": [],
    "discovered": set(),
    "question_count": 0,
}


class MessageIn(BaseModel):
    text: str


def reset_state():
    STATE["messages"] = []
    STATE["discovered"] = set()
    STATE["question_count"] = 0


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = "".join(
        c
        for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", text)


def mark_discoveries_from_answer(answer: str):
    normalized_answer = normalize(answer)

    for item in CHARACTER["hallazgos_ocultos"]:
        evidence_terms = item.get("evidence_terms", [])
        if any(normalize(term) in normalized_answer for term in evidence_terms):
            STATE["discovered"].add(item["id"])


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


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
    mark_discoveries_from_answer(answer)

    return {"message": answer}


@app.post("/api/end")
def end():
    total = len(CHARACTER["hallazgos_ocultos"])
    discovered_ids = STATE["discovered"]

    items = [
        {
            "id": item["id"],
            "description": item["descripcion"],
            "discovered": item["id"] in discovered_ids,
        }
        for item in CHARACTER["hallazgos_ocultos"]
    ]

    q_count = STATE["question_count"]
    coverage = round((len(discovered_ids) / total) * 100) if total else 0

    feedback = [
        "La detección de hallazgos de esta versión todavía es provisional. "
        "El evaluador inteligente se incorporará en el siguiente hito."
    ]

    if q_count < 5:
        feedback.append(
            "Realizaste pocas preguntas; prueba profundizar antes de cerrar un tema."
        )
    else:
        feedback.append(
            "La entrevista tuvo suficientes turnos para observar preguntas y repreguntas."
        )

    return {
        "questions": q_count,
        "coverage": coverage,
        "discovered_count": len(discovered_ids),
        "total": total,
        "items": items,
        "feedback": feedback,
        "transcript": STATE["messages"],
    }


app.mount("/static", StaticFiles(directory=STATIC), name="static")
