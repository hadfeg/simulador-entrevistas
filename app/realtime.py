from pathlib import Path
import hashlib
import json
import os

import httpx
from dotenv import load_dotenv

from .interviewer import build_interview_instructions

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

OPENAI_REALTIME_URL = "https://api.openai.com/v1/realtime/calls"


class RealtimeConfigurationError(RuntimeError):
    pass


class RealtimeServiceError(RuntimeError):
    pass


def _api_key() -> str:
    value = os.getenv("OPENAI_API_KEY", "").strip()
    if not value:
        raise RealtimeConfigurationError(
            "Falta OPENAI_API_KEY para iniciar la conversación en tiempo real."
        )
    return value


def _safety_identifier(user_id: int) -> str:
    return hashlib.sha256(
        f"simulador-entrevistas:{user_id}".encode("utf-8")
    ).hexdigest()


def build_realtime_session(case: dict, character: dict) -> dict:
    model = (
        os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime-2.1").strip()
        or "gpt-realtime-2.1"
    )
    voice = os.getenv("OPENAI_REALTIME_VOICE", "marin").strip() or "marin"
    transcription_model = (
        os.getenv("OPENAI_LIVE_TRANSCRIBE_MODEL", "gpt-live-transcribe").strip()
        or "gpt-live-transcribe"
    )

    instructions = build_interview_instructions(case, character)
    instructions += """

REGLAS ADICIONALES PARA LA CONVERSACIÓN ORAL
- Habla siempre en español latinoamericano natural.
- Mantén respuestas breves y conversacionales, normalmente de 1 a 3 frases.
- No uses listas, títulos, markdown ni lenguaje de asistente virtual.
- No expliques que eres una IA.
- Si el estudiante te interrumpe, detente y escucha.
- Si no entiendes una pregunta, pide una aclaración breve y natural.
- No cierres la entrevista por iniciativa propia.
""".strip()

    transcription_prompt = (
        "Entrevista universitaria de levantamiento de información en español de Chile. "
        f"La persona entrevistada es {character['nombre']}, {character['cargo']} de "
        f"{character['empresa']}. Se habla sobre Bodega, recepción de mercadería, "
        "inventario, stock, despacho, devoluciones, Excel y sistemas de información."
    )

    return {
        "type": "realtime",
        "model": model,
        "instructions": instructions,
        "output_modalities": ["audio"],
        "audio": {
            "input": {
                "transcription": {
                    "model": transcription_model,
                    "prompt": transcription_prompt,
                    "keywords": [
                        "RetailNova",
                        "Bodega",
                        "inventario",
                        "stock",
                        "mercadería",
                        "recepción",
                        "despacho",
                        "devoluciones",
                        "Excel",
                        "sistema",
                    ],
                    "languages": ["es"],
                    "delay": "medium",
                },
                "turn_detection": {
                    "type": "semantic_vad",
                    "eagerness": "medium",
                    "create_response": True,
                    "interrupt_response": True,
                },
            },
            "output": {
                "voice": voice,
            },
        },
    }


def create_realtime_call(
    sdp_offer: str,
    case: dict,
    character: dict,
    user_id: int,
) -> dict:
    if not sdp_offer.strip():
        raise RealtimeServiceError("La oferta WebRTC está vacía.")

    session = build_realtime_session(case, character)

    files = {
        "sdp": (None, sdp_offer, "application/sdp"),
        "session": (
            None,
            json.dumps(session, ensure_ascii=False),
            "application/json",
        ),
    }

    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "OpenAI-Safety-Identifier": _safety_identifier(user_id),
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                OPENAI_REALTIME_URL,
                headers=headers,
                files=files,
            )

        if response.status_code >= 400:
            detail = response.text[:600]
            raise RealtimeServiceError(
                f"No fue posible iniciar Realtime ({response.status_code}): {detail}"
            )

        if not response.text.strip():
            raise RealtimeServiceError(
                "Realtime no devolvió una respuesta SDP válida."
            )

        return {
            "sdp": response.text,
            "model": session["model"],
            "transcription_model": session["audio"]["input"]["transcription"]["model"],
        }
    except RealtimeServiceError:
        raise
    except httpx.HTTPError as exc:
        raise RealtimeServiceError(
            "No fue posible conectar con la Realtime API."
        ) from exc
