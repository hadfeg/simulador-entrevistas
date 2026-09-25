from pathlib import Path
from uuid import uuid4
import json

from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .auth import hash_password, new_session_token, verify_password
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
from .voice import (
    VoiceConfigurationError,
    VoiceServiceError,
    synthesize_speech,
    transcribe_audio,
)
from .usage import (
    add_text_usage,
    add_transcription_usage,
    add_tts_usage,
    finalized_usage,
    new_usage,
)
from .usage_storage import (
    get_attempt_usage,
    init_usage_db,
    save_attempt_usage,
)
from .storage import (
    archive_simulation,
    complete_attempt,
    create_attempt,
    create_session,
    create_simulation,
    create_user,
    delete_session,
    get_attempt,
    get_simulation,
    get_user_by_session,
    get_user_by_username,
    init_db,
    list_attempts,
    list_simulations,
    list_students,
    save_attempt_progress,
    user_count,
)

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
CASE_DIR = ROOT / "casos" / "retailnova"
CONFIG_DIR = ROOT / "config"
SESSION_COOKIE = "sim_session"

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
init_usage_db()

app = FastAPI(title="Simulador de Entrevistas v0.7 · Voz")

ACTIVE_INTERVIEWS: dict[int, dict] = {}


class MessageIn(BaseModel):
    text: str


class SpeechIn(BaseModel):
    text: str = Field(min_length=1, max_length=4096)


class SetupIn(BaseModel):
    username: str = Field(min_length=3, max_length=60)
    display_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=160)


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=60)
    password: str = Field(min_length=1, max_length=160)


class StudentCreate(BaseModel):
    username: str = Field(min_length=3, max_length=60)
    display_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=160)


class CustomObjectiveIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    descripcion: str = Field(min_length=5, max_length=600)
    evidencia_suficiente: str = Field(min_length=5, max_length=600)


class SimulationCreate(BaseModel):
    nombre: str = Field(min_length=3, max_length=160)
    personaje: str
    objetivo_actividad: str = Field(min_length=10, max_length=1200)
    instrucciones_estudiante: str = Field(min_length=10, max_length=1800)
    objetivos_evaluados: list[str] = Field(default_factory=list)
    objetivos_personalizados: list[CustomObjectiveIn] = Field(default_factory=list)


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
    }


def current_user(request: Request) -> dict | None:
    token = request.cookies.get(SESSION_COOKIE)
    return get_user_by_session(token) if token else None


def require_user(request: Request, role: str | None = None) -> dict:
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión.")

    if role and user["role"] != role:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para realizar esta acción.",
        )

    return user


def set_session_cookie(response: Response, token: str):
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=7 * 24 * 60 * 60,
    )


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
        result["active"] = simulation.get("active", True)
        result["objetivos"] = selected_objective_names(simulation)
        result["objetivos_personalizados"] = simulation.get(
            "objetivos_personalizados", []
        )

    return result


def attempt_summary(attempt: dict, include_detail: bool = False) -> dict:
    result = {
        "id": attempt["id"],
        "simulation_id": attempt["simulation_id"],
        "simulation_name": attempt.get("simulation_name"),
        "user_id": attempt["user_id"],
        "username": attempt.get("username"),
        "display_name": attempt.get("display_name"),
        "started_at": attempt["started_at"],
        "completed_at": attempt.get("completed_at"),
        "question_count": attempt["question_count"],
        "global_level": attempt.get("global_level"),
        "completed": bool(attempt.get("completed_at")),
    }

    usage = get_attempt_usage(attempt["id"])
    result["usage_summary"] = usage.get("summary") if usage else None

    if include_detail:
        result["transcript"] = attempt.get("transcript", [])
        result["evaluation"] = attempt.get("evaluation")
        result["usage"] = usage

    return result


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/auth/status")
def auth_status(request: Request):
    return {
        "needs_setup": user_count() == 0,
        "user": public_user(current_user(request)) if current_user(request) else None,
    }


@app.post("/api/auth/setup")
def auth_setup(data: SetupIn, response: Response):
    if user_count() != 0:
        raise HTTPException(
            status_code=409,
            detail="La cuenta profesora inicial ya fue creada.",
        )

    salt, password_hash = hash_password(data.password)

    try:
        user = create_user(
            username=data.username,
            display_name=data.display_name,
            role="teacher",
            password_salt=salt,
            password_hash=password_hash,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    token = new_session_token()
    create_session(token, user["id"])
    set_session_cookie(response, token)

    return {"user": public_user(user)}


@app.post("/api/auth/login")
def auth_login(data: LoginIn, response: Response):
    user = get_user_by_username(data.username)

    if not user or not verify_password(
        data.password,
        user["password_salt"],
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=401,
            detail="Usuario o contraseña incorrectos.",
        )

    token = new_session_token()
    create_session(token, user["id"])
    set_session_cookie(response, token)

    return {"user": public_user(user)}


@app.post("/api/auth/logout")
def auth_logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE)
    user = current_user(request)

    if token:
        delete_session(token)

    if user:
        ACTIVE_INTERVIEWS.pop(user["id"], None)

    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@app.get("/api/catalog")
def catalog(request: Request):
    require_user(request, role="teacher")

    return {
        "objetivo_general": PEDAGOGY["objetivo_general"],
        "objetivos": PEDAGOGY["objetivos"],
        "personajes": [
            character_summary(character)
            for character in CHARACTERS.values()
        ],
    }


@app.get("/api/simulations")
def simulations(request: Request):
    user = require_user(request)

    return [
        simulation_summary(
            simulation,
            teacher=user["role"] == "teacher",
        )
        for simulation in list_simulations()
    ]


@app.get("/api/simulations/{simulation_id}")
def simulation_detail(simulation_id: int, request: Request):
    user = require_user(request)
    simulation = get_simulation(simulation_id)

    if not simulation:
        raise HTTPException(status_code=404, detail="Simulación no encontrada.")

    return simulation_summary(
        simulation,
        teacher=user["role"] == "teacher",
    )


@app.post("/api/simulations")
def new_simulation(data: SimulationCreate, request: Request):
    require_user(request, role="teacher")

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


@app.delete("/api/simulations/{simulation_id}")
def delete_simulation(simulation_id: int, request: Request):
    require_user(request, role="teacher")

    simulation = get_simulation(simulation_id)
    if not simulation or not simulation.get("active", True):
        raise HTTPException(
            status_code=404,
            detail="La actividad no existe o ya fue eliminada.",
        )

    if not archive_simulation(simulation_id):
        raise HTTPException(
            status_code=409,
            detail="No fue posible eliminar la actividad.",
        )

    return {
        "ok": True,
        "message": (
            "Actividad eliminada de las simulaciones disponibles. "
            "Los intentos y resultados históricos se conservaron."
        ),
    }


@app.get("/api/students")
def students(request: Request):
    require_user(request, role="teacher")
    return list_students()


@app.post("/api/students")
def new_student(data: StudentCreate, request: Request):
    require_user(request, role="teacher")

    salt, password_hash = hash_password(data.password)

    try:
        user = create_user(
            username=data.username,
            display_name=data.display_name,
            role="student",
            password_salt=salt,
            password_hash=password_hash,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return public_user(user)


@app.get("/api/attempts")
def attempts(request: Request):
    user = require_user(request)

    rows = (
        list_attempts()
        if user["role"] == "teacher"
        else list_attempts(user_id=user["id"])
    )

    return [attempt_summary(row) for row in rows]


@app.get("/api/attempts/{attempt_id}")
def attempt_detail(attempt_id: int, request: Request):
    user = require_user(request)
    attempt = get_attempt(attempt_id)

    if not attempt:
        raise HTTPException(status_code=404, detail="Intento no encontrado.")

    if user["role"] != "teacher" and attempt["user_id"] != user["id"]:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para revisar este intento.",
        )

    return attempt_summary(attempt, include_detail=True)


@app.post("/api/simulations/{simulation_id}/start")
def start(simulation_id: int, request: Request):
    user = require_user(request, role="student")
    simulation = get_simulation(simulation_id)

    if not simulation or not simulation.get("active", True):
        raise HTTPException(
            status_code=404,
            detail="Esta simulación ya no está disponible.",
        )

    character = CHARACTERS.get(simulation["personaje"])
    if not character:
        raise HTTPException(
            status_code=400,
            detail="El entrevistado configurado no está disponible.",
        )

    attempt = create_attempt(user["id"], simulation_id)

    opening = (
        f"Hola, soy {character['nombre']}, {character['cargo']} de "
        f"{character['empresa']}. ¿En qué te puedo ayudar?"
    )

    ACTIVE_INTERVIEWS[user["id"]] = {
        "messages": [{"role": "assistant", "text": opening}],
        "question_count": 0,
        "simulation": simulation,
        "character": character,
        "attempt_id": attempt["id"],
        "usage": new_usage(),
    }

    save_attempt_progress(
        attempt_id=attempt["id"],
        question_count=0,
        transcript=ACTIVE_INTERVIEWS[user["id"]]["messages"],
    )

    return {
        "attempt_id": attempt["id"],
        "simulation": simulation_summary(simulation),
        "character": character_summary(character),
        "message": opening,
    }


@app.post("/api/message")
def message(data: MessageIn, request: Request):
    user = require_user(request, role="student")
    state = ACTIVE_INTERVIEWS.get(user["id"])

    if not state:
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
        reply = generate_reply(
            case=CASE,
            character=state["character"],
            history=state["messages"],
            question=text,
        )
    except InterviewConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except InterviewServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    answer = reply["text"]
    add_text_usage(state["usage"], "interviewer", reply["usage"])

    state["question_count"] += 1
    state["messages"].append({"role": "user", "text": text})
    state["messages"].append({"role": "assistant", "text": answer})

    save_attempt_progress(
        attempt_id=state["attempt_id"],
        question_count=state["question_count"],
        transcript=state["messages"],
    )

    return {
        "message": answer,
        "usage_summary": finalized_usage(state["usage"])["summary"],
    }


@app.post("/api/voice/transcribe")
async def voice_transcribe(
    request: Request,
    audio: UploadFile = File(...),
    duration_seconds: float = Form(0.0),
):
    user = require_user(request, role="student")
    state = ACTIVE_INTERVIEWS.get(user["id"])

    if not state:
        raise HTTPException(
            status_code=409,
            detail="Primero debes comenzar una simulación.",
        )

    audio_bytes = await audio.read()
    if len(audio_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="La grabación es demasiado grande. Intenta una pregunta más breve.",
        )

    try:
        transcription = transcribe_audio(
            audio_bytes=audio_bytes,
            filename=audio.filename or "pregunta.webm",
            content_type=audio.content_type,
        )
    except VoiceConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except VoiceServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    add_transcription_usage(
        state["usage"],
        transcription["model"],
        duration_seconds,
    )

    return {
        "text": transcription["text"],
        "usage_summary": finalized_usage(state["usage"])["summary"],
    }


@app.post("/api/voice/speech")
def voice_speech(data: SpeechIn, request: Request):
    user = require_user(request, role="student")
    state = ACTIVE_INTERVIEWS.get(user["id"])

    if not state:
        raise HTTPException(
            status_code=409,
            detail="No hay una simulación activa.",
        )

    try:
        speech = synthesize_speech(data.text)
    except VoiceConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except VoiceServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    add_tts_usage(state["usage"], speech["usage"])

    return Response(
        content=speech["audio"],
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-store"},
    )


@app.post("/api/end")
def end(request: Request):
    user = require_user(request, role="student")
    state = ACTIVE_INTERVIEWS.get(user["id"])

    if not state:
        raise HTTPException(
            status_code=409,
            detail="No hay una simulación activa.",
        )

    try:
        evaluation, evaluator_usage = evaluate_interview(
            pedagogy=PEDAGOGY,
            simulation=state["simulation"],
            case=CASE,
            character=state["character"],
            transcript=state["messages"],
        )
    except EvaluationConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except EvaluationServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    add_text_usage(state["usage"], "evaluator", evaluator_usage)
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
                for obj in state["simulation"].get(
                    "objetivos_personalizados",
                    [],
                )
                if obj["id"] == item["objetivo_id"]
            ),
            None,
        )
        item["nombre"] = custom["nombre"] if custom else item["objetivo_id"]

    complete_attempt(
        attempt_id=state["attempt_id"],
        question_count=state["question_count"],
        transcript=state["messages"],
        evaluation=payload,
    )

    usage = finalized_usage(state["usage"])
    save_attempt_usage(state["attempt_id"], usage)

    result = {
        "attempt_id": state["attempt_id"],
        "questions": state["question_count"],
        "simulation": simulation_summary(state["simulation"]),
        "evaluation": payload,
        "transcript": state["messages"],
        "usage": usage,
    }

    ACTIVE_INTERVIEWS.pop(user["id"], None)
    return result


app.mount("/static", StaticFiles(directory=STATIC), name="static")
