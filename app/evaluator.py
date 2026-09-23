from pathlib import Path
from typing import Literal
import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


class EvaluationConfigurationError(RuntimeError):
    pass


class EvaluationServiceError(RuntimeError):
    pass


class ObjectiveResult(BaseModel):
    objetivo_id: str
    nivel: Literal["no_evidenciado", "en_desarrollo", "logrado", "destacado"]
    evidencia: list[str]
    justificacion: str
    mejora_sugerida: str


class InterviewEvaluation(BaseModel):
    nivel_global: Literal["no_evidenciado", "en_desarrollo", "logrado", "destacado"]
    sintesis: str
    resultados: list[ObjectiveResult]
    fortalezas: list[str]
    proximos_pasos: list[str]


def _selected_objectives(pedagogy: dict, simulation: dict) -> list[dict]:
    catalog = {item["id"]: item for item in pedagogy["objetivos"]}
    selected = []

    for objective_id in simulation.get("objetivos_evaluados", []):
        if objective_id in catalog:
            selected.append(catalog[objective_id])

    for custom in simulation.get("objetivos_personalizados", []):
        selected.append(custom)

    return selected


def _transcript_text(transcript: list[dict]) -> str:
    lines = []
    for item in transcript:
        speaker = "Estudiante" if item["role"] == "user" else "Entrevistada"
        lines.append(f"{speaker}: {item['text']}")
    return "\n".join(lines)


def _build_instructions() -> str:
    return """
Eres un evaluador pedagógico de una simulación universitaria de entrevista de levantamiento de información.

Tu función está completamente separada del personaje entrevistado. Evalúas únicamente después de finalizada la entrevista.

REGLAS DE EVALUACIÓN
- Evalúa solamente los objetivos seleccionados para esta simulación.
- Usa únicamente evidencia presente en la transcripción.
- No inventes acciones, preguntas, intenciones ni aprendizajes del estudiante.
- La respuesta de la entrevistada por sí sola no demuestra una competencia del estudiante. Busca la acción del estudiante que provocó, profundizó, validó o utilizó esa información.
- No premies simplemente que haya aparecido una palabra o un hallazgo oculto.
- Valora especialmente la relación entre una respuesta del entrevistado y la pregunta siguiente del estudiante.
- Distingue una pregunta abierta de una pregunta dirigida.
- Distingue una repregunta real de un cambio de tema.
- Para validación, exige una síntesis, paráfrasis o comprobación explícita de comprensión.
- Para cierre, exige evidencia de que el estudiante cerró conscientemente la entrevista. Pulsar un botón no cuenta como cierre conversacional.
- Para neutralidad, considera tanto la presencia como la ausencia de preguntas que impongan causas o soluciones. No otorgues nivel destacado solo porque no hubo errores; debe existir una conducción claramente neutral y consistente.
- Si la entrevista es demasiado breve para observar un objetivo, usa "no_evidenciado" o "en_desarrollo" según la evidencia real.
- Sé exigente, formativo y concreto.
- En "evidencia", incluye como máximo dos ejemplos breves tomados o parafraseados fielmente de intervenciones del estudiante.
- La mejora sugerida debe indicar una acción concreta que el estudiante pueda intentar en una próxima entrevista.
- Devuelve exactamente un resultado por cada objetivo solicitado y conserva su objetivo_id.
""".strip()


def evaluate_interview(
    pedagogy: dict,
    simulation: dict,
    case: dict,
    character: dict,
    transcript: list[dict],
) -> InterviewEvaluation:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise EvaluationConfigurationError(
            "Falta OPENAI_API_KEY. El evaluador necesita la misma clave configurada para el entrevistado."
        )

    objectives = _selected_objectives(pedagogy, simulation)
    if not objectives:
        raise EvaluationConfigurationError(
            "La simulación no tiene objetivos pedagógicos seleccionados."
        )

    model = (
        os.getenv("OPENAI_EVALUATOR_MODEL", "").strip()
        or os.getenv("OPENAI_MODEL", "gpt-5.6-luna").strip()
        or "gpt-5.6-luna"
    )

    payload = {
        "objetivo_general": pedagogy["objetivo_general"],
        "objetivo_de_la_simulacion": simulation["objetivo_actividad"],
        "modo": simulation.get("modo", "entrenamiento"),
        "objetivos_a_evaluar": objectives,
        "escala_de_logro": pedagogy["escala_logro"],
        "contexto_del_caso": case,
        "informacion_interna_del_personaje": character,
        "transcripcion": _transcript_text(transcript),
    }

    client = OpenAI(api_key=api_key)

    try:
        response = client.responses.parse(
            model=model,
            instructions=_build_instructions(),
            input=json.dumps(payload, ensure_ascii=False, indent=2),
            text_format=InterviewEvaluation,
            max_output_tokens=3000,
        )
    except Exception as exc:
        raise EvaluationServiceError(
            "No fue posible generar la evaluación. Revisa la conexión, la clave de API y la disponibilidad del modelo."
        ) from exc

    evaluation = response.output_parsed
    if evaluation is None:
        raise EvaluationServiceError(
            "El evaluador no devolvió una evaluación estructurada utilizable."
        )

    expected_ids = [item["id"] for item in objectives]
    returned = {item.objetivo_id: item for item in evaluation.resultados}

    ordered_results = []
    for objective_id in expected_ids:
        result = returned.get(objective_id)
        if result is None:
            result = ObjectiveResult(
                objetivo_id=objective_id,
                nivel="no_evidenciado",
                evidencia=[],
                justificacion="La evaluación no entregó evidencia suficiente para este objetivo.",
                mejora_sugerida="Realiza acciones explícitas relacionadas con este objetivo en una próxima entrevista.",
            )
        ordered_results.append(result)

    evaluation.resultados = ordered_results
    return evaluation
