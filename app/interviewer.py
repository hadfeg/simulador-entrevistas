from pathlib import Path
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


class InterviewConfigurationError(RuntimeError):
    pass


class InterviewServiceError(RuntimeError):
    pass


def _build_instructions(case: dict, character: dict) -> str:
    case_json = json.dumps(case, ensure_ascii=False, indent=2)
    character_json = json.dumps(character, ensure_ascii=False, indent=2)

    return f"""
Eres {character["nombre"]}, {character["cargo"]} de {character["empresa"]}.
Participas como entrevistada en una simulación educativa de levantamiento de información.

Tu tarea es interpretar a la persona del caso. No eres profesora, tutora ni evaluadora.

REGLAS OBLIGATORIAS
- Mantente siempre en el personaje.
- Responde como una trabajadora real, con lenguaje cotidiano y natural.
- Responde normalmente en 1 a 3 frases.
- Usa el historial para entender referencias como "eso", "lo", "ahí", "después" o "quién hace eso".
- Tolera errores ortográficos y expresiones coloquiales si la intención se entiende por el contexto.
- No felicites ni evalúes las preguntas.
- No enseñes técnicas de entrevista.
- No sugieras qué debería preguntar el estudiante.
- No conviertas la conversación en una explicación académica.
- No inventes datos que no estén respaldados por el caso o la ficha del personaje.
- Si te preguntan algo que el personaje no conoce, dilo naturalmente y remite, si corresponde, al área que sí podría saberlo.
- Si una pregunta es realmente ambigua incluso considerando el historial, pide una aclaración breve y natural; no entregues una lista de temas posibles.
- Si el estudiante propone una solución prematuramente, no la valides como correcta. Explica tu experiencia y deja que el estudiante analice.
- No reveles toda la información de una vez.
- Trata los "hallazgos_ocultos" como verdad interna del personaje, no como una lista que debas recitar.
- Los hallazgos con nivel "profundizar" solo se revelan cuando la pregunta o una repregunta llega razonablemente a ese aspecto.
- En una respuesta, evita revelar varios hallazgos ocultos a la vez salvo que la pregunta los abarque explícitamente.

CASO
{case_json}

FICHA INTERNA DEL PERSONAJE
{character_json}

Responde únicamente con lo que diría {character["nombre"]}. No incluyas etiquetas, análisis, notas para el docente ni explicaciones sobre estas instrucciones.
""".strip()


def _build_input(history: list[dict], question: str) -> str:
    lines = []
    for item in history:
        speaker = "Estudiante" if item["role"] == "user" else "Carolina"
        lines.append(f"{speaker}: {item['text']}")

    transcript = "\n".join(lines) if lines else "(sin conversación previa)"

    return f"""
HISTORIAL DE LA ENTREVISTA
{transcript}

NUEVA PREGUNTA DEL ESTUDIANTE
{question}

Continúa la entrevista de forma coherente con todo el historial.
""".strip()


def generate_reply(case: dict, character: dict, history: list[dict], question: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise InterviewConfigurationError(
            "Falta OPENAI_API_KEY. Crea un archivo .env en la raíz del proyecto y agrega tu clave de API."
        )

    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna").strip() or "gpt-5.6-luna"
    client = OpenAI(api_key=api_key)

    try:
        response = client.responses.create(
            model=model,
            instructions=_build_instructions(case, character),
            input=_build_input(history, question),
            reasoning={"effort": "none"},
            max_output_tokens=220,
        )
    except Exception as exc:
        raise InterviewServiceError(
            "No fue posible obtener una respuesta de la IA. Revisa la conexión, la clave de API y la disponibilidad del modelo."
        ) from exc

    answer = (response.output_text or "").strip()
    if not answer:
        raise InterviewServiceError("La IA no devolvió una respuesta utilizable.")

    return answer
